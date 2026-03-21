"""
ETL Script: Fetch MLB Game Outlook Data from balldontlie API

This script collects regular season MLB game data from the balldontlie API
and saves one CSV file per date in the game_outlook section.

Usage:
    python src/etl/fetch_game_outlook.py --start_date 2025-03-27 --end_date 2025-09-28
    python src/etl/fetch_game_outlook.py --start_date 2025-08-15 --end_date 2025-08-15
    python src/etl/fetch_game_outlook.py --start_date 2025-03-27 --end_date 2025-09-28 --overwrite
"""

import os
import sys
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
import time
import argparse

# Load environment variables
load_dotenv()
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

# API Configuration
BASE_URL = "https://api.balldontlie.io/mlb/v1"
GAMES_ENDPOINT = f"{BASE_URL}/games"
HEADERS = {"Authorization": API_KEY}

# Output directory
OUTPUT_DIR = Path("data/bdl_data/game_outlook")

# Column order (as specified)
COLUMN_ORDER = [
    # Top-level game fields
    "id",
    "season",
    "date",
    "postseason",
    "season_type",
    "status",
    "venue",
    "conference_play",
    # Home team fields
    "home_team_id",
    "away_team_id",
    "home_team_slug",
    "away_team_slug",
    "home_team_abbreviation",
    "away_team_abbreviation",
    "home_team_display_name",
    "away_team_display_name",
    "home_team_short_display_name",
    "away_team_short_display_name",
    "home_team_name",
    "away_team_name",
    "home_team_location",
    "away_team_location",
    "home_team_league",
    "away_team_league",
    "home_team_division",
    "away_team_division",
    # Score fields
    "home_team_score",
    "away_team_score",
    # Favorite/Underdog fields (blank for now)
    "favorite_id",
    "underdog_id",
    "favorite_abbreviation",
    "underdog_abbreviation",
    "favorite_display_name",
    "underdog_display_name",
]


def validate_api_key():
    """Validate that the API key is set."""
    if not API_KEY:
        print("ERROR: BALLDONTLIE_API_KEY not found in environment variables.")
        print("Please set it in your .env file or environment.")
        sys.exit(1)


def fetch_games_for_date(date_str: str, page: int = 1) -> Dict:
    """
    Fetch games for a specific date from the balldontlie API.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        page: Page number for pagination
        
    Returns:
        API response as dictionary with 'data' and 'meta' keys
    """
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
    """
    Fetch all games for a specific date, handling pagination.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        List of game dictionaries
    """
    all_games = []
    page = 1
    
    while True:
        response = fetch_games_for_date(date_str, page)
        games = response.get("data", [])
        
        if not games:
            break
            
        all_games.extend(games)
        
        # Check if there are more pages
        meta = response.get("meta", {})
        current_page = meta.get("current_page", page)
        total_pages = meta.get("total_pages", 1)
        
        if current_page >= total_pages:
            break
            
        page += 1
        time.sleep(0.3)  # Rate limiting
    
    return all_games


def filter_regular_season_games(games: List[Dict]) -> List[Dict]:
    """
    Filter games to only include regular season games with final scores.
    
    Args:
        games: List of game dictionaries
        
    Returns:
        Filtered list of regular season games only (completed with scores)
    """
    regular_season_games = []
    
    for game in games:
        # Check if it's regular season
        # season_type must be "regular" (not "spring_training", "postseason", etc.)
        # postseason should be False
        # status should be STATUS_FINAL (game completed)
        # Must have score data present
        is_postseason = game.get("postseason", False)
        season_type = game.get("season_type", "")
        status = game.get("status", "")
        
        # Check for score data
        home_data = game.get("home_team_data", {})
        away_data = game.get("away_team_data", {})
        has_scores = home_data.get("runs") is not None and away_data.get("runs") is not None
        
        # Only include if:
        # - NOT postseason
        # - season_type is "regular"
        # - status is STATUS_FINAL (completed game)
        # - has valid score data
        if not is_postseason and season_type == "regular" and status == "STATUS_FINAL" and has_scores:
            regular_season_games.append(game)
    
    return regular_season_games


def flatten_game_data(game: Dict) -> Dict:
    """
    Flatten nested game data into a flat dictionary with proper column names.
    
    Args:
        game: Raw game dictionary from API
        
    Returns:
        Flattened dictionary with proper column names
    """
    flattened = {}
    
    # Top-level game fields
    flattened["id"] = game.get("id")
    flattened["season"] = game.get("season")
    flattened["date"] = game.get("date")
    flattened["postseason"] = game.get("postseason")
    flattened["season_type"] = game.get("season_type")
    flattened["status"] = game.get("status")
    flattened["venue"] = game.get("venue")
    flattened["conference_play"] = game.get("conference_play")
    
    # Home team fields
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
    
    # Away team fields
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
    
    # Score fields
    home_team_data = game.get("home_team_data", {})
    away_team_data = game.get("away_team_data", {})
    flattened["home_team_score"] = home_team_data.get("runs")
    flattened["away_team_score"] = away_team_data.get("runs")
    
    # Favorite/Underdog fields (blank for now)
    flattened["favorite_id"] = None
    flattened["underdog_id"] = None
    flattened["favorite_abbreviation"] = None
    flattened["underdog_abbreviation"] = None
    flattened["favorite_display_name"] = None
    flattened["underdog_display_name"] = None
    
    return flattened


def save_games_to_csv(games: List[Dict], date_str: str, overwrite: bool = False) -> bool:
    """
    Save games to a CSV file for the given date.
    
    Args:
        games: List of flattened game dictionaries
        date_str: Date in YYYY-MM-DD format
        overwrite: Whether to overwrite existing files
        
    Returns:
        True if successful, False otherwise
    """
    if not games:
        return False
        
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create filename
    filename = f"game_outlook_{date_str}.csv"
    filepath = OUTPUT_DIR / filename
    
    # Check if file exists
    if filepath.exists() and not overwrite:
        print(f"  ⚠ File already exists: {filepath} (use --overwrite to replace)")
        return False
    
    # Convert to DataFrame
    df = pd.DataFrame(games)
    
    # Ensure all columns exist (even if empty) and in correct order
    for col in COLUMN_ORDER:
        if col not in df.columns:
            df[col] = None
    
    # Reorder columns
    df = df[COLUMN_ORDER]
    
    # Save to CSV
    df.to_csv(filepath, index=False)
    
    return True


def process_date(date_str: str, overwrite: bool = False) -> None:
    """
    Process a single date: fetch games, filter, flatten, and save.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        overwrite: Whether to overwrite existing files
    """
    print(f"\n📅 Processing {date_str}...")
    
    # Fetch all games for this date
    games = fetch_all_games_for_date(date_str)
    
    if not games:
        print(f"  ℹ No games found for {date_str}")
        return
    
    print(f"  ✓ Fetched {len(games)} total games")
    
    # Filter to regular season only
    regular_season_games = filter_regular_season_games(games)
    
    if not regular_season_games:
        print(f"  ℹ No regular season games for {date_str}")
        return
    
    print(f"  ✓ Filtered to {len(regular_season_games)} regular season games")
    
    # Flatten game data
    flattened_games = [flatten_game_data(game) for game in regular_season_games]
    
    # Save to CSV
    success = save_games_to_csv(flattened_games, date_str, overwrite)
    
    if success:
        print(f"  ✓ Saved to game_outlook_{date_str}.csv")
    
    # Rate limiting
    time.sleep(0.5)


def generate_date_range(start_date: str, end_date: str) -> List[str]:
    """
    Generate a list of dates between start_date and end_date (inclusive).
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        List of date strings in YYYY-MM-DD format
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    dates = []
    current = start
    
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    
    return dates


def main():
    """Main function to run the ETL script."""
    parser = argparse.ArgumentParser(
        description="Fetch MLB game outlook data from balldontlie API"
    )
    parser.add_argument(
        "--start_date",
        required=True,
        help="Start date in YYYY-MM-DD format (e.g., 2025-03-27)"
    )
    parser.add_argument(
        "--end_date",
        required=True,
        help="End date in YYYY-MM-DD format (e.g., 2025-09-28)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing CSV files"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("MLB Game Outlook ETL Script")
    print("=" * 80)
    
    # Validate API key
    validate_api_key()
    print("✓ API key validated")
    
    # Generate date range
    dates = generate_date_range(args.start_date, args.end_date)
    print(f"✓ Date range: {args.start_date} to {args.end_date} ({len(dates)} days)")
    
    if args.overwrite:
        print("⚠ Overwrite mode: ON")
    
    # Process each date
    for date_str in dates:
        try:
            process_date(date_str, args.overwrite)
        except Exception as e:
            print(f"  ✗ Error processing {date_str}: {e}")
            continue
    
    print("\n" + "=" * 80)
    print("✓ ETL script completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()


# ============================================================================
# USAGE EXAMPLES
# ============================================================================
#
# Example 1: Fetch a single day
# ------------------------------
# python src/etl/fetch_game_outlook.py --start_date 2025-08-15 --end_date 2025-08-15
#
# Example 2: Fetch a week
# -----------------------
# python src/etl/fetch_game_outlook.py --start_date 2025-08-01 --end_date 2025-08-07
#
# Example 3: Fetch entire 2025 regular season (with overwrite)
# ------------------------------------------------------------
# python src/etl/fetch_game_outlook.py --start_date 2025-03-27 --end_date 2025-09-28 --overwrite
#
# Example 4: Fetch specific month
# -------------------------------
# python src/etl/fetch_game_outlook.py --start_date 2025-06-01 --end_date 2025-06-30
#
# ============================================================================
