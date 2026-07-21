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
# 1. TODAY'S PICKS  (no score yet)
# ─────────────────────────────────────────────────────────────────
df_today = df[(df["date"] == today_fmt) & (df["home_score"].isna())].copy()
print(f"Today's unplayed games: {len(df_today)}")

# If no unplayed games found, try yesterday (handles late-night UTC timezone edge)
if df_today.empty:
    from datetime import timedelta
    yesterday = today - timedelta(days=1)
    yesterday_fmt = f"{yesterday.month}/{yesterday.day}/{yesterday.year}"
    df_today = df[(df["date"] == yesterday_fmt) & (df["home_score"].isna())].copy()
    print(f"Falling back to yesterday ({yesterday_fmt}): {len(df_today)} unplayed games")

picks_today = []
for _, row in df_today.iterrows():
    conf  = get_confidence(row)
    home_odds = int(row["home_odds"]) if pd.notna(row["home_odds"]) else None
    away_odds = int(row["away_odds"]) if pd.notna(row["away_odds"]) else None
    pick_odds = int(row["pick_odds"]) if pd.notna(row["pick_odds"]) else None
    edge  = round(float(row["edge"]), 2) if pd.notna(row["edge"]) else None
    picks_today.append({
        "home_team":  row["home_team"],
        "away_team":  row["away_team"],
        "pick":       row["pick_made"],
        "confidence": round(float(conf), 4) if pd.notna(conf) else None,
        "home_odds":  home_odds,
        "away_odds":  away_odds,
        "line":       pick_odds,
        "edge":       edge,
        "notes":      f"XGBoost edge: +{edge}%" if edge else None
    })

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
