import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import pytz

# ─── CONFIG ─────────────────────────────────────────────────────────────────────
PACIFIC_TZ = pytz.timezone("America/Los_Angeles")
DATE = (datetime.now(PACIFIC_TZ) - timedelta(days=1)).date().isoformat()

TRAINING_SET_PATH = Path("training-data/training-set/training-set.csv")
MATCHUPS_WITH_SCORES_PATH = Path(f"processed/game-scores/game_scores_{DATE}.csv")

MATCHUP_COLUMNS = [
    "Date", "Fav Team", "Dog Team", "away_team", "home_team", "Fav Home?",
    "Spread", "Fav Spread Odds", "Dog Spread Odds",
    "Fav Score", "Dog Score", "Fav/Dog +/-", "Fav Cover?", "Fav Win?",
    "Away Spread Odds", "Home  Spread Odds", "Away Score", "Home Score", "Home/Away  +/-"
]


# ─── LOAD FILES ─────────────────────────────────────────────────────────────────
if not TRAINING_SET_PATH.exists():
    raise FileNotFoundError(f"❌ Training set not found: {TRAINING_SET_PATH}")

if not MATCHUPS_WITH_SCORES_PATH.exists():
    raise FileNotFoundError(f"❌ Scores file not found for {DATE}: {MATCHUPS_WITH_SCORES_PATH}")

df_train = pd.read_csv(TRAINING_SET_PATH)
df_scores = pd.read_csv(MATCHUPS_WITH_SCORES_PATH)

# ─── CLEAN AND VALIDATE ─────────────────────────────────────────────────────────
df_scores = df_scores[MATCHUP_COLUMNS]
df_scores = df_scores.dropna(subset=["Date", "Fav Team", "Dog Team"])

# Only get the rows in the training set for that date
mask = df_train["Date"] == DATE
df_train_date = df_train[mask].copy()

# Merge on identifying columns
key_cols = ["Date", "Fav Team", "Dog Team"]
merged = df_train_date.merge(df_scores, on=key_cols, how="inner", suffixes=("", "_new"))

# Drop unmatched rows
if len(merged) < len(df_train_date):
    dropped = len(df_train_date) - len(merged)
    print(f"⚠️  Dropping {dropped} unmatched games from training set for {DATE}")

# Overwrite matchup columns with the latest ones
for col in MATCHUP_COLUMNS:
    if col in key_cols:
        continue
    new_col = f"{col}_new"
    if new_col in merged.columns:
        merged[col] = merged[new_col]

# ─── RECONSTRUCT FINAL TRAINING SET ─────────────────────────────────────────────
df_final = pd.concat([df_train[~mask], merged[df_train.columns]], ignore_index=True)
df_final.to_csv(TRAINING_SET_PATH, index=False)
print(f"✅ Training set updated for {DATE}: {len(merged)} rows replaced")
