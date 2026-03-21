"""
ETL Script: Fetch Starting Pitcher Cumulative Stats from balldontlie API

This script collects cumulative pitching statistics for starting pitchers
up to (but not including) each game date to avoid data leakage.

It uses the /mlb/v1/stats endpoint to fetch game-by-game stats, then aggregates
them up to the day before each game.

Prerequisites:
    - Input file with starter IDs must exist for each date
    - Expected input location: data/bdl_data/starting_pitcher_info/starting_pitcher_info_YYYY-MM-DD.csv
    - Input columns: id, date, home_starter_id, away_starter_id
    - Game outlook files needed to map game_ids to dates

Usage:
    python src/etl/fetch_starting_pitcher_stats.py --start_date 2025-03-27 --end_date 2025-09-28
    python src/etl/fetch_starting_pitcher_stats.py --start_date 2025-07-12 --end_date 2025-07-12
    python src/etl/fetch_starting_pitcher_stats.py --start_date 2025-03-27 --end_date 2025-09-28 --overwrite
"""

import os
import sys
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dotenv import load_dotenv
import time
import argparse

# Load environment variables
load_dotenv()
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

# API Configuration
BASE_URL = "https://api.balldontlie.io/mlb/v1"
GAME_STATS_ENDPOINT = f"{BASE_URL}/stats"  # Game-by-game stats
GAMES_ENDPOINT = f"{BASE_URL}/games"  # Game details
HEADERS = {"Authorization": API_KEY}

# Directory paths
INPUT_DIR = Path("data/bdl_data/starting_pitcher_info")
GAME_OUTLOOK_DIR = Path("data/bdl_data/game_outlook")
OUTPUT_DIR = Path("data/bdl_data/starting_pitcher_stats")

# Caches
_GAME_DATE_MAPPING = None
_ALL_GAME_STATS = None  # Cache for all game stats

# Output column order (exact order required)
OUTPUT_COLUMNS = [
    "id",
    "date",
    "home_starter_id",
    "away_starter_id",
    "home_starter_full_name",
    "away_starter_full_name",
    "home_starter_team_id",
    "away_starter_team_id",
    "home_starter_team_abbreviation",
    "away_starter_team_abbreviation",
    "home_starter_season",
    "away_starter_season",
    "home_starter_postseason",
    "away_starter_postseason",
    "home_starter_season_type",
    "away_starter_season_type",
    "home_starter_pitching_gp",
    "away_starter_pitching_gp",
    "home_starter_pitching_gs",
    "away_starter_pitching_gs",
    "home_starter_pitching_qs",
    "away_starter_pitching_qs",
    "home_starter_pitching_w",
    "away_starter_pitching_w",
    "home_starter_pitching_l",
    "away_starter_pitching_l",
    "home_starter_pitching_era",
    "away_starter_pitching_era",
    "home_starter_pitching_sv",
    "away_starter_pitching_sv",
    "home_starter_pitching_hld",
    "away_starter_pitching_hld",
    "home_starter_pitching_ip",
    "away_starter_pitching_ip",
    "home_starter_pitching_h",
    "away_starter_pitching_h",
    "home_starter_pitching_er",
    "away_starter_pitching_er",
    "home_starter_pitching_hr",
    "away_starter_pitching_hr",
    "home_starter_pitching_bb",
    "away_starter_pitching_bb",
    "home_starter_pitching_whip",
    "away_starter_pitching_whip",
    "home_starter_pitching_k",
    "away_starter_pitching_k",
    "home_starter_pitching_k_per_9",
    "away_starter_pitching_k_per_9",
    "home_starter_pitching_war",
    "away_starter_pitching_war",
]


def validate_api_key():
    """Validate that the API key is set."""
    if not API_KEY:
        print("ERROR: BALLDONTLIE_API_KEY not found in environment variables.")
        print("Please set it in your .env file or environment.")
        sys.exit(1)


def fetch_game_dates(game_ids: List[int], max_retries: int = 3) -> Dict[int, str]:
    """
    Fetch game dates for specific game IDs from the games API.
    
    Args:
        game_ids: List of game IDs to look up
        max_retries: Maximum retry attempts
        
    Returns:
        Dictionary mapping game_id to date string (YYYY-MM-DD)
    """
    game_dates = {}
    
    # Batch requests - API allows game_ids parameter
    batch_size = 100
    
    for i in range(0, len(game_ids), batch_size):
        batch = game_ids[i:i+batch_size]
        
        for attempt in range(max_retries):
            try:
                # Use the games endpoint with game_ids filter
                params = {"game_ids[]": batch, "per_page": 100}
                response = requests.get(
                    GAMES_ENDPOINT,
                    headers=HEADERS,
                    params=params,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    games = data.get("data", [])
                    
                    for game in games:
                        game_id = game.get("id")
                        date_str = game.get("date")  # ISO format
                        
                        if game_id and date_str:
                            # Convert ISO timestamp to YYYY-MM-DD
                            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            game_dates[game_id] = date_obj.strftime("%Y-%m-%d")
                    
                    break  # Success
                    
                elif response.status_code == 429:
                    wait_time = 2 ** attempt
                    print(f"  ⚠ Rate limited fetching game dates, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    
                else:
                    print(f"  ⚠ Error fetching game dates: {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"  ⚠ Exception fetching game dates: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        
        time.sleep(0.6)  # Rate limiting
    
    return game_dates


def load_game_date_mapping() -> Dict[int, str]:
    """
    Load all game outlook files to build a mapping from game_id to date.
    This is cached globally to avoid reloading on every call.
    
    Returns:
        Dictionary mapping game_id (int) to date string (YYYY-MM-DD)
    """
    global _GAME_DATE_MAPPING
    
    if _GAME_DATE_MAPPING is not None:
        return _GAME_DATE_MAPPING
    
    print("\n📂 Loading game date mapping from game outlook files...")
    game_date_map = {}
    
    if not GAME_OUTLOOK_DIR.exists():
        print(f"  ⚠ Game outlook directory not found: {GAME_OUTLOOK_DIR}")
        _GAME_DATE_MAPPING = {}
        return _GAME_DATE_MAPPING
    
    # Load all game outlook CSVs
    csv_files = sorted(GAME_OUTLOOK_DIR.glob("game_outlook_*.csv"))
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            if 'id' in df.columns and 'date' in df.columns:
                for _, row in df.iterrows():
                    game_id = int(row['id'])
                    game_date = row['date']  # Already in YYYY-MM-DD format
                    game_date_map[game_id] = game_date
        except Exception as e:
            print(f"  ⚠ Error reading {csv_file}: {e}")
    
    print(f"  ✓ Loaded {len(game_date_map)} game ID to date mappings")
    _GAME_DATE_MAPPING = game_date_map
    return _GAME_DATE_MAPPING


def load_starter_ids_for_date(date_str: str) -> Optional[pd.DataFrame]:
    """
    Load the starter ID input file for a given date.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        DataFrame with columns: id, date, home_starter_id, away_starter_id
        Returns None if file doesn't exist
    """
    input_file = INPUT_DIR / f"starting_pitcher_info_{date_str}.csv"
    
    if not input_file.exists():
        return None
    
    try:
        df = pd.read_csv(input_file)
        required_cols = ['id', 'date', 'home_starter_id', 'away_starter_id']
        
        if not all(col in df.columns for col in required_cols):
            print(f"  ⚠ Input file missing required columns: {input_file}")
            return None
            
        return df
    except Exception as e:
        print(f"  ⚠ Error reading input file {input_file}: {e}")
        return None


def fetch_all_pitcher_game_stats(
    pitcher_ids: Set[int],
    season: int = 2025,
    max_retries: int = 3
) -> List[Dict]:
    """
    Fetch all game-level stats for specific pitcher IDs from balldontlie API.
    This caches the results globally to avoid refetching.
    
    Args:
        pitcher_ids: Set of pitcher IDs to fetch stats for
        season: Season year (to filter results)
        max_retries: Maximum number of retry attempts
        
    Returns:
        List of game stat dictionaries (filtered to pitching performances only)
    """
    global _ALL_GAME_STATS
    
    if _ALL_GAME_STATS is not None:
        return _ALL_GAME_STATS
    
    print(f"\n🔄 Fetching all game stats for {len(pitcher_ids)} pitchers...")
    all_stats = []
    
    # Convert to list for batching
    pitcher_list = list(pitcher_ids)
    
    # The API might have limits on how many player_ids we can send at once
    # Split into batches of 25 players (more conservative for player queries)
    batch_size = 25
    
    for i in range(0, len(pitcher_list), batch_size):
        batch = pitcher_list[i:i+batch_size]
        print(f"  Batch {i//batch_size + 1}/{(len(pitcher_list)-1)//batch_size + 1}: {len(batch)} pitchers")
        
        page = 1
        batch_stats = []
        
        while True:
            params = {
                "player_ids[]": batch,
                "per_page": 100,
                "page": page,
            }
            
            for attempt in range(max_retries):
                try:
                    response = requests.get(
                        GAME_STATS_ENDPOINT,
                        headers=HEADERS,
                        params=params,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        stats = data.get("data", [])
                        
                        # Filter to actual pitching performances (IP > 0)
                        pitching_stats = [
                            s for s in stats 
                            if s.get("ip") is not None and s.get("ip") > 0
                        ]
                        
                        batch_stats.extend(pitching_stats)
                        
                        # Check if there are more pages
                        meta = data.get("meta", {})
                        next_page = meta.get("next_page")
                        
                        if next_page is None:
                            break
                            
                        page = next_page
                        time.sleep(0.6)  # Rate limiting
                        break
                        
                    elif response.status_code == 429:
                        # Rate limit - wait and retry
                        wait_time = 2 ** attempt
                        print(f"  ⚠ Rate limited, waiting {wait_time}s...")
                        time.sleep(wait_time)
                        
                    else:
                        print(f"  ⚠ API error {response.status_code}: {response.text[:200]}")
                        break
                        
                except requests.exceptions.RequestException as e:
                    print(f"  ⚠ Request error (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
            
            # If pagination is done
            if next_page is None:
                break
        
        all_stats.extend(batch_stats)
        print(f"    → Found {len(batch_stats)} pitching performances")
        time.sleep(0.6)  # Rate limiting between batches
    
    print(f"  ✓ Fetched {len(all_stats)} total pitching performances")
    _ALL_GAME_STATS = all_stats
    return all_stats


def aggregate_pitcher_stats_before_date(
    player_stats: List[Dict],
    target_date: str,
    game_date_map: Dict[int, str]
) -> Dict[int, Dict]:
    """
    Aggregate each pitcher's stats up to (but not including) the target date.
    
    Note: player_stats should already be filtered to only pitching performances (IP > 0)
    
    Args:
        player_stats: List of game-level stat dictionaries from API (pitching only)
        target_date: Date string (YYYY-MM-DD) - we want stats BEFORE this date
        game_date_map: Mapping from game_id to date string
        
    Returns:
        Dictionary mapping player_id to their aggregated stats
    """
    # First pass: identify all game_ids that need dates
    all_game_ids = {stat.get("game_id") for stat in player_stats if stat.get("game_id")}
    unmapped_game_ids = [gid for gid in all_game_ids if gid not in game_date_map]
    
    # Fetch dates for unmapped games
    if unmapped_game_ids:
        print(f"  🔄 Fetching dates for {len(unmapped_game_ids)} unmapped games...")
        new_dates = fetch_game_dates(unmapped_game_ids)
        game_date_map.update(new_dates)
        print(f"  ✓ Successfully mapped {len(new_dates)} additional games")
    
    # Group stats by player
    player_game_stats = {}
    games_without_dates = 0
    games_with_dates = 0
    
    for stat in player_stats:
        player_id = stat.get("player", {}).get("id")
        game_id = stat.get("game_id")
        
        if player_id is None or game_id is None:
            continue
        
        # Get the date this game was played
        game_date = game_date_map.get(game_id)
        
        # If still no date after fetching, skip
        if game_date is None:
            games_without_dates += 1
            continue
        
        games_with_dates += 1
        
        # Only include games BEFORE the target date
        if game_date >= target_date:
            continue
        
        if player_id not in player_game_stats:
            player_game_stats[player_id] = []
        
        player_game_stats[player_id].append(stat)
    
    # Report on mapping success
    if games_without_dates > 0:
        print(f"  ⚠ Warning: {games_without_dates} game records still unmapped after lookup")
    print(f"  ℹ Successfully processed {games_with_dates} game records")
    
    # Aggregate stats for each player
    aggregated_stats = {}
    
    for player_id, games in player_game_stats.items():
        if not games:
            continue
        
        # Get player info from first game
        first_game = games[0]
        player_info = first_game.get("player", {})
        
        # Calculate cumulative pitching stats
        total_ip = sum(game.get("ip", 0) or 0 for game in games)
        total_er = sum(game.get("er", 0) or 0 for game in games)
        total_k = sum(game.get("p_k", 0) or 0 for game in games)
        total_hits = sum(game.get("p_hits", 0) or 0 for game in games)
        total_bb = sum(game.get("p_bb", 0) or 0 for game in games)
        total_hr = sum(game.get("p_hr", 0) or 0 for game in games)
        total_wins = sum(game.get("wins", 0) or 0 for game in games)
        total_losses = sum(game.get("losses", 0) or 0 for game in games)
        total_saves = sum(game.get("saves", 0) or 0 for game in games)
        total_holds = sum(game.get("holds", 0) or 0 for game in games)
        total_gs = sum(1 for game in games if game.get("games_started", 0) > 0)
        
        # Calculate derived stats
        era = (total_er / total_ip * 9) if total_ip > 0 else 0
        whip = ((total_hits + total_bb) / total_ip) if total_ip > 0 else 0
        k_per_9 = (total_k / total_ip * 9) if total_ip > 0 else 0
        
        # Count quality starts (6+ IP, 3 or fewer ER)
        qs = sum(1 for game in games 
                 if (game.get("ip", 0) or 0) >= 6 and (game.get("er", 0) or 0) <= 3)
        
        aggregated_stats[player_id] = {
            "player_id": player_id,
            "full_name": player_info.get("full_name"),
            "team_id": None,  # Not available consistently in game stats
            "team_abbreviation": first_game.get("team_name"),
            "season": 2025,
            "postseason": False,
            "season_type": "regular",
            "pitching_gp": len(games),
            "pitching_gs": total_gs,
            "pitching_qs": qs,
            "pitching_w": total_wins,
            "pitching_l": total_losses,
            "pitching_era": round(era, 4),
            "pitching_sv": total_saves,
            "pitching_hld": total_holds,
            "pitching_ip": round(total_ip, 1),
            "pitching_h": total_hits,
            "pitching_er": total_er,
            "pitching_hr": total_hr,
            "pitching_bb": total_bb,
            "pitching_whip": round(whip, 4),
            "pitching_k": total_k,
            "pitching_k_per_9": round(k_per_9, 2),
            "pitching_war": None,  # Not available in game-level stats
        }
    
    return aggregated_stats


def merge_starter_stats(
    games_df: pd.DataFrame,
    aggregated_stats: Dict[int, Dict]
) -> pd.DataFrame:
    """
    Merge home and away starter stats onto game rows.
    
    Args:
        games_df: DataFrame with game info and starter IDs
        aggregated_stats: Dictionary mapping player_id to their aggregated stats
        
    Returns:
        DataFrame with home_starter_* and away_starter_* columns
    """
    # Start with game info
    result_df = games_df[['id', 'date', 'home_starter_id', 'away_starter_id']].copy()
    
    # Convert aggregated stats to DataFrames
    if aggregated_stats:
        stats_df = pd.DataFrame(list(aggregated_stats.values()))
        
        # Merge home starter stats
        home_stats = stats_df.add_prefix('home_starter_')
        home_stats = home_stats.rename(columns={'home_starter_player_id': 'home_starter_id'})
        
        result_df = result_df.merge(
            home_stats,
            on='home_starter_id',
            how='left'
        )
        
        # Merge away starter stats
        away_stats = stats_df.add_prefix('away_starter_')
        away_stats = away_stats.rename(columns={'away_starter_player_id': 'away_starter_id'})
        
        result_df = result_df.merge(
            away_stats,
            on='away_starter_id',
            how='left'
        )
    
    # Ensure all output columns exist
    for col in OUTPUT_COLUMNS:
        if col not in result_df.columns:
            result_df[col] = None
    
    # Reorder to exact output columns
    result_df = result_df[OUTPUT_COLUMNS]
    
    return result_df


def save_starter_stats_to_csv(
    df: pd.DataFrame,
    date_str: str,
    overwrite: bool = False
) -> bool:
    """
    Save starter stats DataFrame to CSV for the given date.
    
    Args:
        df: DataFrame with starter stats
        date_str: Date in YYYY-MM-DD format
        overwrite: Whether to overwrite existing files
        
    Returns:
        True if successful, False otherwise
    """
    if df.empty:
        return False
    
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create filename
    filename = f"starting_pitcher_stats_{date_str}.csv"
    filepath = OUTPUT_DIR / filename
    
    # Check if file exists
    if filepath.exists() and not overwrite:
        print(f"  ⚠ File already exists: {filepath} (use --overwrite to replace)")
        return False
    
    # Save to CSV
    df.to_csv(filepath, index=False)
    
    return True


def process_date(date_str: str, overwrite: bool = False) -> None:
    """
    Process a single date: load starter IDs, aggregate from cached stats, and save.
    
    Note: Assumes _ALL_GAME_STATS has been populated by fetching all pitcher stats first.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        overwrite: Whether to overwrite existing files
    """
    print(f"\n📅 Processing {date_str}...")
    
    # Step 1: Load starter IDs for this date
    games_df = load_starter_ids_for_date(date_str)
    
    if games_df is None:
        print(f"  ℹ No starter info file found for {date_str}, skipping")
        return
    
    if games_df.empty:
        print(f"  ℹ No games found for {date_str}")
        return
    
    print(f"  ✓ Loaded {len(games_df)} games with starter info")
    
    # Step 2: Load game date mapping (cached globally)
    game_date_map = load_game_date_mapping()
    
    # Step 3: Collect all unique starter IDs for this date
    home_starters = set(games_df['home_starter_id'].dropna().astype(int))
    away_starters = set(games_df['away_starter_id'].dropna().astype(int))
    all_starter_ids = home_starters | away_starters
    
    if not all_starter_ids:
        print(f"  ℹ No starter IDs found for {date_str}")
        return
    
    print(f"  ✓ Found {len(all_starter_ids)} unique starter IDs")
    
    # Step 4: Use cached game stats (already fetched in main())
    game_stats_list = _ALL_GAME_STATS
    
    if not game_stats_list:
        print(f"  ⚠ No game stats available (cache empty)")
        aggregated_stats = {}
    else:
        # Step 5: Aggregate stats up to (but not including) this date
        print(f"  🔄 Aggregating stats before {date_str}...")
        aggregated_stats = aggregate_pitcher_stats_before_date(
            game_stats_list,
            date_str,
            game_date_map
        )
        
        # Filter to only the pitchers we need for this date
        relevant_stats = {
            pid: stats for pid, stats in aggregated_stats.items()
            if pid in all_starter_ids
        }
        
        print(f"  ✓ Aggregated stats for {len(relevant_stats)}/{len(all_starter_ids)} pitchers")
        aggregated_stats = relevant_stats
    
    # Step 6: Merge stats with games
    merged_df = merge_starter_stats(games_df, aggregated_stats)
    
    # Step 7: Save to CSV
    success = save_starter_stats_to_csv(merged_df, date_str, overwrite)
    
    if success:
        print(f"  ✅ Saved starter stats for {date_str}")
    else:
        print(f"  ⚠ Failed to save starter stats for {date_str}")


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
        description="Fetch starting pitcher season stats from balldontlie API"
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
    print("STARTING PITCHER STATS ETL")
    print("=" * 80)
    print(f"\nDate range: {args.start_date} to {args.end_date}")
    print(f"Overwrite: {args.overwrite}")
    print(f"Input directory: {INPUT_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Generate date range
    try:
        dates = generate_date_range(args.start_date, args.end_date)
    except ValueError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
    
    print(f"\nProcessing {len(dates)} dates...")
    
    # Step 1: Load game date mapping once (will be cached)
    print("\n" + "=" * 80)
    print("STEP 1: Loading game date mapping...")
    print("=" * 80)
    game_date_map = load_game_date_mapping()
    
    # Step 2: Collect ALL pitcher IDs across all dates
    print("\n" + "=" * 80)
    print("STEP 2: Collecting pitcher IDs from all dates...")
    print("=" * 80)
    
    all_pitcher_ids = set()
    for date_str in dates:
        games_df = load_starter_ids_for_date(date_str)
        if games_df is not None and not games_df.empty:
            home_starters = set(games_df['home_starter_id'].dropna().astype(int))
            away_starters = set(games_df['away_starter_id'].dropna().astype(int))
            all_pitcher_ids.update(home_starters | away_starters)
    
    print(f"  ✓ Found {len(all_pitcher_ids)} unique pitchers across all dates")
    
    # Step 3: Fetch ALL game stats for these pitchers (cached globally)
    print("\n" + "=" * 80)
    print("STEP 3: Fetching game-by-game stats for all pitchers...")
    print("=" * 80)
    
    if all_pitcher_ids:
        fetch_all_pitcher_game_stats(all_pitcher_ids)
    else:
        print("  ⚠ No pitcher IDs found, skipping stats fetch")
    
    # Step 4: Process each date using cached data
    print("\n" + "=" * 80)
    print("STEP 4: Processing each date...")
    print("=" * 80)
    
    for date_str in dates:
        try:
            process_date(date_str, args.overwrite)
        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n⚠ Error processing {date_str}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "=" * 80)
    print("✅ STARTING PITCHER STATS ETL COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
