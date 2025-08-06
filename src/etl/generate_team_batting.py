import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+

# Full MLB name → Novig code
TEAM_NAME_MAP = {
    "Arizona Diamondbacks": "ARI", "Atlanta Braves": "ATL", "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS", "Chicago White Sox": "CWS", "Chicago Cubs": "CHC",
    "Cincinnati Reds": "CIN", "Cleveland Guardians": "CLE", "Colorado Rockies": "COL",
    "Detroit Tigers": "DET", "Houston Astros": "HOU", "Kansas City Royals": "KAN",
    "Los Angeles Angels": "LAA", "Los Angeles Dodgers": "LAD", "Miami Marlins": "MIA",
    "Milwaukee Brewers": "MIL", "Minnesota Twins": "MIN", "New York Mets": "NYM",
    "New York Yankees": "NYY", "Athletics": "OAK", "Philadelphia Phillies": "PHI",
    "Pittsburgh Pirates": "PIT", "San Diego Padres": "SD", "San Francisco Giants": "SF",
    "Seattle Mariners": "SEA", "St. Louis Cardinals": "STL", "Tampa Bay Rays": "TB",
    "Texas Rangers": "TEX", "Toronto Blue Jays": "TOR", "Washington Nationals": "WAS",
}

BAT_RENAME = {
    "team": "team_name", "gamesPlayed": "games_played", "groundOuts": "ground_outs",
    "airOuts": "air_outs", "runs": "runs", "doubles": "doubles", "triples": "triples",
    "homeRuns": "homeruns", "strikeOuts": "strikeouts", "baseOnBalls": "base_on_balls",
    "intentionalWalks": "intentional_walks", "hits": "hits", "hitByPitch": "hit_by_pitch",
    "avg": "avg", "atBats": "ab", "obp": "obp", "slg": "slg", "ops": "ops",
    "caughtStealing": "caught_stealing", "stolenBases": "stolen_bases",
    "stolenBasePercentage": "stolen_base_percentage", "groundIntoDoublePlay": "ground_into_double_play",
    "numberOfPitches": "number_of_pitches", "plateAppearances": "plate_appearances",
    "totalBases": "total_bases", "rbi": "rbi", "leftOnBase": "left_on_base",
    "sacBunts": "sac_bunts", "sacFlies": "sac_flies", "babip": "babip",
    "groundOutsToAirouts": "ground_outs_to_air_outs", "catchersInterference": "catchers_interference",
    "atBatsPerHomeRun": "ab_per_home_run",
}

def safe_div(num: pd.Series, den: pd.Series) -> pd.Series:
    return num.div(den.replace({0: pd.NA}))

def transform_team_batting(date_str: str, data_dir: Path, out_dir: Path) -> pd.DataFrame:
    project_root = Path(__file__).resolve().parents[2]
    mp = project_root / "processed" / "matchups" / f"matchups_{date_str}.csv"
    df_m = pd.read_csv(mp)
    df_m.columns = df_m.columns.str.strip()
    df_m = df_m.rename(columns={
        "Fav Team": "favorite_team",
        "Dog Team": "underdog_team",
        "Fav Home?": "fav_home"
    })
    mask = df_m["fav_home"].astype(bool)
    df_m["home_team"] = df_m["favorite_team"].where(mask, df_m["underdog_team"])
    df_m["away_team"] = df_m["underdog_team"].where(mask, df_m["favorite_team"])
    df_m = df_m[["favorite_team","underdog_team","away_team","home_team"]]

    bat_fp = data_dir / "team_batting" / f"team_batting_{date_str}.csv"
    df_b = pd.read_csv(bat_fp).rename(columns=BAT_RENAME)
    df_b["team_code"] = df_b["team_name"].map(TEAM_NAME_MAP)
    stats = [v for k,v in BAT_RENAME.items() if v != "team_name"]

    fav = (
        df_b.rename(columns={"team_code": "favorite_team"})
            .loc[:, ["favorite_team"] + stats]
            .set_index("favorite_team").add_prefix("fav_b_").reset_index()
    )
    dog = (
        df_b.rename(columns={"team_code": "underdog_team"})
            .loc[:, ["underdog_team"] + stats]
            .set_index("underdog_team").add_prefix("dog_b_").reset_index()
    )
    fav.drop(columns=[c for c in fav.columns if c.endswith("team_name")], inplace=True)
    dog.drop(columns=[c for c in dog.columns if c.endswith("team_name")], inplace=True)

    df = df_m.merge(fav, on="favorite_team", how="left") \
             .merge(dog, on="underdog_team", how="left")

    rate_stats = ["runs","doubles","triples","homeruns","strikeouts","base_on_balls","rbi"]
    for side in ("fav_b","dog_b"): 
        for stat in rate_stats:
            df[f"{side}_{stat}_per_ab"] = safe_div(df[f"{side}_{stat}"], df[f"{side}_ab"])

    final_cols = [
        "favorite_team","underdog_team","away_team","home_team",
        "fav_b_runs","dog_b_runs",
        "fav_b_runs_per_ab","dog_b_runs_per_ab",
        "fav_b_doubles","dog_b_doubles",
        "fav_b_doubles_per_ab","dog_b_doubles_per_ab",
        "fav_b_triples","dog_b_triples",
        "fav_b_triples_per_ab","dog_b_triples_per_ab",
        "fav_b_homeruns","dog_b_homeruns",
        "fav_b_homeruns_per_ab","dog_b_homeruns_per_ab",
        "fav_b_strikeouts","dog_b_strikeouts",
        "fav_b_strikeouts_per_ab","dog_b_strikeouts_per_ab",
        "fav_b_base_on_balls","dog_b_base_on_balls",
        "fav_b_base_on_balls_per_ab","dog_b_base_on_balls_per_ab",
        "fav_b_hits","dog_b_hits",
        "fav_b_avg","dog_b_avg",
        "fav_b_ab","dog_b_ab",
        "fav_b_obp","dog_b_obp",
        "fav_b_slg","dog_b_slg",
        "fav_b_ops","dog_b_ops",
        "fav_b_stolen_bases","dog_b_stolen_bases",
        "fav_b_total_bases","dog_b_total_bases",
        "fav_b_rbi","dog_b_rbi",
        "fav_b_rbi_per_ab","dog_b_rbi_per_ab",
    ]
    df = df[final_cols]

    out_dir.mkdir(parents=True, exist_ok=True)
    out_fp = out_dir / f"team_batting_matchups_{date_str}.csv"
    df.to_csv(out_fp, index=False)
    print(f"Wrote {out_fp} ({len(df)} rows)")
    return df

# Run only for today (Pacific Time)
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    BASE = project_root / "data"
    OUT = project_root / "processed" / "team-batting"

    pacific_today = datetime.now(ZoneInfo("America/Los_Angeles")).date()
    ds = pacific_today.isoformat()
    try:
        transform_team_batting(ds, BASE, OUT)
    except FileNotFoundError as e:
        print(f"[{ds}] skipped (missing file): {e}")
    except Exception as e:
        print(f"[{ds}] failed: {e}")
