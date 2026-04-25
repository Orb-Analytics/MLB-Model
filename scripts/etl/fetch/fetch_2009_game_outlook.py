"""
Fetch 2009 Game Outlook Data (Practice Run - First Few Days)

Fetches the first few days of 2009 season from balldontlie API
and saves to /workspaces/MLB-Model/data/2009_data/mlb_data/raw/bdl_data/game_outlook
"""

import os
import sys
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

# API Configuration
BASE_URL = "https://api.balldontlie.io/mlb/v1"
GAMES_ENDPOINT = f"{BASE_URL}/games"
HEADERS = {"Authorization": API_KEY}

# Output directory for 2009
OUTPUT_DIR = Path("data/2009_data/mlb_data/raw/bdl_data/game_outlook")

# Column order (matching 2025 format)
COLUMN_ORDER = [
    "id", "season", "date", "postseason", "season_type", "status", "venue", "conference_play",
    "home_team_id", "away_team_id", "home_team_slug", "away_team_slug",
    "home_team_abbreviation", "away_team_abbreviation",
    "home_team_display_name", "away_team_display_name",
    "home_team_short_display_name", "away_team_short_display_name",
    "home_team_name", "away_team_name",
    "home_team_location", "away_team_location",
    "home_team_league", "away_team_league",
    "home_team_division", "away_team_division",
    "home_team_score", "away_team_score",
    "favorite_id", "underdog_id", "favorite_abbreviation", "underdog_abbreviation",
    "favorite_display_name", "underdog_display_name",
]


def validate_api_key():
    """Validate that the API key is set."""
    if not API_KEY:
        print("ERROR: BALLDONTLIE_API_KEY not found in environment variables.")
        sys.exit(1)


def fetch_games_for_date(date_str: str, page: int = 1) -> Dict:
    """Fetch games for a specific date from the balldontlie API."""
    params = {
        "dates[]": date_str,
        "per_page": 100,
        "page": page
    }
    
    try:
        response = requests.get(GAMES_ENDPOINT, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  ✗ API request failed for {date_str} (page {page}): {e}")
        return {"data": [], "meta": {}}


def fetch_all_games_for_date(date_str: str) -> List[Dict]:
    """Fetch all games for a specific date, handling pagination."""
    all_games = []
    page = 1
    
    while True:
        response = fetch_games_for_date(date_str, page)
        games = response.get("data", [])
        
        if not games:
            break
            
        all_games.extend(games)
        
        meta = response.get("meta", {})
        current_page = meta.get("current_page", page)
        total_pages = meta.get("total_pages", 1)
        
        if current_page >= total_pages:
            break
            
        page += 1
        time.sleep(0.3)
    
    return all_games


def filter_regular_season_games(games: List[Dict]) -> List[Dict]:
    """Filter games to only include regular season games with final scores."""
    regular_season_games = []
    
    for game in games:
        is_postseason = game.get("postseason", False)
        season_type = game.get("season_type", "")
        status = game.get("status", "")
        
        home_data = game.get("home_team_data", {})
        away_data = game.get("away_team_data", {})
        has_scores = home_data.get("runs") is not None and away_data.get("runs") is not None
        
        if not is_postseason and season_type == "regular" and status == "STATUS_FINAL" and has_scores:
            regular_season_games.append(game)
    
    return regular_season_games


def flatten_game_data(game: Dict) -> Dict:
    """Flatten nested game data into a flat dictionary."""
    flattened = {}
    
    # Top-level fields
    flattened["id"] = game.get("id")
    flattened["season"] = game.get("season")
    flattened["date"] = game.get("date")
    flattened["postseason"] = game.get("postseason")
    flattened["season_type"] = game.get("season_type")
    flattened["status"] = game.get("status")
    flattened["venue"] = game.get("venue")
    flattened["conference_play"] = game.get("conference_play")
    
    # Home team
    home_team = game.get("home_team", {})
    flattened["home_team_id"] = home_team.get("id")
    flattened["home_team_slug"] = home_team.get("slug")
    flattened["home_team_abbreviation"] = home_team.get("abbreviation")
    flattened["home_team_display_name"] = home_team.get("display_name")
    flattened["home_team_short_display_name"] = home_team.get("short_display_name")
    flattened["home_team_name"] = home_team.get("name")
    flattened["home_team_location"] = home_team.get("location")
    flattened["home_team_league"] = home_team.get("league")
    flattened["home_team_division"] = home_team.get("division")
    
    # Away team
    away_team = game.get("away_team", {})
    flattened["away_team_id"] = away_team.get("id")
    flattened["away_team_slug"] = away_team.get("slug")
    flattened["away_team_abbreviation"] = away_team.get("abbreviation")
    flattened["away_team_display_name"] = away_team.get("display_name")
    flattened["away_team_short_display_name"] = away_team.get("short_display_name")
    flattened["away_team_name"] = away_team.get("name")
    flattened["away_team_location"] = away_team.get("location")
    flattened["away_team_league"] = away_team.get("league")
    flattened["away_team_division"] = away_team.get("division")
    
    # Scores
    home_team_data = game.get("home_team_data", {})
    away_team_data = game.get("away_team_data", {})
    flattened["home_team_score"] = home_team_data.get("runs")
    flattened["away_team_score"] = away_team_data.get("runs")
    
    # Favorite/Underdog (empty)
    flattened["favorite_id"] = None
    flattened["underdog_id"] = None
    flattened["favorite_abbreviation"] = None
    flattened["underdog_abbreviation"] = None
    flattened["favorite_display_name"] = None
    flattened["underdog_display_name"] = None
    
    return flattened


def save_games_to_csv(games: List[Dict], date_str: str) -> bool:
    """Save games to a CSV file for the given date."""
    if not games:
        return False
        
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    filename = f"game_outlook_{date_str}.csv"
    filepath = OUTPUT_DIR / filename
    
    df = pd.DataFrame(games)
    
    # Ensure all columns exist and in correct order
    for col in COLUMN_ORDER:
        if col not in df.columns:
            df[col] = None
    
    df = df[COLUMN_ORDER]
    df.to_csv(filepath, index=False)
    
    return True


def main():
    print("=" * 80)
    print("FETCHING 2009 GAME OUTLOOK DATA (FULL SEASON)")
    print("=" * 80)
    print()
    
    validate_api_key()
    
    # 2009 season: April 5 - October 7 (regular season)
    start_date = datetime(2009, 4, 5)
    end_date = datetime(2009, 10, 7)
    num_days = (end_date - start_date).days + 1
    
    print(f"Fetching {num_days} days starting from {start_date.date()}")
    print(f"Output: {OUTPUT_DIR}")
    print()
    
    total_games = 0
    files_created = 0
    
    for day_offset in range(num_days):
        current_date = start_date + timedelta(days=day_offset)
        date_str = current_date.strftime('%Y-%m-%d')
        
        print(f"Processing {date_str}...")
        
        # Fetch all games
        all_games = fetch_all_games_for_date(date_str)
        print(f"  Fetched {len(all_games)} total games")
        
        # Filter to regular season completed games
        regular_games = filter_regular_season_games(all_games)
        print(f"  Regular season finals: {len(regular_games)}")
        
        if regular_games:
            # Flatten game data
            flattened_games = [flatten_game_data(game) for game in regular_games]
            
            # Save to CSV
            if save_games_to_csv(flattened_games, date_str):
                print(f"  ✓ Saved game_outlook_{date_str}.csv")
                files_created += 1
                total_games += len(flattened_games)
            else:
                print(f"  ✗ Failed to save")
        else:
            print(f"  ⚠ No games to save")
        
        print()
        time.sleep(0.5)
    
    print("=" * 80)
    print(f"✓ Complete: {files_created} files created, {total_games} games total")
    print("=" * 80)


if __name__ == "__main__":
    main()
