"""
ETL Script: Fetch Starting Pitcher Info from balldontlie Plate Appearances API

This script identifies starting pitchers for each game by querying the plate appearances
endpoint and finding the first pitcher in inning 1 (top for away, bottom for home).

Prerequisites:
    - game_outlook CSV files must exist for each date
    - Data location: data/bdl_data/game_outlook/game_outlook_YYYY-MM-DD.csv

Usage:
    python src/etl/fetch_starting_pitcher_info.py --start_date 2025-03-27 --end_date 2025-09-28
    python src/etl/fetch_starting_pitcher_info.py --start_date 2025-07-12 --end_date 2025-07-12
    python src/etl/fetch_starting_pitcher_info.py --start_date 2025-03-27 --end_date 2025-09-28 --overwrite
"""

import os
import sys
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import time
import argparse

# Load environment variables
load_dotenv()
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

# API Configuration
BASE_URL = "https://api.balldontlie.io/mlb/v1"
PLATE_APPEARANCES_ENDPOINT = f"{BASE_URL}/plate_appearances"
PLAYERS_ENDPOINT = f"{BASE_URL}/players"
HEADERS = {"Authorization": API_KEY}

# Directory paths
GAME_OUTLOOK_DIR = Path("data/bdl_data/game_outlook")
OUTPUT_DIR = Path("data/bdl_data/starting_pitcher_info")


def validate_api_key():
    """Validate that the API key is set."""
    if not API_KEY:
        print("ERROR: BALLDONTLIE_API_KEY not found in environment variables.")
        print("Please set it in your .env file or environment.")
        sys.exit(1)


def load_games_for_date(date_str: str) -> Optional[pd.DataFrame]:
    """
    Load game outlook file for a given date to get game IDs.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        DataFrame with game info including id column
        Returns None if file doesn't exist
    """
    game_file = GAME_OUTLOOK_DIR / f"game_outlook_{date_str}.csv"
    
    if not game_file.exists():
        return None
    
    try:
        df = pd.read_csv(game_file)
        
        if 'id' not in df.columns:
            print(f"  ⚠ Game outlook file missing 'id' column: {game_file}")
            return None
            
        return df
    except Exception as e:
        print(f"  ⚠ Error reading game file {game_file}: {e}")
        return None


def fetch_plate_appearances(game_id: int, max_retries: int = 3) -> List[Dict]:
    """
    Fetch plate appearances for a specific game.
    
    Args:
        game_id: The balldontlie game ID
        max_retries: Maximum number of retry attempts
        
    Returns:
        List of plate appearance dictionaries
    """
    all_pas = []
    page = 1
    
    while True:
        params = {
            "game_id": game_id,
            "per_page": 100,
            "page": page,
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    PLATE_APPEARANCES_ENDPOINT,
                    headers=HEADERS,
                    params=params,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    pas = data.get("data", [])
                    all_pas.extend(pas)
                    
                    # Check pagination
                    meta = data.get("meta", {})
                    next_page = meta.get("next_page")
                    
                    if next_page is None:
                        return all_pas
                        
                    page = next_page
                    time.sleep(0.6)  # Rate limiting
                    break
                    
                elif response.status_code == 429:
                    wait_time = 2 ** attempt
                    print(f"    ⚠ Rate limited for game {game_id}, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    
                elif response.status_code == 404:
                    # Game has no plate appearances data
                    return []
                    
                else:
                    print(f"    ⚠ API error {response.status_code} for game {game_id}")
                    return all_pas
                    
            except requests.exceptions.RequestException as e:
                print(f"    ⚠ Request error for game {game_id} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return all_pas
        
        if not next_page:
            break
    
    return all_pas


def identify_starting_pitchers(plate_appearances: List[Dict]) -> Tuple[Optional[int], Optional[int]]:
    """
    Identify the starting pitchers from plate appearances data.
    
    Starting pitchers are:
    - Away starter: first pitcher in inning 1, half_inning "top"
    - Home starter: first pitcher in inning 1, half_inning "bottom"
    
    Args:
        plate_appearances: List of plate appearance dictionaries
        
    Returns:
        Tuple of (home_starter_id, away_starter_id)
    """
    home_starter_id = None
    away_starter_id = None
    
    # Sort by inning and pa_number to ensure we get first appearances
    sorted_pas = sorted(
        plate_appearances,
        key=lambda x: (x.get("inning", 99), x.get("pa_number", 99))
    )
    
    for pa in sorted_pas:
        inning = pa.get("inning")
        half_inning = pa.get("half_inning")
        pitcher_id = pa.get("pitcher_id")
        
        if inning == 1 and half_inning == "top" and away_starter_id is None:
            away_starter_id = pitcher_id
            
        if inning == 1 and half_inning == "bottom" and home_starter_id is None:
            home_starter_id = pitcher_id
        
        # Stop once we have both
        if home_starter_id is not None and away_starter_id is not None:
            break
    
    return home_starter_id, away_starter_id


def get_player_name(player_id: int, max_retries: int = 3) -> Optional[str]:
    """
    Fetch player's full name from balldontlie API.
    
    Args:
        player_id: Player ID
        max_retries: Maximum retry attempts
        
    Returns:
        Player's full name, or None if not found
    """
    url = f"{PLAYERS_ENDPOINT}/{player_id}"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                player = data.get("data", {})
                return player.get("full_name")
                
            elif response.status_code == 404:
                return None
                
            elif response.status_code == 429:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
                
            else:
                return None
                
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return None
    
    return None


def process_date(date_str: str, overwrite: bool = False) -> None:
    """
    Process a single date: load games, fetch PAs, identify starters, and save.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        overwrite: Whether to overwrite existing files
    """
    print(f"\n📅 Processing {date_str}...")
    
    # Step 1: Load games for this date
    games_df = load_games_for_date(date_str)
    
    if games_df is None:
        print(f"  ℹ No game outlook file found for {date_str}, skipping")
        return
    
    if games_df.empty:
        print(f"  ℹ No games found for {date_str}")
        return
    
    print(f"  ✓ Loaded {len(games_df)} games")
    
    # Step 2: Check if output already exists
    output_file = OUTPUT_DIR / f"starting_pitcher_info_{date_str}.csv"
    if output_file.exists() and not overwrite:
        print(f"  ⚠ File already exists: {output_file} (use --overwrite to replace)")
        return
    
    # Step 3: Fetch plate appearances and identify starters for each game
    results = []
    
    for idx, game in games_df.iterrows():
        game_id = game['id']
        date = game['date']
        
        print(f"    Fetching PAs for game {game_id}...", end='', flush=True)
        
        # Fetch plate appearances
        pas = fetch_plate_appearances(game_id)
        
        if not pas:
            print(f" no data")
            # Keep the game but with null starter IDs
            results.append({
                'id': game_id,
                'date': date,
                'home_starter_id': None,
                'home_starter_name': None,
                'away_starter_id': None,
                'away_starter_name': None
            })
            continue
        
        # Identify starting pitchers
        home_starter_id, away_starter_id = identify_starting_pitchers(pas)
        
        # Fetch pitcher names
        home_starter_name = None
        away_starter_name = None
        
        if home_starter_id:
            home_starter_name = get_player_name(home_starter_id)
            time.sleep(0.6)  # Rate limiting
            
        if away_starter_id:
            away_starter_name = get_player_name(away_starter_id)
            time.sleep(0.6)  # Rate limiting
        
        print(f" ✓ (home: {home_starter_name or home_starter_id}, away: {away_starter_name or away_starter_id})")
        
        results.append({
            'id': game_id,
            'date': date,
            'home_starter_id': home_starter_id,
            'home_starter_name': home_starter_name,
            'away_starter_id': away_starter_id,
            'away_starter_name': away_starter_name
        })
        
        time.sleep(0.6)  # Rate limiting between games
    
    # Step 4: Save results
    if not results:
        print(f"  ℹ No starter info collected for {date_str}")
        return
    
    results_df = pd.DataFrame(results)
    
    # Create output directory if needed
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    results_df.to_csv(output_file, index=False)
    
    starters_found = results_df['home_starter_id'].notna().sum()
    print(f"  ✓ Saved starting pitcher info for {len(results_df)} games ({starters_found} with starters)")


def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime object."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def generate_date_range(start_date: str, end_date: str) -> List[str]:
    """Generate list of dates between start_date and end_date (inclusive)."""
    start = parse_date(start_date)
    end = parse_date(end_date)
    
    if start > end:
        raise ValueError("start_date must be before or equal to end_date")
    
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    
    return dates


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Fetch starting pitcher info from balldontlie plate appearances API"
    )
    parser.add_argument(
        "--start_date",
        required=True,
        help="Start date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--end_date",
        required=True,
        help="End date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing CSV files"
    )
    
    args = parser.parse_args()
    
    # Validate API key
    validate_api_key()
    
    print("=" * 80)
    print("STARTING PITCHER INFO ETL")
    print("=" * 80)
    print(f"\nDate range: {args.start_date} to {args.end_date}")
    print(f"Overwrite: {args.overwrite}")
    print(f"Game outlook directory: {GAME_OUTLOOK_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Generate date range
    try:
        dates = generate_date_range(args.start_date, args.end_date)
    except ValueError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
    
    print(f"\nProcessing {len(dates)} dates...")
    
    # Process each date
    for date_str in dates:
        try:
            process_date(date_str, args.overwrite)
        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n⚠ Error processing {date_str}: {e}")
            continue
    
    print("\n" + "=" * 80)
    print("✅ STARTING PITCHER INFO ETL COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
