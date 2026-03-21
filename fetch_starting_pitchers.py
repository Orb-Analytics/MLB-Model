"""
Fetch starting pitcher information for each game from MLB Stats API.
Uses game_pk (id column) from box scores to query pitcher data.
"""

import requests
import pandas as pd
import glob
import os
import time
from datetime import datetime

print("="*80)
print("FETCHING STARTING PITCHER INFORMATION")
print("="*80)
print()

# Create output directory
output_dir = 'data/bdl_data/starting_pitcher_info'
os.makedirs(output_dir, exist_ok=True)

# Load all box scores to get game IDs
print("Loading box scores...")
boxscore_files = sorted(glob.glob('data/bdl_data/boxscores/boxscores_2025-*.csv'))
print(f"Found {len(boxscore_files)} box score files")

def get_starting_pitchers(game_pk):
    """
    Fetch starting pitcher information for a game from MLB Stats API.
    Returns dict with home and away starting pitcher info.
    """
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract starting pitchers
        home_pitchers = data.get('teams', {}).get('home', {}).get('pitchers', [])
        away_pitchers = data.get('teams', {}).get('away', {}).get('pitchers', [])
        
        # Get player info
        players = data.get('teams', {}).get('home', {}).get('players', {})
        players.update(data.get('teams', {}).get('away', {}).get('players', {}))
        
        # Find starting pitchers (usually first in the list)
        home_starter_id = home_pitchers[0] if home_pitchers else None
        away_starter_id = away_pitchers[0] if away_pitchers else None
        
        home_starter_info = None
        away_starter_info = None
        
        # Get home starter details
        if home_starter_id:
            player_key = f"ID{home_starter_id}"
            if player_key in players:
                player = players[player_key]
                home_starter_info = {
                    'player_id': home_starter_id,
                    'full_name': player.get('person', {}).get('fullName', ''),
                    'first_name': player.get('person', {}).get('firstName', ''),
                    'last_name': player.get('person', {}).get('lastName', ''),
                    'jersey_number': player.get('jerseyNumber', ''),
                }
        
        # Get away starter details
        if away_starter_id:
            player_key = f"ID{away_starter_id}"
            if player_key in players:
                player = players[player_key]
                away_starter_info = {
                    'player_id': away_starter_id,
                    'full_name': player.get('person', {}).get('fullName', ''),
                    'first_name': player.get('person', {}).get('firstName', ''),
                    'last_name': player.get('person', {}).get('lastName', ''),
                    'jersey_number': player.get('jerseyNumber', ''),
                }
        
        return {
            'success': True,
            'home_starter': home_starter_info,
            'away_starter': away_starter_info
        }
    
    except Exception as e:
        print(f"      ❌ Error fetching pitchers for game {game_pk}: {e}")
        return {
            'success': False,
            'home_starter': None,
            'away_starter': None,
            'error': str(e)
        }

print()
print("Processing games by date...")
print()

total_games = 0
successful = 0
failed = 0

# Process each date file
for file_idx, file_path in enumerate(boxscore_files):
    date_str = file_path.split('_')[-1].replace('.csv', '')
    
    # Load box scores for this date
    df = pd.read_csv(file_path)
    
    print(f"[{file_idx+1}/{len(boxscore_files)}] Processing {date_str} ({len(df)} games)...")
    
    pitcher_data = []
    
    for idx, game in df.iterrows():
        game_pk = game['id']
        total_games += 1
        
        # Fetch starting pitchers
        result = get_starting_pitchers(game_pk)
        
        if result['success']:
            successful += 1
            
            # Build row with pitcher info
            row = {
                'balldontlie_game_id': game['balldontlie_game_id'],
                'game_pk': game_pk,
                'date': game['date'],
                'home_team_id': game['home_team_id'],
                'away_team_id': game['away_team_id'],
                'home_team_abbreviation': game['home_team_abbreviation'],
                'away_team_abbreviation': game['away_team_abbreviation'],
                'home_team_display_name': game['home_team_display_name'],
                'away_team_display_name': game['away_team_display_name'],
                
                # Home starting pitcher
                'home_starter_id': result['home_starter']['player_id'] if result['home_starter'] else None,
                'home_starter_full_name': result['home_starter']['full_name'] if result['home_starter'] else None,
                'home_starter_first_name': result['home_starter']['first_name'] if result['home_starter'] else None,
                'home_starter_last_name': result['home_starter']['last_name'] if result['home_starter'] else None,
                'home_starter_jersey': result['home_starter']['jersey_number'] if result['home_starter'] else None,
                
                # Away starting pitcher
                'away_starter_id': result['away_starter']['player_id'] if result['away_starter'] else None,
                'away_starter_full_name': result['away_starter']['full_name'] if result['away_starter'] else None,
                'away_starter_first_name': result['away_starter']['first_name'] if result['away_starter'] else None,
                'away_starter_last_name': result['away_starter']['last_name'] if result['away_starter'] else None,
                'away_starter_jersey': result['away_starter']['jersey_number'] if result['away_starter'] else None,
            }
            
            pitcher_data.append(row)
            
            # Show sample
            if result['home_starter'] and result['away_starter']:
                home_name = result['home_starter']['full_name']
                away_name = result['away_starter']['full_name']
                print(f"      ✅ {game['away_team_abbreviation']} @ {game['home_team_abbreviation']}: "
                      f"{away_name} vs {home_name}")
        else:
            failed += 1
        
        # Be respectful to API
        time.sleep(0.3)
    
    # Save file for this date
    if pitcher_data:
        pitcher_df = pd.DataFrame(pitcher_data)
        output_file = f'{output_dir}/starting_pitchers_{date_str}.csv'
        pitcher_df.to_csv(output_file, index=False)
        print(f"      💾 Saved {len(pitcher_df)} games to {output_file.split('/')[-1]}")
    
    print()

print()
print("="*80)
print("SUMMARY")
print("="*80)
print(f"Total games processed: {total_games}")
print(f"Successfully fetched: {successful} ({successful/total_games*100:.1f}%)")
print(f"Failed: {failed}")
print()
print(f"Files saved to: {output_dir}/")
print()
print("="*80)
print("COMPLETE!")
print("="*80)
