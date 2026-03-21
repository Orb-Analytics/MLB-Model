"""
ETL Script: Fetch Starting Pitcher Cumulative Stats from MLB Stats API

This script uses the official MLB Stats API to collect cumulative pitching statistics
for starting pitchers up to (but not including) each game date.

The MLB API provides proper cumulative season stats without data leakage.

Prerequisites:
    - Input file with starter IDs must exist for each date
    - Expected input location: data/bdl_data/starting_pitcher_info/starting_pitcher_info_YYYY-MM-DD.csv
    - Input columns: id, date, home_starter_id, away_starter_id
    - Note: These use balldontlie player IDs, which we need to map to MLB IDs

Usage:
    python src/etl/fetch_pitcher_stats_mlb_api.py --start_date 2025-07-12 --end_date 2025-07-12
    python src/etl/fetch_pitcher_stats_mlb_api.py --start_date 2025-03-27 --end_date 2025-09-28 --overwrite
"""

import os
import sys
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
import time
import argparse
import json

# MLB Stats API Configuration
MLB_API_BASE = "https://statsapi.mlb.com/api/v1"
MLB_PEOPLE_ENDPOINT = f"{MLB_API_BASE}/people"

# Directory paths
INPUT_DIR = Path("data/bdl_data/starting_pitcher_info")
OUTPUT_DIR = Path("data/bdl_data/starting_pitcher_stats")
MAPPING_FILE = Path("data/player_id_mapping_clean.csv")

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


def load_player_id_mapping() -> Dict[int, int]:
    """
    Load player ID mapping from balldontlie IDs to MLB IDs.
    
    Returns:
        Dictionary mapping balldontlie_id -> mlb_id
    """
    if not MAPPING_FILE.exists():
        print(f"⚠ Player ID mapping file not found: {MAPPING_FILE}")
        print("Run build_player_id_mapping.py first to create the mapping.")
        return {}
    
    try:
        df = pd.read_csv(MAPPING_FILE)
        # Convert to dictionary: bdl_id -> mlb_id
        mapping = dict(zip(df['balldontlie_id'], df['mlb_id']))
        print(f"  ✓ Loaded mapping for {len(mapping)} players")
        return mapping
    except Exception as e:
        print(f"  ⚠ Error loading player ID mapping: {e}")
        return {}


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


def fetch_pitcher_stats_mlb(mlb_player_id: int, through_date: str, season: int = 2025) -> Optional[Dict]:
    """
    Fetch cumulative pitcher stats from MLB Stats API through a specific date.
    
    Args:
        mlb_player_id: MLB player ID
        through_date: Date string (YYYY-MM-DD) - get stats through day BEFORE this
        season: Season year
        
    Returns:
        Dictionary with pitcher stats, or None if not found
    """
    # Calculate the date to query (day before the game)
    game_date = datetime.strptime(through_date, "%Y-%m-%d")
    query_date = game_date - timedelta(days=1)
    query_date_str = query_date.strftime("%Y-%m-%d")
    
    # MLB Stats API endpoint for player stats
    url = f"{MLB_PEOPLE_ENDPOINT}/{mlb_player_id}/stats"
    params = {
        "stats": "season",
        "season": season,
        "gameType": "R",  # Regular season only
        "group": "pitching",
        "endDate": query_date_str  # Stats through this date
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            stats_list = data.get("stats", [])
            
            if not stats_list:
                return None
            
            # Get the splits (should be one entry for season stats)
            splits = stats_list[0].get("splits", [])
            
            if not splits:
                return None
            
            pitching_stats = splits[0].get("stat", {})
            player_info = splits[0].get("player", {})
            team_info = splits[0].get("team", {})
            
            # Extract and normalize stats
            return {
                "player_id": mlb_player_id,
                "full_name": player_info.get("fullName"),
                "team_id": team_info.get("id"),
                "team_abbreviation": team_info.get("abbreviation"),
                "season": season,
                "postseason": False,
                "season_type": "regular",
                "pitching_gp": pitching_stats.get("gamesPlayed"),
                "pitching_gs": pitching_stats.get("gamesStarted"),
                "pitching_qs": pitching_stats.get("qualityStarts", 0),  # May not be available
                "pitching_w": pitching_stats.get("wins"),
                "pitching_l": pitching_stats.get("losses"),
                "pitching_era": float(pitching_stats.get("era", 0)),
                "pitching_sv": pitching_stats.get("saves"),
                "pitching_hld": pitching_stats.get("holds"),
                "pitching_ip": float(pitching_stats.get("inningsPitched", 0)),
                "pitching_h": pitching_stats.get("hits"),
                "pitching_er": pitching_stats.get("earnedRuns"),
                "pitching_hr": pitching_stats.get("homeRuns"),
                "pitching_bb": pitching_stats.get("baseOnBalls"),
                "pitching_whip": float(pitching_stats.get("whip", 0)),
                "pitching_k": pitching_stats.get("strikeOuts"),
                "pitching_k_per_9": float(pitching_stats.get("strikeoutsPer9Inn", 0)),
                "pitching_war": None,  # Not directly available in basic stats
            }
            
        elif response.status_code == 404:
            # Player not found or no stats
            return None
        else:
            print(f"  ⚠ MLB API error {response.status_code} for player {mlb_player_id}")
            return None
            
    except Exception as e:
        print(f"  ⚠ Error fetching MLB stats for player {mlb_player_id}: {e}")
        return None


def merge_starter_stats(
    games_df: pd.DataFrame,
    aggregated_stats: Dict[int, Dict]
) -> pd.DataFrame:
    """
    Merge home and away starter stats onto game rows.
    
    Args:
        games_df: DataFrame with game info and starter IDs  
        aggregated_stats: Dictionary mapping player_id (balldontlie) to their stats
        
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


def process_date(date_str: str, player_id_mapping: Dict[int, int], overwrite: bool = False) -> None:
    """
    Process a single date: load starter IDs, fetch MLB stats, and save.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        player_id_mapping: Dictionary mapping balldontlie_id -> mlb_id
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
    
    # Step 2: Collect all unique starter IDs
    home_ids = set(games_df['home_starter_id'].dropna().astype(int))
    away_ids = set(games_df['away_starter_id'].dropna().astype(int))
    all_starter_ids = home_ids | away_ids
    
    print(f"  📊 Fetching stats for {len(all_starter_ids)} pitchers...")
    
    # Step 3: Fetch stats for each unique starter
    aggregated_stats = {}
    failed_mappings = []
    failed_fetches = []
    
    for bdl_id in sorted(all_starter_ids):
        # Convert balldontlie ID to MLB ID
        mlb_id = player_id_mapping.get(bdl_id)
        
        if mlb_id is None:
            failed_mappings.append(bdl_id)
            continue
        
        # Fetch cumulative stats through day before game
        stats = fetch_pitcher_stats_mlb(mlb_id, date_str)
        
        if stats:
            aggregated_stats[bdl_id] = stats
        else:
            failed_fetches.append((bdl_id, mlb_id))
        
        time.sleep(0.6)  # Rate limiting
    
    print(f"  ✓ Fetched stats for {len(aggregated_stats)}/{len(all_starter_ids)} pitchers")
    
    if failed_mappings:
        print(f"  ⚠ No MLB ID mapping for balldontlie IDs: {failed_mappings}")
    
    if failed_fetches:
        print(f"  ⚠ Failed to fetch stats for {len(failed_fetches)} pitchers")
    
    # Step 4: Merge stats with game data
    merged_df = merge_starter_stats(games_df, aggregated_stats)
    
    # Step 5: Save results
    success = save_starter_stats_to_csv(merged_df, date_str, overwrite)
    
    if success:
        stats_count = len(aggregated_stats)
        print(f"  ✅ Saved starter stats for {len(merged_df)} games ({stats_count} pitchers with stats)")
    
    return


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
        description="Fetch starting pitcher cumulative stats from MLB Stats API"
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
    
    print("=" * 80)
    print("STARTING PITCHER STATS ETL (MLB Stats API)")
    print("=" * 80)
    print(f"\nDate range: {args.start_date} to {args.end_date}")
    print(f"Overwrite: {args.overwrite}")
    print(f"Input directory: {INPUT_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Mapping file: {MAPPING_FILE}")
    
    # Load player ID mapping
    print("\n📂 Loading player ID mapping...")
    player_id_mapping = load_player_id_mapping()
    
    if not player_id_mapping:
        print("\n⚠ ERROR: No player ID mapping loaded!")
        print("Please run build_player_id_mapping.py first to create the mapping.")
        sys.exit(1)
    
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
            process_date(date_str, player_id_mapping, args.overwrite)
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
