"""
Generate season-to-date team bullpen statistics from daily boxscores.
Calculates cumulative team bullpen stats up to (but NOT including) each game.
This shows each team's performance BEFORE the current game for predictive modeling.
"""

import pandas as pd
import glob
import os
from collections import defaultdict

def initialize_bullpen_stats():
    """Initialize empty team bullpen statistics dictionary."""
    return {
        'team_id': None,
        'team_name': None,
        'games': 0,
        'total_ip': 0.0,
        'total_hits': 0,
        'total_earned_runs': 0,
        'total_walks': 0,
        'total_strikeouts': 0,
        'total_homeruns': 0,
        'era': 0.0,
        'whip': 0.0,
        'k_per_9': 0.0,
        'k_bb_ratio': 0.0,
        'hr_per_9': 0.0,
        'bb_per_9': 0.0,
    }

def convert_ip_to_float(ip_str):
    """Convert innings pitched string (e.g., '5.0') to float with proper fractional innings."""
    try:
        if pd.isna(ip_str):
            return 0.0
        ip_str = str(ip_str)
        if '.' in ip_str:
            parts = ip_str.split('.')
            full_innings = float(parts[0])
            partial = float(parts[1])
            # Each out is 1/3 of an inning
            return full_innings + (partial / 3.0)
        return float(ip_str)
    except:
        return 0.0

def calculate_derived_stats(stats):
    """Calculate rate stats from cumulative totals."""
    total_ip = stats['total_ip']
    
    if total_ip > 0:
        # ERA: (Earned Runs * 9) / IP
        stats['era'] = round((stats['total_earned_runs'] * 9.0) / total_ip, 2)
        
        # WHIP: (Hits + Walks) / IP
        stats['whip'] = round((stats['total_hits'] + stats['total_walks']) / total_ip, 2)
        
        # K/9: (Strikeouts * 9) / IP
        stats['k_per_9'] = round((stats['total_strikeouts'] * 9.0) / total_ip, 2)
        
        # HR/9: (Home Runs * 9) / IP
        stats['hr_per_9'] = round((stats['total_homeruns'] * 9.0) / total_ip, 2)
        
        # BB/9: (Walks * 9) / IP
        stats['bb_per_9'] = round((stats['total_walks'] * 9.0) / total_ip, 2)
    
    # K/BB Ratio
    if stats['total_walks'] > 0:
        stats['k_bb_ratio'] = round(stats['total_strikeouts'] / stats['total_walks'], 2)
    else:
        stats['k_bb_ratio'] = float(stats['total_strikeouts']) if stats['total_strikeouts'] > 0 else 0.0
    
    return stats

def update_bullpen_stats(team_stats, bullpen_data, is_home):
    """Update team bullpen statistics with a game's results."""
    prefix = 'home_bullpen_' if is_home else 'away_bullpen_'
    
    # Only update if there was bullpen activity (IP > 0)
    ip = convert_ip_to_float(bullpen_data[f'{prefix}ip'])
    if ip > 0:
        team_stats['games'] += 1
        team_stats['total_ip'] += ip
        team_stats['total_hits'] += int(bullpen_data[f'{prefix}hits'])
        team_stats['total_earned_runs'] += int(bullpen_data[f'{prefix}earned_runs'])
        team_stats['total_walks'] += int(bullpen_data[f'{prefix}walks'])
        team_stats['total_strikeouts'] += int(bullpen_data[f'{prefix}strikeouts'])
        team_stats['total_homeruns'] += int(bullpen_data[f'{prefix}homeruns'])
        
        # Recalculate derived stats
        team_stats = calculate_derived_stats(team_stats)
    
    return team_stats

def process_team_bullpen_season_stats():
    """Process all team bullpen box scores and generate season-to-date stats."""
    
    # Load the schedule to get team ID mappings
    print("Loading MLB schedule for team mappings...")
    schedule_df = pd.read_csv('mlb_official_2025_schedule.csv')
    
    # Create a mapping from game_pk to team IDs and names
    game_team_map = {}
    for _, row in schedule_df.iterrows():
        game_pk = row['mlb_game_pk']
        game_team_map[game_pk] = {
            'home_team_id': row['home_team_id'],
            'home_team_name': row['home_team_name'],
            'away_team_id': row['away_team_id'],
            'away_team_name': row['away_team_name'],
            'date': row['date']
        }
    
    # Get all team bullpen boxscore files
    boxscore_files = sorted(glob.glob('data/mlb_data/team_bullpen_boxscores/team_bullpen_boxscores_*.csv'))
    
    print(f"Found {len(boxscore_files)} bullpen boxscore files")
    
    # Create output directory
    output_dir = 'data/mlb_data/derived_stats/team_bullpen_season_to_date_stats'
    os.makedirs(output_dir, exist_ok=True)
    
    # Dictionary to store cumulative stats for each team
    team_stats = defaultdict(initialize_bullpen_stats)
    
    total_games = 0
    processed_games = 0
    
    for boxscore_file in boxscore_files:
        # Extract date from filename
        date_str = boxscore_file.split('_')[-1].replace('.csv', '')
        
        # Load bullpen box scores
        df = pd.read_csv(boxscore_file)
        
        if len(df) == 0:
            print(f"Skipping {date_str}: no games")
            continue
        
        print(f"Processing {date_str}: {len(df)} games")
        total_games += len(df)
        
        # Collect stats for all games on this date BEFORE updating cumulative stats
        games_to_save = []
        
        for _, row in df.iterrows():
            game_pk = row['game_pk']
            
            # Skip if we don't have team mapping for this game
            if game_pk not in game_team_map:
                print(f"  Warning: No team mapping for game {game_pk}")
                continue
            
            team_info = game_team_map[game_pk]
            home_team_id = team_info['home_team_id']
            away_team_id = team_info['away_team_id']
            
            # Initialize team names if this is first time seeing these teams
            if team_stats[home_team_id]['team_id'] is None:
                team_stats[home_team_id]['team_id'] = home_team_id
                team_stats[home_team_id]['team_name'] = team_info['home_team_name']
            
            if team_stats[away_team_id]['team_id'] is None:
                team_stats[away_team_id]['team_id'] = away_team_id
                team_stats[away_team_id]['team_name'] = team_info['away_team_name']
            
            # Save current stats BEFORE this game (this is what we want for prediction)
            games_to_save.append({
                'game_pk': game_pk,
                'row': row,
                'home_team_id': home_team_id,
                'away_team_id': away_team_id,
                'home_stats_before': team_stats[home_team_id].copy(),
                'away_stats_before': team_stats[away_team_id].copy()
            })
            
            # Now update stats with this game's results for future games
            team_stats[home_team_id] = update_bullpen_stats(team_stats[home_team_id], row, is_home=True)
            team_stats[away_team_id] = update_bullpen_stats(team_stats[away_team_id], row, is_home=False)
            
            processed_games += 1
        
        # Save the stats from BEFORE each game (for prediction)
        stats_records = []
        for game_data in games_to_save:
            home_stats = game_data['home_stats_before']
            away_stats = game_data['away_stats_before']
            
            record = {
                'game_pk': game_data['game_pk'],
                'date': date_str,
                'home_team_id': game_data['home_team_id'],
                'home_team_name': home_stats['team_name'],
                'home_games': home_stats['games'],
                'home_total_ip': round(home_stats['total_ip'], 1),
                'home_total_hits': home_stats['total_hits'],
                'home_total_earned_runs': home_stats['total_earned_runs'],
                'home_total_walks': home_stats['total_walks'],
                'home_total_strikeouts': home_stats['total_strikeouts'],
                'home_total_homeruns': home_stats['total_homeruns'],
                'home_era': home_stats['era'],
                'home_whip': home_stats['whip'],
                'home_k_per_9': home_stats['k_per_9'],
                'home_k_bb_ratio': home_stats['k_bb_ratio'],
                'home_hr_per_9': home_stats['hr_per_9'],
                'home_bb_per_9': home_stats['bb_per_9'],
                'away_team_id': game_data['away_team_id'],
                'away_team_name': away_stats['team_name'],
                'away_games': away_stats['games'],
                'away_total_ip': round(away_stats['total_ip'], 1),
                'away_total_hits': away_stats['total_hits'],
                'away_total_earned_runs': away_stats['total_earned_runs'],
                'away_total_walks': away_stats['total_walks'],
                'away_total_strikeouts': away_stats['total_strikeouts'],
                'away_total_homeruns': away_stats['total_homeruns'],
                'away_era': away_stats['era'],
                'away_whip': away_stats['whip'],
                'away_k_per_9': away_stats['k_per_9'],
                'away_k_bb_ratio': away_stats['k_bb_ratio'],
                'away_hr_per_9': away_stats['hr_per_9'],
                'away_bb_per_9': away_stats['bb_per_9'],
            }
            stats_records.append(record)
        
        if stats_records:
            # Save to date-specific file
            output_file = f"{output_dir}/team_bullpen_season_to_date_{date_str}.csv"
            stats_df = pd.DataFrame(stats_records)
            stats_df = stats_df.sort_values('game_pk')
            stats_df.to_csv(output_file, index=False)
            print(f"  Saved {len(stats_records)} team records to {output_file}")
    
    print(f"\nProcessing complete!")
    print(f"Total games found: {total_games}")
    print(f"Games processed: {processed_games}")
    print(f"Teams tracked: {len(team_stats)}")
    
    # Save a final consolidated file with all dates
    print("\nCreating consolidated file with all dates...")
    all_files = sorted(glob.glob(f"{output_dir}/team_bullpen_season_to_date_*.csv"))
    all_data = []
    for file in all_files:
        df = pd.read_csv(file)
        all_data.append(df)
    
    if all_data:
        consolidated_df = pd.concat(all_data, ignore_index=True)
        consolidated_file = f"{output_dir}/team_bullpen_season_to_date_all.csv"
        consolidated_df.to_csv(consolidated_file, index=False)
        print(f"Saved consolidated file: {consolidated_file}")
        print(f"Total records: {len(consolidated_df)}")

if __name__ == "__main__":
    process_team_bullpen_season_stats()
