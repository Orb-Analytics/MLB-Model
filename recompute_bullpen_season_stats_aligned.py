"""
Recompute team bullpen season-to-date statistics aligned with main dataset.
Ensures output is in exact same order as /workspaces/MLB-Model/data/2025_dataset/2025_dataset.csv
Stats represent team bullpen performance BEFORE each game (for predictive modeling).
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

def main():
    """Main processing function."""
    
    print("=" * 60)
    print("RECOMPUTING BULLPEN SEASON-TO-DATE STATS")
    print("Aligned with main dataset")
    print("=" * 60)
    
    # Step 1: Load main dataset to get the exact game list and order
    print("\n1. Loading main dataset...")
    main_df = pd.read_csv('data/2025_dataset/2025_dataset.csv')
    print(f"   Main dataset has {len(main_df)} games")
    
    # Get the ordered list of game_pks from main dataset
    main_game_pks = main_df['id'].tolist()
    main_game_dates = dict(zip(main_df['id'], main_df['date']))
    
    # Step 2: Load schedule for team mappings
    print("\n2. Loading MLB schedule for team mappings...")
    schedule_df = pd.read_csv('mlb_official_2025_schedule.csv')
    
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
    
    # Step 3: Load all bullpen boxscores
    print("\n3. Loading all bullpen boxscores...")
    boxscore_files = sorted(glob.glob('data/mlb_data/team_bullpen_boxscores/team_bullpen_boxscores_*.csv'))
    print(f"   Found {len(boxscore_files)} boxscore files")
    
    # Combine all boxscores into one DataFrame
    all_boxscores = []
    for file in boxscore_files:
        df = pd.read_csv(file)
        all_boxscores.append(df)
    
    boxscore_df = pd.concat(all_boxscores, ignore_index=True)
    print(f"   Total {len(boxscore_df)} games in boxscores")
    
    # Create a lookup for boxscore data by game_pk
    boxscore_lookup = {}
    for _, row in boxscore_df.iterrows():
        boxscore_lookup[row['game_pk']] = row
    
    # Step 4: Sort main dataset games by date for chronological processing
    print("\n4. Sorting games by date for chronological processing...")
    main_df_sorted = main_df.copy()
    main_df_sorted['datetime'] = pd.to_datetime(main_df_sorted['date'])
    main_df_sorted = main_df_sorted.sort_values(['datetime', 'id']).reset_index(drop=True)
    
    # Step 5: Process games in chronological order, building season-to-date stats
    print("\n5. Computing season-to-date stats...")
    team_stats = defaultdict(initialize_bullpen_stats)
    game_stats_before = {}  # Store stats BEFORE each game
    
    processed = 0
    skipped = 0
    
    for _, row in main_df_sorted.iterrows():
        game_pk = row['id']
        
        # Check if we have boxscore data for this game
        if game_pk not in boxscore_lookup:
            print(f"   Warning: No boxscore data for game {game_pk}")
            skipped += 1
            continue
        
        if game_pk not in game_team_map:
            print(f"   Warning: No team mapping for game {game_pk}")
            skipped += 1
            continue
        
        boxscore_row = boxscore_lookup[game_pk]
        team_info = game_team_map[game_pk]
        
        home_team_id = team_info['home_team_id']
        away_team_id = team_info['away_team_id']
        
        # Initialize team names if first time seeing these teams
        if team_stats[home_team_id]['team_id'] is None:
            team_stats[home_team_id]['team_id'] = home_team_id
            team_stats[home_team_id]['team_name'] = team_info['home_team_name']
        
        if team_stats[away_team_id]['team_id'] is None:
            team_stats[away_team_id]['team_id'] = away_team_id
            team_stats[away_team_id]['team_name'] = team_info['away_team_name']
        
        # Save stats BEFORE this game (for prediction)
        game_stats_before[game_pk] = {
            'game_pk': game_pk,
            'date': main_game_dates[game_pk],
            'home_team_id': home_team_id,
            'away_team_id': away_team_id,
            'home_stats': team_stats[home_team_id].copy(),
            'away_stats': team_stats[away_team_id].copy()
        }
        
        # Update stats with this game's results
        team_stats[home_team_id] = update_bullpen_stats(team_stats[home_team_id], boxscore_row, is_home=True)
        team_stats[away_team_id] = update_bullpen_stats(team_stats[away_team_id], boxscore_row, is_home=False)
        
        processed += 1
    
    print(f"   Processed: {processed} games")
    print(f"   Skipped: {skipped} games (no data)")
    
    # Step 6: Create output in main dataset order
    print("\n6. Creating output files in main dataset order...")
    output_dir = 'data/mlb_data/derived_stats/team_bullpen_season_to_date_stats'
    os.makedirs(output_dir, exist_ok=True)
    
    # Build records in main dataset order
    all_records = []
    for game_pk in main_game_pks:
        if game_pk not in game_stats_before:
            print(f"   Warning: No stats computed for game {game_pk}")
            continue
        
        game_data = game_stats_before[game_pk]
        home_stats = game_data['home_stats']
        away_stats = game_data['away_stats']
        
        record = {
            'game_pk': game_pk,
            'date': game_data['date'],
            'home_team_id': game_data['home_team_id'],
            'away_team_id': game_data['away_team_id'],
            'home_team_name': home_stats['team_name'],
            'away_team_name': away_stats['team_name'],
            'home_games': home_stats['games'],
            'away_games': away_stats['games'],
            'home_total_ip': round(home_stats['total_ip'], 1),
            'away_total_ip': round(away_stats['total_ip'], 1),
            'home_total_hits': home_stats['total_hits'],
            'away_total_hits': away_stats['total_hits'],
            'home_total_hits_per_ip': round(home_stats['total_hits'] / home_stats['total_ip'], 3) if home_stats['total_ip'] > 0 else 0.0,
            'away_total_hits_per_ip': round(away_stats['total_hits'] / away_stats['total_ip'], 3) if away_stats['total_ip'] > 0 else 0.0,
            'home_total_earned_runs': home_stats['total_earned_runs'],
            'away_total_earned_runs': away_stats['total_earned_runs'],
            'home_total_earned_runs_per_ip': round(home_stats['total_earned_runs'] / home_stats['total_ip'], 3) if home_stats['total_ip'] > 0 else 0.0,
            'away_total_earned_runs_per_ip': round(away_stats['total_earned_runs'] / away_stats['total_ip'], 3) if away_stats['total_ip'] > 0 else 0.0,
            'home_total_walks': home_stats['total_walks'],
            'away_total_walks': away_stats['total_walks'],
            'home_total_walks_per_ip': round(home_stats['total_walks'] / home_stats['total_ip'], 3) if home_stats['total_ip'] > 0 else 0.0,
            'away_total_walks_per_ip': round(away_stats['total_walks'] / away_stats['total_ip'], 3) if away_stats['total_ip'] > 0 else 0.0,
            'home_total_strikeouts': home_stats['total_strikeouts'],
            'away_total_strikeouts': away_stats['total_strikeouts'],
            'home_total_strikeouts_per_ip': round(home_stats['total_strikeouts'] / home_stats['total_ip'], 3) if home_stats['total_ip'] > 0 else 0.0,
            'away_total_strikeouts_per_ip': round(away_stats['total_strikeouts'] / away_stats['total_ip'], 3) if away_stats['total_ip'] > 0 else 0.0,
            'home_total_homeruns': home_stats['total_homeruns'],
            'away_total_homeruns': away_stats['total_homeruns'],
            'home_total_homeruns_per_ip': round(home_stats['total_homeruns'] / home_stats['total_ip'], 3) if home_stats['total_ip'] > 0 else 0.0,
            'away_total_homeruns_per_ip': round(away_stats['total_homeruns'] / away_stats['total_ip'], 3) if away_stats['total_ip'] > 0 else 0.0,
            'home_era': home_stats['era'],
            'away_era': away_stats['era'],
            'home_whip': home_stats['whip'],
            'away_whip': away_stats['whip'],
            'home_k_per_9': home_stats['k_per_9'],
            'away_k_per_9': away_stats['k_per_9'],
            'home_k_bb_ratio': home_stats['k_bb_ratio'],
            'away_k_bb_ratio': away_stats['k_bb_ratio'],
            'home_hr_per_9': home_stats['hr_per_9'],
            'away_hr_per_9': away_stats['hr_per_9'],
            'home_bb_per_9': home_stats['bb_per_9'],
            'away_bb_per_9': away_stats['bb_per_9'],
        }
        all_records.append(record)
    
    # Create DataFrame in main dataset order
    all_stats_df = pd.DataFrame(all_records)
    
    # Save consolidated file
    consolidated_file = f"{output_dir}/team_bullpen_season_to_date_all.csv"
    all_stats_df.to_csv(consolidated_file, index=False)
    print(f"   Saved consolidated file: {consolidated_file}")
    print(f"   Total games: {len(all_stats_df)}")
    
    # Step 7: Create individual date files
    print("\n7. Creating individual date files...")
    date_groups = all_stats_df.groupby('date')
    
    for date, group_df in date_groups:
        date_file = f"{output_dir}/team_bullpen_season_to_date_{date}.csv"
        group_df.to_csv(date_file, index=False)
        print(f"   {date}: {len(group_df)} games")
    
    print(f"\n   Created {len(date_groups)} date files")
    
    # Step 8: Final verification
    print("\n8. Final verification...")
    print(f"   Main dataset games: {len(main_df)}")
    print(f"   Output file games: {len(all_stats_df)}")
    print(f"   Match: {len(main_df) == len(all_stats_df)}")
    
    # Check order alignment
    order_match = (main_df['id'].values == all_stats_df['game_pk'].values).all()
    print(f"   Order alignment: {order_match}")
    
    if order_match:
        print("\n✅ SUCCESS! Bullpen stats perfectly aligned with main dataset")
    else:
        print("\n❌ WARNING: Order mismatch detected")
    
    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
