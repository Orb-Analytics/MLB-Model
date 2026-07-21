"""
Generate predictions.json (today) and predictions_history.json (settled picks)
"""
import json
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

REPO_ROOT   = Path(__file__).resolve().parent
PICKS_FILE  = REPO_ROOT / "data" / "mlb_detailed_picks_tracking.csv"
TODAY_OUT   = REPO_ROOT / "predictions.json"
HISTORY_OUT = REPO_ROOT / "predictions_history.json"

today     = datetime.now(ZoneInfo("America/Chicago")).date()
today_fmt = f"{today.month}/{today.day}/{today.year}"
now_utc   = datetime.now(ZoneInfo("UTC")).isoformat()

print(f"Date: {today_fmt}")

df = pd.read_csv(PICKS_FILE)

# ── Confidence helper ─────────────────────────────────────────────
def get_confidence(row):
    if row["pick_is_home"] == 1:
        return row["regressed_home_prob"]
    return row["regressed_away_prob"]

# ─────────────────────────────────────────────────────────────────
# 1. TODAY'S PICKS  (all games, with pick flag)
# ─────────────────────────────────────────────────────────────────
DATASET_FILE = REPO_ROOT / "data" / "2026_data" / "2026_dataset" / "2026_dataset.csv"

df_dataset = pd.read_csv(DATASET_FILE, encoding='latin-1', low_memory=False)
df_all_today = df_dataset[df_dataset["Date"] == today_fmt].copy()
print(f"All games today: {len(df_all_today)}")

# Get picks for today
df_today = df[(df["date"] == today_fmt) & (df["home_score"].isna())].copy()

# Fallback to yesterday if no unplayed games found
if df_today.empty:
    from datetime import timedelta
    yesterday = today - timedelta(days=1)
    yesterday_fmt = f"{yesterday.month}/{yesterday.day}/{yesterday.year}"
    df_today = df[(df["date"] == yesterday_fmt) & (df["home_score"].isna())].copy()
    print(f"Falling back to yesterday ({yesterday_fmt}): {len(df_today)} unplayed games")

# Build picks lookup keyed by home+away
picks_lookup = {}
for _, row in df_today.iterrows():
    key = (row["home_team"], row["away_team"])
    picks_lookup[key] = row

picks_today = []
for _, row in df_all_today.iterrows():
    home = row["home team"]
    away = row["away team"]
    home_odds = int(row["home ml close"]) if pd.notna(row["home ml close"]) else None
    away_odds = int(row["away ml close"]) if pd.notna(row["away ml close"]) else None

    # Check if model made a pick for this game
    pick_row = picks_lookup.get((home, away))
    has_pick = pick_row is not None

    if has_pick:
        conf = get_confidence(pick_row)
        edge = round(float(pick_row["edge"]), 2) if pd.notna(pick_row["edge"]) else None
        pick_made = pick_row["pick_made"]
        confidence = round(float(conf), 4) if pd.notna(conf) else None
        notes = f"XGBoost edge: +{edge}%" if edge else None
    else:
        edge = None
        pick_made = None
        confidence = None
        notes = None

    picks_today.append({
        "home_team":  home,
        "away_team":  away,
        "pick":       pick_made,
        "has_pick":   has_pick,
        "confidence": confidence,
        "home_odds":  home_odds,
        "away_odds":  away_odds,
        "line":       int(pick_row["pick_odds"]) if has_pick and pd.notna(pick_row["pick_odds"]) else None,
        "edge":       edge,
        "notes":      notes
    })

print(f"Today's unplayed games: {len(df_today)}")

if picks_today:
    with open(TODAY_OUT, "w") as f:
        json.dump({
            "model":        "MLB",
            "generated_at": now_utc,
            "version":      "v2.1",
            "picks":        picks_today
        }, f, indent=2)
    print(f"✅ predictions.json — {len(picks_today)} picks")
else:
    print(f"⚠️ No picks found — predictions.json not overwritten")

# ─────────────────────────────────────────────────────────────────
# 2. HISTORY  (settled picks only — has a result)
# ─────────────────────────────────────────────────────────────────
df_hist = df[df["pick_correct"].notna()].copy()
df_hist = df_hist.sort_values("date", ascending=False)

wins   = int((df_hist["pick_correct"] == 1).sum())
losses = int((df_hist["pick_correct"] == 0).sum())
total_units = round(float(df_hist["units"].sum()), 2)
win_rate    = round(wins / len(df_hist) * 100, 1) if len(df_hist) else 0

history_picks = []
for _, row in df_hist.iterrows():
    conf   = get_confidence(row)
    odds   = int(row["pick_odds"])  if pd.notna(row["pick_odds"])  else None
    edge   = round(float(row["edge"]), 2)   if pd.notna(row["edge"])   else None
    units  = round(float(row["units"]), 2)  if pd.notna(row["units"])  else None
    result = "Win" if row["pick_correct"] == 1 else "Loss"

    history_picks.append({
        "date":       row["date"],
        "home_team":  row["home_team"],
        "away_team":  row["away_team"],
        "pick":       row["pick_made"],
        "confidence": round(float(conf), 4) if pd.notna(conf) else None,
        "line":       odds,
        "edge":       edge,
        "result":     result,
        "units":      units,
        "home_score": int(row["home_score"]) if pd.notna(row["home_score"]) else None,
        "away_score": int(row["away_score"]) if pd.notna(row["away_score"]) else None
    })

with open(HISTORY_OUT, "w") as f:
    json.dump({
        "model":        "MLB",
        "generated_at": now_utc,
        "version":      "v2.1",
        "summary": {
            "wins":        wins,
            "losses":      losses,
            "win_rate":    win_rate,
            "total_units": total_units,
            "total_picks": len(df_hist)
        },
        "picks": history_picks
    }, f, indent=2)

print(f"✅ predictions_history.json — {len(history_picks)} settled picks ({wins}W-{losses}L, {win_rate}% win rate, {total_units:+.2f}u)")
