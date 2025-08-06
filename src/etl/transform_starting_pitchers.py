import pandas as pd
import numpy as np
from pathlib import Path
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
    "Athletics": "OAK"
}

PITCHER_STATS = [("ERA", "era"), ("WHIP", "whip"), ("IP", "ip"),
                 ("SO", "so"), ("AVG", "avg"), ("AB", "ab")]
BULLPEN_STATS = [("BP ERA", "bp_era"), ("BP WHIP", "bp_whip"), ("BP IP", "bp_ip"),
                 ("BP SO", "bp_so"), ("BP AB", "bp_ab")]

def normalize_team(name):
    return TEAM_NAME_MAP.get(name, name)

def extract_stats(df, prefix, side):
    out = pd.DataFrame()
    for orig, new in PITCHER_STATS + BULLPEN_STATS:
        col = f"{side}_{orig.lower().replace(' ', '_')}"
        out[f"{prefix}_sp_{new}"] = df[col] if col in df else np.nan
    out[f"{prefix}_sp_starter"] = df[f"{side}_starter"] if f"{side}_starter" in df else np.nan
    return out

TEAM_PITCHING_MAP = {
    "era": "era",
    "whip": "whip",
    "ip": "inningsPitched",
    "so": "strikeOuts",
    "avg": "avg",
    "ab": "atBats",
    "bp_era": "era",
    "bp_whip": "whip",
    "bp_ip": "inningsPitched",
    "bp_so": "strikeOuts",
    "bp_ab": "atBats"
}

def fill_with_team_pitching(team_code, tp, prefix):
    stats = tp[tp["team"] == team_code]
    if stats.empty:
        result = {f"{prefix}_sp_{k}": np.nan for k in TEAM_PITCHING_MAP}
        result[f"{prefix}_sp_starter"] = f"{prefix.upper()} team pitching (missing)"
        return pd.Series(result)

    row = stats.iloc[0]
    result = {
        f"{prefix}_sp_{k}": row.get(source_col, np.nan)
        for k, source_col in TEAM_PITCHING_MAP.items()
    }
    result[f"{prefix}_sp_starter"] = f"{prefix.upper()} team pitching"
    return pd.Series(result)

def transform_starting_pitchers(date_str, data_dir, out_dir):
    matchup_path = Path("processed/matchups") / f"matchups_{date_str}.csv"
    sp_path = Path(data_dir) / "starting-pitchers" / f"starting_pitchers_{date_str}.csv"
    tp_path = Path(data_dir) / "team_pitching" / f"team_pitching_{date_str}.csv"

    if not matchup_path.exists() or not sp_path.exists():
        print(f"❌ Missing matchup or SP file for {date_str}, skipping.")
        return

    matchups = pd.read_csv(matchup_path)
    sp = pd.read_csv(sp_path)
    tp = pd.read_csv(tp_path) if tp_path.exists() else pd.DataFrame()

    matchups.columns = [c.strip().lower().replace(" ", "").replace("?", "") for c in matchups.columns]
    sp.columns = [c.strip().replace(" ", "_").lower() for c in sp.columns]

    sp["home_team"] = sp["home_team"].apply(normalize_team)
    sp["away_team"] = sp["away_team"].apply(normalize_team)
    if not tp.empty and "team" in tp.columns:
        tp["team"] = tp["team"].apply(normalize_team)

    fav = matchups.merge(sp, left_on="favteam", right_on="home_team", how="left")
    fav_stats = extract_stats(fav, "fav", "home")
    unmatched = fav["home_starter"].isnull()
    if unmatched.any():
        fallback = matchups.loc[unmatched].merge(sp, left_on="favteam", right_on="away_team", how="left")
        fav_stats.loc[unmatched] = extract_stats(fallback, "fav", "away")

    dog = matchups.merge(sp, left_on="dogteam", right_on="home_team", how="left")
    dog_stats = extract_stats(dog, "dog", "home")
    unmatched = dog["home_starter"].isnull()
    if unmatched.any():
        fallback = matchups.loc[unmatched].merge(sp, left_on="dogteam", right_on="away_team", how="left")
        dog_stats.loc[unmatched] = extract_stats(fallback, "dog", "away")

    df = matchups.copy()
    df["favorite_team"] = df["favteam"]
    df["underdog_team"] = df["dogteam"]
    df["away_team"] = df["away"]
    df["home_team"] = df["home"]
    df = pd.concat([df, fav_stats, dog_stats], axis=1)

    for prefix in ["fav", "dog"]:
        missing = df[f"{prefix}_sp_era"].isnull()
        if missing.any() and not tp.empty:
            fallback = df.loc[missing, f"{prefix}team"].apply(lambda team: fill_with_team_pitching(team, tp, prefix))
            df.loc[missing, fallback.columns] = fallback.values
            print(f"⚠️  Used team-level pitching stats for {missing.sum()} {prefix.upper()} teams on {date_str}")

    for prefix in ["fav", "dog"]:
        df[f"{prefix}_sp_ab_per_ip"] = df[f"{prefix}_sp_ab"] / df[f"{prefix}_sp_ip"]
        df[f"{prefix}_sp_so_per_ab"] = df[f"{prefix}_sp_so"] / df[f"{prefix}_sp_ab"]
        df[f"{prefix}_bp_ab_per_ip"] = df[f"{prefix}_sp_bp_ab"] / df[f"{prefix}_sp_bp_ip"]
        df[f"{prefix}_bp_so_per_ab"] = df[f"{prefix}_sp_bp_so"] / df[f"{prefix}_sp_bp_ab"]

    cols = [
        "favorite_team", "underdog_team", "away_team", "home_team",
        "fav_sp_starter", "dog_sp_starter",
        "fav_sp_era", "dog_sp_era",
        "fav_sp_whip", "dog_sp_whip",
        "fav_sp_ip", "dog_sp_ip",
        "fav_sp_ab_per_ip", "dog_sp_ab_per_ip",
        "fav_sp_so", "dog_sp_so",
        "fav_sp_so_per_ab", "dog_sp_so_per_ab",
        "fav_sp_avg", "dog_sp_avg",
        "fav_sp_ab", "dog_sp_ab",
        "fav_sp_bp_era", "dog_sp_bp_era",
        "fav_sp_bp_whip", "dog_sp_bp_whip",
        "fav_sp_bp_ip", "dog_sp_bp_ip",
        "fav_bp_ab_per_ip", "dog_bp_ab_per_ip",
        "fav_sp_bp_so", "dog_sp_bp_so",
        "fav_bp_so_per_ab", "dog_bp_so_per_ab",
        "fav_sp_bp_ab", "dog_sp_bp_ab"
    ]

    df_out = df[cols]
    out_path = Path("processed/starting-pitchers") / f"starting_pitchers_matchups_{date_str}.csv"
    df_out.to_csv(out_path, index=False)
    print(f"✅ Wrote {out_path} ({len(df_out)} rows)")

if __name__ == "__main__":
    pacific_today = datetime.now(ZoneInfo("America/Los_Angeles")).date()
    transform_starting_pitchers(
        pacific_today.isoformat(),
        data_dir="data",
        out_dir="processed/starting-pitchers"
    )
