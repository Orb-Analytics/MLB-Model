"""
Fetch Historical Game Outlook Data for Multiple Years (2010-2024)

Fetches game outlook data from balldontlie API for specified years
and saves to respective year folders in the correct format.
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

# Season date ranges
SEASON_DATES = {
    2010: (datetime(2010, 4, 4), datetime(2010, 10, 3)),
    2011: (datetime(2011, 3, 31), datetime(2011, 9, 28)),
    2012: (datetime(2012, 3, 28), datetime(2012, 10, 3)),
    2013: (datetime(2013, 3, 31), datetime(2013, 9, 30)),
    2014: (datetime(2014, 3, 22), datetime(2014, 9, 28)),
    2015: (datetime(2015, 4, 5), datetime(2015, 10, 4)),
    2016: (datetime(2016, 4, 3), datetime(2016, 10, 2)),
    2017: (datetime(2017, 4, 2), datetime(2017, 10, 1)),
    2018: (datetime(2018, 3, 29), datetime(2018, 10, 1)),
    2019: (datetime(2019, 3, 20), datetime(2019, 9, 29)),
    2020: (datetime(2020, 7, 23), datetime(2020, 9, 27)),  # COVID-shortened
    2021: (datetime(2021, 4, 1), datetime(2021, 10, 3)),
    2022: (datetime(2022, 4, 7), datetime(2022, 10, 5)),
    2023: (datetime(2023, 3, 30), datetime(2023, 10, 1)),
    2024: (datetime(2024, 3, 20), datetime(2024, 9, 29)),
}


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


def save_games_to_csv(games: List[Dict], date_str: str, year: int) -> bool:
    """Save games to a CSV file for the given date and year."""
    if not games:
        return False
        
    # Create output directory for this year
    output_dir = Path(f"data/{year}_data/mlb_data/raw/bdl_data/game_outlook")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"game_outlook_{date_str}.csv"
    filepath = output_dir / filename
    
    df = pd.DataFrame(games)
    
    # Ensure all columns exist and in correct order
    for col in COLUMN_ORDER:
        if col not in df.columns:
            df[col] = None
    
    df = df[COLUMN_ORDER]
    df.to_csv(filepath, index=False)
    
    return True


def process_year(year: int):
    """Process all games for a given year."""
    if year not in SEASON_DATES:
        print(f"⚠ No season dates defined for {year}")
        return
    
    start_date, end_date = SEASON_DATES[year]
    num_days = (end_date - start_date).days + 1
    
    print("=" * 80)
    print(f"PROCESSING {year} SEASON")
    print("=" * 80)
    print(f"Date range: {start_date.date()} to {end_date.date()}")
    print(f"Days to process: {num_days}")
    print()
    
    total_games = 0
    files_created = 0
    
    for day_offset in range(num_days):
        current_date = start_date + timedelta(days=day_offset)
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Fetch all games
        all_games = fetch_all_games_for_date(date_str)
        
        # Filter to regular season completed games
        regular_games = filter_regular_season_games(all_games)
        
        if regular_games:
            # Flatten game data
            flattened_games = [flatten_game_data(game) for game in regular_games]
            
            # Save to CSV
            if save_games_to_csv(flattened_games, date_str, year):
                files_created += 1
                total_games += len(flattened_games)
                
                # Progress update every 10 files
                if files_created % 10 == 0:
                    print(f"  {date_str}: {files_created} files, {total_games} games so far...")
        
        time.sleep(0.5)
    
    print()
    print(f"✓ {year} Complete: {files_created} files created, {total_games} games total")
    print()


def main():
    print("=" * 80)
    print("FETCHING HISTORICAL GAME OUTLOOK DATA (2010-2024)")
    print("=" * 80)
    print()
    
    validate_api_key()
    
    years = range(2010, 2025)  # 2010 through 2024
    
    for year in years:
        process_year(year)
    
    print("=" * 80)
    print("✓ ALL YEARS COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
