import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import pytz

# Mapping full names to abbreviations
TEAM_ABBR = {
    "Arizona Diamondbacks": "ARI", "Atlanta Braves": "ATL", "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS", "Chicago White Sox": "CWS", "Chicago Cubs": "CHC",
    "Cincinnati Reds": "CIN", "Cleveland Guardians": "CLE", "Colorado Rockies": "COL",
    "Detroit Tigers": "DET", "Houston Astros": "HOU", "Kansas City Royals": "KAN",
    "Los Angeles Angels": "LAA", "Los Angeles Dodgers": "LAD", "Miami Marlins": "MIA",
    "Milwaukee Brewers": "MIL", "Minnesota Twins": "MIN", "New York Mets": "NYM",
    "New York Yankees": "NYY", "Athletics": "OAK", "Philadelphia Phillies": "PHI",
    "Pittsburgh Pirates": "PIT", "San Diego Padres": "SD", "San Francisco Giants": "SF",
    "Seattle Mariners": "SEA", "St. Louis Cardinals": "STL", "Tampa Bay Rays": "TB",
    "Texas Rangers": "TEX", "Toronto Blue Jays": "TOR", "Washington Nationals": "WAS"
}

# Determine yesterday's date in Pacific Time
PACIFIC_TZ = pytz.timezone("America/Los_Angeles")
yesterday = datetime.now(PACIFIC_TZ).date() - timedelta(days=1)
date_str = yesterday.isoformat()

print(f"\n🔍 Processing {date_str}")

# File paths
matchup_path = Path(f"processed/matchups/matchups_{date_str}.csv")
scores_path = Path(f"data/game-scores/game_scores_{date_str}.csv")
out_path = Path(f"processed/game-scores/game_scores_{date_str}.csv")
missing_log_path = Path(f"processed/game-scores/missing_scores_{date_str}.csv")

if not matchup_path.exists() or not scores_path.exists():
    print(f"❌ Missing input files for {date_str}")
else:
    # Load data
    matchups = pd.read_csv(matchup_path)
    scores = pd.read_csv(scores_path)

    matchups = matchups.rename(columns={"Home": "home_team", "Away": "away_team"})
    scores["home_team"] = scores["Home Team"].map(TEAM_ABBR)
    scores["away_team"] = scores["Away Team"].map(TEAM_ABBR)
    scores = scores.dropna(subset=["home_team", "away_team"])
    scores = scores.rename(columns={"Home Score": "home_score", "Away Score": "away_score"})

    # Merge in both directions
    merged_normal = pd.merge(
        matchups,
        scores[["home_team", "away_team", "home_score", "away_score"]],
        on=["home_team", "away_team"],
        how="left"
    )

    scores_flipped = scores.rename(columns={
        "home_team": "away_team",
        "away_team": "home_team",
        "home_score": "away_score_flipped",
        "away_score": "home_score_flipped"
    })
    merged_flipped = pd.merge(
        matchups,
        scores_flipped[["home_team", "away_team", "home_score_flipped", "away_score_flipped"]],
        on=["home_team", "away_team"],
        how="left"
    )

    # Combine results
    matchups["Home Score"] = merged_normal["home_score"].combine_first(merged_flipped["home_score_flipped"])
    matchups["Away Score"] = merged_normal["away_score"].combine_first(merged_flipped["away_score_flipped"])

    # Add Fav/Dog scores
    matchups["Fav Score"] = matchups.apply(
        lambda row: row["Home Score"] if row["Fav Home?"] else row["Away Score"], axis=1
    )
    matchups["Dog Score"] = matchups.apply(
        lambda row: row["Away Score"] if row["Fav Home?"] else row["Home Score"], axis=1
    )

    # Compute outcomes
    matchups["Fav/Dog +/-"] = matchups["Fav Score"] - matchups["Dog Score"]
    matchups["Fav Cover?"] = (matchups["Fav/Dog +/-"] > matchups["Spread"]).astype(int)
    matchups["Fav Win?"] = (matchups["Fav Score"] > matchups["Dog Score"]).astype(int)
    matchups["Home/Away  +/-"] = matchups["Home Score"] - matchups["Away Score"]

    # Log missing scores
    missing = matchups[matchups[["Home Score", "Away Score"]].isnull().any(axis=1)]
    if not missing.empty:
        missing.to_csv(missing_log_path, index=False)
        print(f"⚠️ Missing {len(missing)} scores. Logged to {missing_log_path}")
    else:
        print("✅ All scores matched.")

    matchups.to_csv(out_path, index=False)
    print(f"✅ Saved merged file to {out_path}")
