"""
Fetch 2026 betting odds from BallDontLie API and save as betting_outlook files.

Uses the same timezone conversion logic as the ETL pipeline:
  - Game dates are stored in UTC by BDL
  - Local dates come from the game_outlook filenames (already timezone-adjusted)
  - We fetch odds by game_id, so no date alignment issues

Saves one CSV per date at:
  data/2026_data/mlb_data/raw/betting_outlook/betting_outlook_{date}.csv

Uses DraftKings as primary vendor (available for all games).
BDL only provides a single odds snapshot (no open/close distinction),
so we populate both open and close columns with the same values.
"""

import os
import sys
import csv
import time
import glob
import requests
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("BALLDONTLIE_API_KEY")
BDL_BASE = "https://api.balldontlie.io/mlb/v1"
HEADERS = {"Authorization": API_KEY}
BASE_DIR = Path("data/2026_data/mlb_data/raw")
VENDOR = "draftkings"

OUTLOOK_COLS = [
    "Date", "home team", "away team", "home score", "away score",
    "home ml open", "away ml open", "home ml close", "away ml close",
    "over open", "under open", "over close", "under close",
    "over open odds", "under open odds", "over close odds", "under close odds",
]


def load_game_metadata():
    """Load game_pk -> metadata from game_outlook files.
    
    Returns dict: game_pk -> {date, home_team, away_team, home_score, away_score}
    The date comes from the filename (already local/timezone-adjusted).
    """
    games = {}
    go_files = sorted(glob.glob(str(BASE_DIR / "game_outlook" / "game_outlook_*.csv")))
    for f in go_files:
        file_date = os.path.basename(f).replace("game_outlook_", "").replace(".csv", "")
        with open(f) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                gpk = row["game_pk"]
                games[gpk] = {
                    "date": file_date,
                    "home_team": row["home_team_abbreviation"],
                    "away_team": row["away_team_abbreviation"],
                    "home_score": row.get("home_team_score", ""),
                    "away_score": row.get("away_team_score", ""),
                    "status": row.get("status", ""),
                }
    return games


def fetch_odds_batch(game_ids):
    """Fetch odds for a batch of game IDs. Returns list of odds records."""
    all_odds = []
    cursor = None
    while True:
        params = {"game_ids[]": game_ids, "per_page": 100}
        if cursor:
            params["cursor"] = cursor
        resp = requests.get(f"{BDL_BASE}/odds", headers=HEADERS, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        all_odds.extend(data["data"])
        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor:
            break
        time.sleep(0.3)
    return all_odds


def main():
    # 1. Load game metadata (game_pk -> date, teams, scores)
    game_meta = load_game_metadata()
    all_game_pks = sorted(game_meta.keys(), key=int)
    print(f"Loaded {len(all_game_pks)} games from game_outlook files")

    # 2. Fetch odds in batches of 15 (15 games * 6 vendors = 90 records < 100/page)
    BATCH_SIZE = 15
    odds_by_game = defaultdict(list)
    
    for i in range(0, len(all_game_pks), BATCH_SIZE):
        batch = all_game_pks[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(all_game_pks) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"  Fetching batch {batch_num}/{total_batches} ({len(batch)} games)...", end=" ")
        
        odds = fetch_odds_batch(batch)
        for o in odds:
            odds_by_game[str(o["game_id"])].append(o)
        
        print(f"got {len(odds)} records")
        time.sleep(0.3)

    # 3. Group games by date and build betting outlook files
    games_by_date = defaultdict(list)
    for gpk, meta in game_meta.items():
        games_by_date[meta["date"]].append(gpk)

    games_with_odds = 0
    games_without_odds = 0
    
    out_dir = BASE_DIR / "betting_outlook"
    out_dir.mkdir(parents=True, exist_ok=True)

    for date_str in sorted(games_by_date.keys()):
        gpks = games_by_date[date_str]
        rows = []
        
        for gpk in sorted(gpks, key=int):
            meta = game_meta[gpk]
            
            # Find DraftKings odds for this game
            game_odds = [o for o in odds_by_game.get(gpk, []) if o["vendor"] == VENDOR]
            
            row = {
                "Date": date_str,
                "home team": meta["home_team"],
                "away team": meta["away_team"],
                "home score": meta["home_score"] if "FINAL" in meta.get("status", "") else "",
                "away score": meta["away_score"] if "FINAL" in meta.get("status", "") else "",
            }
            
            if game_odds:
                o = game_odds[0]
                # BDL has single snapshot - use for both open and close
                row["home ml open"] = o["moneyline_home_odds"]
                row["away ml open"] = o["moneyline_away_odds"]
                row["home ml close"] = o["moneyline_home_odds"]
                row["away ml close"] = o["moneyline_away_odds"]
                row["over open"] = o["total_value"]
                row["under open"] = o["total_value"]
                row["over close"] = o["total_value"]
                row["under close"] = o["total_value"]
                row["over open odds"] = o["total_over_odds"]
                row["under open odds"] = o["total_under_odds"]
                row["over close odds"] = o["total_over_odds"]
                row["under close odds"] = o["total_under_odds"]
                games_with_odds += 1
            else:
                # Leave odds columns empty
                for col in OUTLOOK_COLS[5:]:
                    row[col] = ""
                games_without_odds += 1
            
            rows.append(row)
        
        # Write CSV
        out_path = out_dir / f"betting_outlook_{date_str}.csv"
        with open(out_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=OUTLOOK_COLS)
            writer.writeheader()
            writer.writerows(rows)
        
        n_with = sum(1 for r in rows if r.get("home ml close"))
        print(f"  {date_str}: {len(rows)} games, {n_with} with odds → {out_path.name}")

    print(f"\nDone: {games_with_odds} games with odds, {games_without_odds} without")


if __name__ == "__main__":
    main()
