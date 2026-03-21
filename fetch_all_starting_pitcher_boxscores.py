"""
Fetch Starting Pitcher Boxscores for All Games

Purpose:
    For each game in team_boxscores, fetch the individual starting pitcher
    game stats from MLB API and save as starting_pitcher_boxscores.
    
Input:
    /workspaces/MLB-Model/data/mlb_data/team_boxscores/team_boxscores_YYYY-MM-DD.csv
    
Output:
    /workspaces/MLB-Model/data/mlb_data/starting_pitcher_boxscores/starting_pitcher_boxscores_YYYY-MM-DD.csv
"""

import requests
import pandas as pd
import os
import time
from pathlib import Path

MLB_STATS_API = "https://statsapi.mlb.com/api/v1"

# Directories
TEAM_BOXSCORES_DIR = Path("data/mlb_data/team_boxscores")
OUTPUT_DIR = Path("data/mlb_data/starting_pitcher_boxscores")

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_game_boxscore_json(game_pk):
    """Fetch the full boxscore JSON from MLB API."""
    url = f"{MLB_STATS_API}/game/{game_pk}/boxscore"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"    ❌ Error fetching game {game_pk}: {e}")
        return None


def extract_starting_pitcher_stats(boxscore_data):
    """Extract starting pitcher stats from boxscore."""
    if not boxscore_data or 'teams' not in boxscore_data:
        return None
    
    teams = boxscore_data['teams']
    pitcher_stats = {}
    
    for side in ['home', 'away']:
        team_data = teams[side]
        pitcher_ids = team_data.get('pitchers', [])
        players = team_data.get('players', {})
        
        if not pitcher_ids:
            continue
        
        # Starting pitcher is first in the list
        starter_id = pitcher_ids[0]
        starter_key = f"ID{starter_id}"
        
        if starter_key not in players:
            continue
        
        starter_data = players[starter_key]
        person = starter_data.get('person', {})
        stats = starter_data.get('stats', {}).get('pitching', {})
        
        pitcher_stats[side] = {
            'id': person.get('id'),
            'name': person.get('fullName'),
            'team': team_data.get('team', {}).get('name'),
            'ip': stats.get('inningsPitched', 0),
            'hits': stats.get('hits', 0),
            'runs': stats.get('runs', 0),
            'earned_runs': stats.get('earnedRuns', 0),
            'walks': stats.get('baseOnBalls', 0),
            'strikeouts': stats.get('strikeOuts', 0),
            'homeruns': stats.get('homeRuns', 0),
            'era': stats.get('era', 0),
            'whip': stats.get('whip', 0),
            'pitches': stats.get('numberOfPitches', 0),
            'strikes': stats.get('strikes', 0),
            'hit_batters': stats.get('hitBatsmen', 0),
            'wild_pitches': stats.get('wildPitches', 0),
            'balks': stats.get('balks', 0),
            'batters_faced': stats.get('battersFaced', 0),
            'ground_outs': stats.get('groundOuts', 0),
            'air_outs': stats.get('airOuts', 0),
            'wins': stats.get('wins', 0),
            'losses': stats.get('losses', 0),
            'saves': stats.get('saves', 0),
            'blown_saves': stats.get('blownSaves', 0),
            'holds': stats.get('holds', 0),
        }
    
    return pitcher_stats


def create_alternating_row(pitcher_stats):
    """Create single row with alternating home_starter_/away_starter_ columns."""
    if not pitcher_stats or 'home' not in pitcher_stats or 'away' not in pitcher_stats:
        return None
    
    row = {}
    stat_keys = list(pitcher_stats['home'].keys())
    
    for key in stat_keys:
        row[f'home_starter_{key}'] = pitcher_stats['home'][key]
        row[f'away_starter_{key}'] = pitcher_stats['away'][key]
    
    return row


def process_team_boxscore_file(team_boxscore_path):
    """
    Process a single team boxscore file and create starting pitcher boxscore.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    # Read the team boxscore to get game IDs
    team_df = pd.read_csv(team_boxscore_path)
    
    if team_df.empty:
        return False, "Empty file"
    
    # Extract filename and date
    filename = team_boxscore_path.stem  # e.g., 'team_boxscores_2025-03-18'
    date_str = filename.replace('team_boxscores_', '')  # e.g., '2025-03-18'
    
    # Output filename
    output_filename = f"starting_pitcher_boxscores_{date_str}.csv"
    output_path = OUTPUT_DIR / output_filename
    
    # Check if already exists
    if output_path.exists():
        return True, "Already exists (skipped)"
    
    # Collect starting pitcher stats for all games on this date
    all_rows = []
    
    for idx, game_row in team_df.iterrows():
        game_pk = game_row['id']  # MLB game ID
        
        # Fetch boxscore
        boxscore = get_game_boxscore_json(game_pk)
        
        if not boxscore:
            print(f"    ⚠ Could not fetch game {game_pk}")
            continue
        
        # Extract starting pitcher stats
        pitcher_stats = extract_starting_pitcher_stats(boxscore)
        
        if not pitcher_stats or 'home' not in pitcher_stats or 'away' not in pitcher_stats:
            print(f"    ⚠ Could not extract starters for game {game_pk}")
            continue
        
        # Add game identifiers
        row = {
            'game_pk': game_pk,
            'date': date_str,
        }
        
        # Add alternating starter stats
        starter_row = create_alternating_row(pitcher_stats)
        if starter_row:
            row.update(starter_row)
            all_rows.append(row)
        
        # Be nice to the API
        time.sleep(0.5)
    
    if not all_rows:
        return False, "No starter data extracted"
    
    # Create DataFrame and save
    df = pd.DataFrame(all_rows)
    df.to_csv(output_path, index=False)
    
    return True, f"Saved {len(all_rows)} games"


def main():
    """Process all team boxscore files."""
    print("="*80)
    print("FETCHING STARTING PITCHER BOXSCORES FOR ALL GAMES")
    print("="*80)
    
    # Get all team boxscore files
    team_boxscore_files = sorted(TEAM_BOXSCORES_DIR.glob("team_boxscores_*.csv"))
    
    print(f"\nFound {len(team_boxscore_files)} team boxscore files")
    print(f"Output directory: {OUTPUT_DIR}")
    print()
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for i, filepath in enumerate(team_boxscore_files, 1):
        filename = filepath.name
        print(f"[{i}/{len(team_boxscore_files)}] Processing {filename}...", end=' ')
        
        success, message = process_team_boxscore_file(filepath)
        
        if success:
            if "skipped" in message.lower():
                skip_count += 1
                print(f"⏭  {message}")
            else:
                success_count += 1
                print(f"✓ {message}")
        else:
            error_count += 1
            print(f"❌ {message}")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"  Processed:  {success_count} files")
    print(f"  Skipped:    {skip_count} files (already existed)")
    print(f"  Errors:     {error_count} files")
    print(f"  Total:      {len(team_boxscore_files)} files")
    print("="*80)
    
    # Show sample output files
    output_files = sorted(OUTPUT_DIR.glob("starting_pitcher_boxscores_*.csv"))
    if output_files:
        print(f"\n✓ Created {len(output_files)} starting pitcher boxscore files")
        print("\nFirst 5 files:")
        for f in output_files[:5]:
            print(f"  - {f.name}")
        if len(output_files) > 5:
            print("\nLast 5 files:")
            for f in output_files[-5:]:
                print(f"  - {f.name}")


if __name__ == "__main__":
    main()
