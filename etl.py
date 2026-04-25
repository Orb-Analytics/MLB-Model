#!/usr/bin/env python3
"""
MLB Daily ETL Pipeline

Runs the full data pipeline for a given date:
  1. Fetch game outlook (schedule) for TARGET_DATE from BDL API
  2. Fetch probable pitchers for TARGET_DATE from MLB Stats API
  3. Fetch boxscores for YESTERDAY (now final) from BDL API
  4. Compute bullpen boxscores for YESTERDAY
  5. Compute season-to-date stats for TARGET_DATE
  6. Compute rolling stats for TARGET_DATE
  7. Consolidate processed files
  8. Build 2026 dataset
  9. Update training set

Usage:
    python etl.py                      # Auto-detects today as target date
    python etl.py 2026-04-06           # Explicit target date
    python etl.py 2026-04-06 --skip-fetch  # Skip API fetches (reprocess only)
"""

import os
import sys
import subprocess
import argparse
import time
import re
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# ─── Configuration ──────────────────────────────────────────────────────────────

load_dotenv()
API_KEY = os.getenv("BALLDONTLIE_API_KEY")
BDL_BASE = "https://api.balldontlie.io/mlb/v1"
BDL_HEADERS = {"Authorization": API_KEY}
MLB_BASE = "https://statsapi.mlb.com/api/v1"

YEAR = 2026
BASE_DIR = Path(f"data/{YEAR}_data/mlb_data/raw")
PROCESSED_DIR = Path(f"data/{YEAR}_data/mlb_data/processed")
DATASET_DIR = Path(f"data/{YEAR}_data/{YEAR}_dataset")
TRAINING_SET = Path("training-set/training_set.csv")

# Ensure directories exist
for d in [
    BASE_DIR / "game_outlook",
    BASE_DIR / "boxscores",
    BASE_DIR / "starting_pitcher_boxscores",
    BASE_DIR / "team_bullpen_boxscores",
    BASE_DIR / "probable_pitchers",
    PROCESSED_DIR,
    DATASET_DIR,
]:
    d.mkdir(parents=True, exist_ok=True)


def log(step, msg):
    print(f"[{step}] {msg}")


# ─── Step 1: Fetch Game Outlook ────────────────────────────────────────────────

GAME_OUTLOOK_COLUMNS = [
    "id", "game_pk", "season", "date", "postseason", "season_type", "status",
    "venue", "conference_play",
    "home_team_id", "away_team_id",
    "home_team_slug", "away_team_slug",
    "home_team_abbreviation", "away_team_abbreviation",
    "home_team_display_name", "away_team_display_name",
    "home_team_short_display_name", "away_team_short_display_name",
    "home_team_name", "away_team_name",
    "home_team_location", "away_team_location",
    "home_team_league", "away_team_league",
    "home_team_division", "away_team_division",
    "home_team_score", "away_team_score",
    "favorite_id", "underdog_id",
    "favorite_abbreviation", "underdog_abbreviation",
    "favorite_display_name", "underdog_display_name",
]


def fetch_game_outlook(target_date: str):
    """Fetch game outlook/schedule for target_date from BDL API."""
    out_path = BASE_DIR / "game_outlook" / f"game_outlook_{target_date}.csv"
    if out_path.exists():
        log("1-OUTLOOK", f"Already exists: {out_path.name}")
        return True

    log("1-OUTLOOK", f"Fetching games for {target_date}...")

    # BDL stores UTC timestamps, so query both target and next day
    target = datetime.strptime(target_date, "%Y-%m-%d").date()
    next_day = (target + timedelta(days=1)).strftime("%Y-%m-%d")

    all_games = []
    for query_date in [target_date, next_day]:
        cursor = None
        while True:
            params = {"dates[]": query_date, "per_page": 100}
            if cursor:
                params["cursor"] = cursor
            resp = requests.get(f"{BDL_BASE}/games", headers=BDL_HEADERS, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            all_games.extend(data["data"])
            cursor = data.get("meta", {}).get("next_cursor")
            if not cursor:
                break
            time.sleep(0.3)

    # Filter to target local date and regular season
    games = []
    seen_ids = set()
    for g in all_games:
        if g["id"] in seen_ids:
            continue
        seen_ids.add(g["id"])
        utc_dt = datetime.fromisoformat(g["date"].replace("Z", "+00:00"))
        local_dt = utc_dt - timedelta(hours=5)  # EST proxy
        if local_dt.date() == target and g.get("season_type") == "regular":
            games.append(g)

    if not games:
        log("1-OUTLOOK", f"No regular season games found for {target_date}")
        return False

    # Flatten
    rows = []
    for g in games:
        home = g.get("home_team", {})
        away = g.get("away_team", {})
        home_data = g.get("home_team_data", {})
        away_data = g.get("away_team_data", {})
        rows.append({
            "id": g["id"], "game_pk": g["id"],
            "season": g.get("season"), "date": g.get("date"),
            "postseason": g.get("postseason"), "season_type": g.get("season_type"),
            "status": g.get("status"), "venue": g.get("venue"),
            "conference_play": g.get("conference_play"),
            "home_team_id": home.get("id"), "away_team_id": away.get("id"),
            "home_team_slug": home.get("slug"), "away_team_slug": away.get("slug"),
            "home_team_abbreviation": home.get("abbreviation"),
            "away_team_abbreviation": away.get("abbreviation"),
            "home_team_display_name": home.get("display_name"),
            "away_team_display_name": away.get("display_name"),
            "home_team_short_display_name": home.get("short_display_name"),
            "away_team_short_display_name": away.get("short_display_name"),
            "home_team_name": home.get("name"), "away_team_name": away.get("name"),
            "home_team_location": home.get("location"),
            "away_team_location": away.get("location"),
            "home_team_league": home.get("league"), "away_team_league": away.get("league"),
            "home_team_division": home.get("division"),
            "away_team_division": away.get("division"),
            "home_team_score": home_data.get("runs", 0),
            "away_team_score": away_data.get("runs", 0),
            "favorite_id": None, "underdog_id": None,
            "favorite_abbreviation": None, "underdog_abbreviation": None,
            "favorite_display_name": None, "underdog_display_name": None,
        })

    df = pd.DataFrame(rows)
    for col in GAME_OUTLOOK_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[GAME_OUTLOOK_COLUMNS]
    df.to_csv(out_path, index=False)
    log("1-OUTLOOK", f"Saved {len(df)} games to {out_path.name}")
    return True


# ─── Step 1b: Fetch Betting Odds ───────────────────────────────────────────────

BETTING_OUTLOOK_DIR = BASE_DIR / "betting_outlook"
BETTING_OUTLOOK_DIR.mkdir(parents=True, exist_ok=True)

BETTING_OUTLOOK_COLUMNS = [
    "game_pk", "Date", "home team", "away team", "home score", "away score",
    "home ml open", "away ml open", "home ml close", "away ml close",
    "over open", "under open", "over close", "under close",
    "over open odds", "under open odds", "over close odds", "under close odds",
]

NOVIG_URL = "https://gql.novig.us/v1/graphql"
NOVIG_QUERY = """
query {
  event(where: {_and: [
      {_or: [
        {status: {_eq: "OPEN_PREGAME"}},
        {status: {_eq: "OPEN_INGAME"}}
      ]},
      {game: {league: {_eq: "MLB"}}}
    ]}) {
    id
    description
    game {
      scheduled_start
    }
    markets {
      description
      is_consensus
      outcomes {
        description
        available
      }
    }
  }
}
"""

_ML_RE = re.compile(r'^[A-Z]{2,3}$')
_TOTAL_RE = re.compile(r'^[A-Z]{2,3} @ [A-Z]{2,3} t(\d+\.?\d*)$')
_1H_RE = re.compile(r'\b1H\b|1st Inning', re.IGNORECASE)

# Novig uses different abbreviations for 3 teams
_NOVIG_ABBR_MAP = {"KAN": "KC", "CWS": "CHW", "WAS": "WSH"}


def _price_to_american(price):
    """Convert Novig probability (0-1) to American odds string."""
    try:
        if price is None:
            return ""
        price = float(price)
        if price <= 0 or price >= 1:
            return ""
        if price == 0.5:
            return 100
        elif price < 0.5:
            return int(round((1 / price - 1) * 100))
        else:
            return int(round(-100 / (1 / price - 1)))
    except Exception:
        return ""


def _extract_novig_odds(markets, home_abbr, away_abbr):
    """Extract moneyline and totals from Novig consensus markets.

    Returns dict with keys matching BETTING_OUTLOOK_COLUMNS odds fields,
    or empty dict if nothing found.
    """
    ml = {}   # {team_abbr: american_odds}
    total_line = None
    total_over_odds = None
    total_under_odds = None

    for mkt in markets:
        if not mkt.get("is_consensus"):
            continue
        mdesc = mkt.get("description") or ""
        if _1H_RE.search(mdesc):
            continue

        outcomes = mkt.get("outcomes") or []

        # Moneyline: market description is home team abbr (e.g. "MIL")
        if _ML_RE.match(mdesc):
            for oc in outcomes:
                od = (oc.get("description") or "").strip()
                p = oc.get("available")
                if _1H_RE.search(od):
                    continue
                if _ML_RE.match(od) and p is not None:
                    od = _NOVIG_ABBR_MAP.get(od, od)
                    ml[od] = _price_to_american(p)
            continue

        # Totals: market description like "TOR @ MIL t7.5"
        tm = _TOTAL_RE.match(mdesc)
        if tm:
            total_line = float(tm.group(1))
            for oc in outcomes:
                od = (oc.get("description") or "").strip()
                p = oc.get("available")
                if _1H_RE.search(od):
                    continue
                if p is not None:
                    if od.lower().startswith("over"):
                        total_over_odds = _price_to_american(p)
                    elif od.lower().startswith("under"):
                        total_under_odds = _price_to_american(p)
            continue

    result = {}
    if home_abbr in ml and away_abbr in ml:
        result["home ml open"] = ml[home_abbr]
        result["away ml open"] = ml[away_abbr]
        result["home ml close"] = ml[home_abbr]
        result["away ml close"] = ml[away_abbr]
    if total_line is not None:
        result["over open"] = total_line
        result["under open"] = total_line
        result["over close"] = total_line
        result["under close"] = total_line
    if total_over_odds is not None:
        result["over open odds"] = total_over_odds
        result["over close odds"] = total_over_odds
    if total_under_odds is not None:
        result["under open odds"] = total_under_odds
        result["under close odds"] = total_under_odds

    return result


def fetch_betting_odds(target_date: str):
    """Fetch pregame betting odds for target_date from Novig API.

    Reads the game_outlook file for target_date to get game info,
    then fetches consensus odds from Novig's GraphQL endpoint.
    Matches Novig events to game_outlook rows via display team names.
    """
    out_path = BETTING_OUTLOOK_DIR / f"betting_outlook_{target_date}.csv"
    if out_path.exists():
        log("1b-ODDS", f"Already exists: {out_path.name}")
        return True

    outlook_path = BASE_DIR / "game_outlook" / f"game_outlook_{target_date}.csv"
    if not outlook_path.exists():
        log("1b-ODDS", f"No game outlook for {target_date}, skipping odds")
        return True  # Not a failure — just no games that day

    log("1b-ODDS", f"Fetching pregame odds from Novig for {target_date}...")

    outlook = pd.read_csv(outlook_path)

    # Fetch all MLB pregame events from Novig
    try:
        resp = requests.post(NOVIG_URL, json={"query": NOVIG_QUERY}, timeout=30)
        resp.raise_for_status()
        novig_data = resp.json()
    except Exception as e:
        log("1b-ODDS", f"Novig API error: {e}")
        return False

    events = novig_data.get("data", {}).get("event", [])

    # Build lookup: "Away Display @ Home Display" -> event with most markets
    # Novig can have duplicate events; pick the one with the most markets
    event_lookup = {}
    for ev in events:
        desc = ev.get("description", "")
        n_markets = len(ev.get("markets") or [])
        if desc not in event_lookup or n_markets > len(event_lookup[desc].get("markets") or []):
            event_lookup[desc] = ev

    # Build rows
    rows = []
    matched = 0
    for _, g in outlook.iterrows():
        home_display = str(g["home_team_display_name"]).strip()
        away_display = str(g["away_team_display_name"]).strip()
        home_abbr = str(g["home_team_abbreviation"]).strip()
        away_abbr = str(g["away_team_abbreviation"]).strip()

        row = {
            "game_pk": g["id"],
            "Date": target_date,
            "home team": home_abbr,
            "away team": away_abbr,
            "home score": "",
            "away score": "",
        }

        # Match Novig event by display name
        novig_key = f"{away_display} @ {home_display}"
        ev = event_lookup.get(novig_key)

        if ev and ev.get("markets"):
            odds = _extract_novig_odds(ev["markets"], home_abbr, away_abbr)
            if odds:
                row.update(odds)
                matched += 1

        # Fill any missing odds columns with empty string
        for col in BETTING_OUTLOOK_COLUMNS:
            if col not in row:
                row[col] = ""

        rows.append(row)

    df = pd.DataFrame(rows, columns=BETTING_OUTLOOK_COLUMNS)
    df.to_csv(out_path, index=False)
    log("1b-ODDS", f"Saved {len(df)} games ({matched} with odds) to {out_path.name}")
    return True


# ─── Step 2: Fetch Probable Pitchers ───────────────────────────────────────────

def fetch_probable_pitchers(target_date: str):
    """Fetch probable pitchers for target_date from MLB Stats API."""
    out_path = BASE_DIR / "probable_pitchers" / f"probable_pitchers_{target_date}.csv"
    if out_path.exists():
        log("2-PITCHERS", f"Already exists: {out_path.name}")
        return True

    log("2-PITCHERS", f"Fetching probable pitchers for {target_date}...")
    url = f"{MLB_BASE}/schedule"
    params = {"date": target_date, "sportId": 1, "hydrate": "probablePitcher,team"}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for date_entry in data.get("dates", []):
        for game in date_entry.get("games", []):
            game_pk = game["gamePk"]
            game_date = game.get("gameDate", "")
            status = game.get("status", {}).get("detailedState", "")
            venue = game.get("venue", {}).get("name", "")

            home = game.get("teams", {}).get("home", {})
            away = game.get("teams", {}).get("away", {})
            home_team = home.get("team", {})
            away_team = away.get("team", {})

            home_pitcher = home.get("probablePitcher", {})
            away_pitcher = away.get("probablePitcher", {})

            rows.append({
                "game_pk": game_pk,
                "date": game_date,
                "home_team_id": home_team.get("id"),
                "away_team_id": away_team.get("id"),
                "home_team_name": home_team.get("name", ""),
                "away_team_name": away_team.get("name", ""),
                "home_probable_pitcher_id": home_pitcher.get("id", ""),
                "home_probable_pitcher_name": home_pitcher.get("fullName", ""),
                "away_probable_pitcher_id": away_pitcher.get("id", ""),
                "away_probable_pitcher_name": away_pitcher.get("fullName", ""),
                "venue": venue,
                "game_time_utc": game_date,
                "status": status,
            })

    if not rows:
        log("2-PITCHERS", f"No games found for {target_date}")
        return False

    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)
    log("2-PITCHERS", f"Saved {len(df)} games to {out_path.name}")
    return True


# ─── Step 3: Fetch Boxscores (for yesterday) ───────────────────────────────────

def fetch_boxscores(date_str: str):
    """Fetch team + starting pitcher boxscores from BDL API using existing script."""
    team_path = BASE_DIR / "boxscores" / f"boxscores_{date_str}.csv"
    pitcher_path = BASE_DIR / "starting_pitcher_boxscores" / f"starting_pitcher_boxscores_{date_str}.csv"

    if team_path.exists() and pitcher_path.exists():
        log("3-BOXSCORES", f"Already exist for {date_str}")
        return True

    log("3-BOXSCORES", f"Fetching boxscores for {date_str}...")
    cmd = [
        sys.executable, "bdl-exploration/fetch_bdl_boxscores.py",
        "--date", date_str,
        "--boxscore-dir", str(BASE_DIR / "boxscores"),
        "--pitcher-dir", str(BASE_DIR / "starting_pitcher_boxscores"),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log("3-BOXSCORES", f"ERROR: {result.stderr}")
        return False

    log("3-BOXSCORES", result.stdout.strip().split("\n")[-1] if result.stdout.strip() else "Done")
    return True


# ─── Step 4: Compute Bullpen Boxscores (for yesterday) ─────────────────────────

def safe_divide(num, denom, default=0.0):
    if denom == 0 or pd.isna(denom):
        return default
    return num / denom


def compute_bullpen_boxscores(date_str: str):
    """Compute bullpen boxscores by subtracting starter from team totals."""
    out_path = BASE_DIR / "team_bullpen_boxscores" / f"team_bullpen_boxscores_{date_str}.csv"
    if out_path.exists():
        log("4-BULLPEN", f"Already exists for {date_str}")
        return True

    team_path = BASE_DIR / "boxscores" / f"boxscores_{date_str}.csv"
    pitcher_path = BASE_DIR / "starting_pitcher_boxscores" / f"starting_pitcher_boxscores_{date_str}.csv"

    if not team_path.exists() or not pitcher_path.exists():
        log("4-BULLPEN", f"Missing boxscore data for {date_str}, skipping")
        return False

    team_df = pd.read_csv(team_path)
    pitcher_df = pd.read_csv(pitcher_path)

    rows = []
    for _, team_row in team_df.iterrows():
        gp = team_row["game_pk"]
        pitcher_match = pitcher_df[pitcher_df["game_pk"] == gp]
        if pitcher_match.empty:
            continue
        starter_row = pitcher_match.iloc[0]

        row = {"game_pk": gp, "date": date_str}
        for side in ["home", "away"]:
            team_ip = float(team_row[f"{side}_pitching_ip"])
            starter_ip = float(starter_row[f"{side}_starter_ip"])
            bp_ip = round(max(team_ip - starter_ip, 0), 4)

            bp_h = max(int(team_row[f"{side}_pitching_h"] - starter_row[f"{side}_starter_hits"]), 0)
            bp_er = max(int(team_row[f"{side}_pitching_er"] - starter_row[f"{side}_starter_earned_runs"]), 0)
            bp_bb = max(int(team_row[f"{side}_pitching_bb"] - starter_row[f"{side}_starter_walks"]), 0)
            bp_k = max(int(team_row[f"{side}_pitching_k"] - starter_row[f"{side}_starter_strikeouts"]), 0)
            bp_hr = max(int(team_row[f"{side}_pitching_hr"] - starter_row[f"{side}_starter_homeruns"]), 0)

            row[f"{side}_bullpen_ip"] = bp_ip
            row[f"{side}_bullpen_hits"] = bp_h
            row[f"{side}_bullpen_earned_runs"] = bp_er
            row[f"{side}_bullpen_walks"] = bp_bb
            row[f"{side}_bullpen_strikeouts"] = bp_k
            row[f"{side}_bullpen_homeruns"] = bp_hr
            row[f"{side}_bullpen_era"] = round(safe_divide(bp_er * 9, bp_ip), 2)
            row[f"{side}_bullpen_whip"] = round(safe_divide(bp_h + bp_bb, bp_ip), 2)
            row[f"{side}_bullpen_k_per_9"] = round(safe_divide(bp_k * 9, bp_ip), 2)
            row[f"{side}_bullpen_k_bb_ratio"] = round(safe_divide(bp_k, bp_bb), 2)
            row[f"{side}_bullpen_hr_per_9"] = round(safe_divide(bp_hr * 9, bp_ip), 2)
            row[f"{side}_bullpen_bb_per_9"] = round(safe_divide(bp_bb * 9, bp_ip), 2)
        rows.append(row)

    if rows:
        pd.DataFrame(rows).to_csv(out_path, index=False)
        log("4-BULLPEN", f"Saved {len(rows)} games to {out_path.name}")
    else:
        log("4-BULLPEN", f"No bullpen data computed for {date_str}")
    return True


# ─── Step 4b: Update Yesterday's Game Outlook with Final Scores ─────────────────

def update_game_outlook_scores(date_str: str):
    """Re-fetch game data for date_str to update scores and status in the outlook file."""
    out_path = BASE_DIR / "game_outlook" / f"game_outlook_{date_str}.csv"
    if not out_path.exists():
        log("4b-SCORES", f"No game outlook file for {date_str}, skipping")
        return True

    existing = pd.read_csv(out_path)
    # If all games already final, skip
    if existing["status"].str.contains("FINAL").all():
        log("4b-SCORES", f"All games already final for {date_str}")
        return True

    log("4b-SCORES", f"Updating scores for {date_str}...")
    target = datetime.strptime(date_str, "%Y-%m-%d").date()
    next_day = (target + timedelta(days=1)).strftime("%Y-%m-%d")

    all_games = []
    for query_date in [date_str, next_day]:
        cursor = None
        while True:
            params = {"dates[]": query_date, "per_page": 100}
            if cursor:
                params["cursor"] = cursor
            resp = requests.get(f"{BDL_BASE}/games", headers=BDL_HEADERS, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            all_games.extend(data["data"])
            cursor = data.get("meta", {}).get("next_cursor")
            if not cursor:
                break
            time.sleep(0.3)

    # Build lookup: BDL game id -> (status, home_score, away_score)
    score_lookup = {}
    for g in all_games:
        home_data = g.get("home_team_data", {})
        away_data = g.get("away_team_data", {})
        score_lookup[g["id"]] = {
            "status": g.get("status", ""),
            "home_team_score": home_data.get("runs", 0),
            "away_team_score": away_data.get("runs", 0),
        }

    updated = 0
    for idx, row in existing.iterrows():
        game_id = row["id"]
        if game_id in score_lookup:
            info = score_lookup[game_id]
            if info["status"] != row["status"]:
                existing.at[idx, "status"] = info["status"]
                existing.at[idx, "home_team_score"] = info["home_team_score"]
                existing.at[idx, "away_team_score"] = info["away_team_score"]
                updated += 1

    existing.to_csv(out_path, index=False)
    log("4b-SCORES", f"Updated {updated} games with final scores in {out_path.name}")
    return True


# ─── Step 4c: Backfill Missing Probable Pitchers ───────────────────────────────

def backfill_probable_pitchers(date_str: str):
    """Fill in missing probable pitchers from actual starting pitcher boxscores.

    When the MLB Stats API doesn't have a confirmed starter at fetch time,
    we leave the pitcher name/ID blank. Once boxscores are in (step 3),
    we can backfill with the actual starter who pitched.
    """
    pp_path = BASE_DIR / "probable_pitchers" / f"probable_pitchers_{date_str}.csv"
    sp_path = BASE_DIR / "starting_pitcher_boxscores" / f"starting_pitcher_boxscores_{date_str}.csv"
    go_path = BASE_DIR / "game_outlook" / f"game_outlook_{date_str}.csv"

    if not pp_path.exists():
        log("4c-BACKFILL", f"No probable pitchers file for {date_str}, skipping")
        return True
    if not sp_path.exists():
        log("4c-BACKFILL", f"No boxscores for {date_str}, skipping")
        return True
    if not go_path.exists():
        log("4c-BACKFILL", f"No game outlook for {date_str}, skipping")
        return True

    pp = pd.read_csv(pp_path, dtype=str).fillna("")
    sp = pd.read_csv(sp_path, dtype=str).fillna("")
    go = pd.read_csv(go_path, dtype=str).fillna("")

    # Build mapping: team display_name -> BDL game_pk (from game_outlook)
    # Handle both sides (a team could be home or away)
    team_to_gpk = {}
    for _, r in go.iterrows():
        gpk = r["game_pk"]
        team_to_gpk[(r["home_team_display_name"], "home")] = gpk
        team_to_gpk[(r["away_team_display_name"], "away")] = gpk

    # Build mapping: BDL game_pk -> starter info (from boxscores)
    gpk_to_starter = {}
    for _, r in sp.iterrows():
        gpk_to_starter[r["game_pk"]] = {
            "home_name": r["home_starter_name"],
            "away_name": r["away_starter_name"],
        }

    filled = 0
    for idx, row in pp.iterrows():
        for side, pp_name_col in [("home", "home_probable_pitcher_name"),
                                   ("away", "away_probable_pitcher_name")]:
            if row[pp_name_col].strip():
                continue  # Already has a pitcher

            team_name = row[f"{side}_team_name"]
            # Try exact match first, then partial match for "Athletics" vs "Oakland Athletics"
            gpk = team_to_gpk.get((team_name, side))
            if not gpk:
                for (dn, s), g in team_to_gpk.items():
                    if s == side and (team_name in dn or dn in team_name):
                        gpk = g
                        break

            if not gpk or gpk not in gpk_to_starter:
                continue

            starter_name = gpk_to_starter[gpk][f"{side}_name"]
            if starter_name.strip():
                pp.at[idx, pp_name_col] = starter_name
                filled += 1
                log("4c-BACKFILL", f"  Filled {side} pitcher for {team_name}: {starter_name}")

    if filled > 0:
        pp.to_csv(pp_path, index=False)
        log("4c-BACKFILL", f"Backfilled {filled} missing pitcher(s) in {pp_path.name}")
        # Re-run STD for the backfilled date so updated pitcher names propagate
        # into the season-to-date stats file (steps 6-9 will pick them up).
        log("4c-BACKFILL", f"Re-running STD for {date_str} to propagate backfilled pitchers...")
        compute_season_to_date(date_str)
    else:
        log("4c-BACKFILL", f"No missing pitchers to backfill for {date_str}")
    return True


# ─── Step 5: Compute Season-to-Date Stats ──────────────────────────────────────

def compute_season_to_date(target_date: str):
    """Run compute_daily_season_to_date_stats.py."""
    log("5-STD", f"Computing season-to-date stats for {target_date}...")
    result = subprocess.run(
        [sys.executable, "scripts/etl/compute/compute_daily_season_to_date_stats.py", target_date],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        log("5-STD", f"ERROR:\n{result.stderr[-500:]}")
        return False
    # Print last few lines of output
    lines = result.stdout.strip().split("\n")
    for line in lines[-3:]:
        log("5-STD", line)
    return True


# ─── Step 6: Compute Rolling Stats ─────────────────────────────────────────────

def compute_rolling(target_date: str):
    """Run compute_daily_rolling_stats.py."""
    log("6-ROLLING", f"Computing rolling stats for {target_date}...")
    result = subprocess.run(
        [sys.executable, "scripts/etl/compute/compute_daily_rolling_stats.py", target_date],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        log("6-ROLLING", f"ERROR:\n{result.stderr[-500:]}")
        return False
    lines = result.stdout.strip().split("\n")
    for line in lines[-3:]:
        log("6-ROLLING", line)
    return True


# ─── Step 7: Consolidate Processed Files ───────────────────────────────────────

def consolidate():
    """Run consolidate_year_stats.py."""
    log("7-CONSOLIDATE", f"Consolidating processed files for {YEAR}...")
    result = subprocess.run(
        [sys.executable, "scripts/etl/consolidate/consolidate_year_stats.py", str(YEAR)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        log("7-CONSOLIDATE", f"ERROR:\n{result.stderr[-500:]}")
        return False
    lines = result.stdout.strip().split("\n")
    for line in lines[-5:]:
        log("7-CONSOLIDATE", line)
    return True


# ─── Step 8: Build 2026 Dataset ────────────────────────────────────────────────

def build_dataset():
    """Run build_2026_dataset.py."""
    log("8-DATASET", "Building 2026 dataset...")
    result = subprocess.run(
        [sys.executable, "scripts/etl/builders/build_2026_dataset.py"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        log("8-DATASET", f"ERROR:\n{result.stderr[-500:]}")
        return False
    lines = result.stdout.strip().split("\n")
    for line in lines:
        log("8-DATASET", line)
    return True


# ─── Step 9: Update Training Set ───────────────────────────────────────────────

def update_training_set():
    """Replace any existing 2026 rows in training set with updated dataset."""
    log("9-TRAINING", "Updating training set...")

    ts = pd.read_csv(TRAINING_SET)
    ds = pd.read_csv(DATASET_DIR / f"{YEAR}_dataset.csv")

    # Verify columns match
    if list(ts.columns) != list(ds.columns):
        log("9-TRAINING", "ERROR: Column mismatch between training set and dataset!")
        ts_set = set(ts.columns)
        ds_set = set(ds.columns)
        log("9-TRAINING", f"  In training only: {ts_set - ds_set}")
        log("9-TRAINING", f"  In dataset only: {ds_set - ts_set}")
        return False

    # Remove existing 2026 rows
    dates = pd.to_datetime(ts["Date"], format="mixed")
    old_2026_count = (dates.dt.year == YEAR).sum()
    ts = ts[dates.dt.year != YEAR]

    # Append new 2026 data
    combined = pd.concat([ts, ds], ignore_index=True)
    combined.to_csv(TRAINING_SET, index=False)

    log("9-TRAINING", f"Removed {old_2026_count} old 2026 rows, added {len(ds)} new rows")
    log("9-TRAINING", f"Training set: {len(combined)} total rows")
    return True


# ─── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="MLB Daily ETL Pipeline")
    parser.add_argument("target_date", nargs="?", default=None,
                        help="Target date (YYYY-MM-DD). Defaults to today.")
    parser.add_argument("--skip-fetch", action="store_true",
                        help="Skip API fetches (steps 1-4), only reprocess")
    args = parser.parse_args()

    target_date = args.target_date or datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

    print("=" * 60)
    print(f"  MLB ETL Pipeline")
    print(f"  Target date:  {target_date}")
    print(f"  Yesterday:    {yesterday}")
    print(f"  Skip fetch:   {args.skip_fetch}")
    print("=" * 60)
    print()

    steps = []

    if not args.skip_fetch:
        # Step 1: Fetch game outlook for today
        steps.append(("1-OUTLOOK", fetch_game_outlook(target_date)))

        # Step 1b: Fetch pregame betting odds for today
        steps.append(("1b-ODDS", fetch_betting_odds(target_date)))

        # Step 2: Fetch probable pitchers for today
        steps.append(("2-PITCHERS", fetch_probable_pitchers(target_date)))

        # Step 3: Fetch boxscores for yesterday
        steps.append(("3-BOXSCORES", fetch_boxscores(yesterday)))

        # Step 4: Compute bullpen boxscores for yesterday
        steps.append(("4-BULLPEN", compute_bullpen_boxscores(yesterday)))

        # Step 4b: Update yesterday's game outlook with final scores
        steps.append(("4b-SCORES", update_game_outlook_scores(yesterday)))

        # Step 4c: Backfill missing probable pitchers from actual boxscores
        steps.append(("4c-BACKFILL", backfill_probable_pitchers(yesterday)))

    # Step 5: Compute season-to-date stats for target date
    steps.append(("5-STD", compute_season_to_date(target_date)))

    # Step 6: Compute rolling stats for target date
    steps.append(("6-ROLLING", compute_rolling(target_date)))

    # Step 7: Consolidate processed files
    steps.append(("7-CONSOLIDATE", consolidate()))

    # Step 8: Build dataset
    steps.append(("8-DATASET", build_dataset()))

    # Step 9: Update training set
    steps.append(("9-TRAINING", update_training_set()))

    # Summary
    print()
    print("=" * 60)
    print("  ETL Summary")
    print("=" * 60)
    for name, success in steps:
        status = "OK" if success else "FAILED"
        print(f"  {name}: {status}")
    print("=" * 60)

    failed = [name for name, success in steps if not success]
    if failed:
        print(f"\n  {len(failed)} step(s) failed: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("\n  All steps completed successfully!")


if __name__ == "__main__":
    main()
