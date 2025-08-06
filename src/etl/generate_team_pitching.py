import os
from pathlib import Path
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+

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

FINAL_COLS = [
    "favorite_team","underdog_team","away_team","home_team",
    "runline_spread","favorite_spread_odds","underdog_spread_odds",
    "fav_p_runs","dog_p_runs",
    "fav_p_runs_per_ab","dog_p_runs_per_ab",
    "fav_p_doubles","dog_p_doubles",
    "fav_p_doubles_per_ab","dog_p_doubles_per_ab",
    "fav_p_triples","dog_p_triples",
    "fav_p_triples_per_ab","dog_p_triples_per_ab",
    "fav_p_homeruns","dog_p_homeruns",
    "fav_p_homeruns_per_ab","dog_p_homeruns_per_ab",
    "fav_p_strikeouts","dog_p_strikeouts",
    "fav_p_strikeouts_per_ab","dog_p_strikeouts_per_ab",
    "fav_p_baseonballs","dog_p_baseonballs",
    "fav_p_baseonballs_per_ab","dog_p_baseonballs_per_ab",
    "fav_p_hits","dog_p_hits",
    "fav_p_avg","dog_p_avg",
    "fav_p_atbats","dog_p_atbats",
    "fav_p_obp","dog_p_obp",
    "fav_p_slg","dog_p_slg",
    "fav_p_ops","dog_p_ops",
    "fav_p_era","dog_p_era",
    "fav_p_inningspitched","dog_p_inningspitched",
    "fav_p_earnedruns","dog_p_earnedruns",
    "fav_p_earnedruns_per_ab","dog_p_earnedruns_per_ab",
    "fav_p_whip","dog_p_whip",
    "fav_p_battersfaced","dog_p_battersfaced",
    "fav_p_totalbases","dog_p_totalbases",
    "fav_p_pitchesperinning","dog_p_pitchesperinning",
    "fav_p_gamesfinished","dog_p_gamesfinished",
    "fav_p_strikeoutwalkratio","dog_p_strikeoutwalkratio",
    "fav_p_strikeoutsper9inn","dog_p_strikeoutsper9inn",
    "fav_p_walksper9inn","dog_p_walksper9inn",
    "fav_p_hitsper9inn","dog_p_hitsper9inn",
    "fav_p_runsscoredper9","dog_p_runsscoredper9",
    "fav_p_homerunsper9","dog_p_homerunsper9"
]

def transform_team_pitching(date_str: str, data_dir: Path, out_dir: Path) -> pd.DataFrame:
    project_root = Path(__file__).resolve().parents[2]
    matchups_fp = project_root / "processed" / "matchups" / f"matchups_{date_str}.csv"
    if not matchups_fp.exists():
        print(f"Skipped {date_str}: no matchups file found")
        return None

    df_m = pd.read_csv(matchups_fp)
    df_m.columns = df_m.columns.str.strip().str.lower()
    df_m = df_m.rename(columns={
        "fav team": "favorite_team",
        "dog team": "underdog_team",
        "away": "away_team",
        "home": "home_team",
        "spread": "runline_spread",
        "fav spread odds": "favorite_spread_odds",
        "dog spread odds": "underdog_spread_odds"
    })

    pit_fp = data_dir / "team_pitching" / f"team_pitching_{date_str}.csv"
    if not pit_fp.exists():
        print(f"Skipped {date_str}: no pitching file found")
        return None

    df_p = pd.read_csv(pit_fp)
    df_p.columns = df_p.columns.str.strip().str.lower()
    df_p["team_code"] = df_p["team"].map(TEAM_NAME_MAP)

    fav = df_p.rename(columns={"team_code": "favorite_team"}).set_index("favorite_team").add_prefix("fav_p_").reset_index()
    dog = df_p.rename(columns={"team_code": "underdog_team"}).set_index("underdog_team").add_prefix("dog_p_").reset_index()

    df = df_m.merge(fav, on="favorite_team", how="left").merge(dog, on="underdog_team", how="left")

    stats_to_divide = ["runs","doubles","triples","homeruns","strikeouts","baseonballs","earnedruns"]
    for stat in stats_to_divide:
        if f"fav_p_{stat}" in df.columns and "fav_p_atbats" in df.columns:
            df[f"fav_p_{stat}_per_ab"] = df[f"fav_p_{stat}"] / df["fav_p_atbats"]
        if f"dog_p_{stat}" in df.columns and "dog_p_atbats" in df.columns:
            df[f"dog_p_{stat}_per_ab"] = df[f"dog_p_{stat}"] / df["dog_p_atbats"]

    for col in FINAL_COLS:
        if col not in df.columns:
            df[col] = ""

    df = df[FINAL_COLS]

    out_dir.mkdir(parents=True, exist_ok=True)
    out_fp = out_dir / f"team_pitching_matchups_{date_str}.csv"
    df.to_csv(out_fp, index=False)
    print(f"Wrote {out_fp} ({len(df)} rows)")
    return df

def main():
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    out_dir = project_root / "processed" / "team-pitching"

    # Use current date in Pacific Time
    pacific_today = datetime.now(ZoneInfo("America/Los_Angeles")).date()
    date_str = pacific_today.isoformat()
    transform_team_pitching(date_str, data_dir, out_dir)

if __name__ == "__main__":
    main()
