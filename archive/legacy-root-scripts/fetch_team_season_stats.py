"""
Generate season-to-date team statistics for each game.
Calculates cumulative team stats up to (but not including) each game.
"""

import pandas as pd
import glob
import os
from collections import defaultdict

def initialize_team_stats():
    """Initialize empty team statistics dictionary."""
    return {
        'postseason': 0,
        'season_type': 'regular',
        'season': '2025',
        'gp': 0,
        'batting_ab': 0,
        'batting_r': 0,
        'batting_h': 0,
        'batting_2b': 0,
        'batting_3b': 0,
        'batting_hr': 0,
        'batting_rbi': 0,
        'batting_tb': 0,
        'batting_bb': 0,
        'batting_so': 0,
        'batting_sb': 0,
        'batting_avg': 0.0,
        'batting_obp': 0.0,
        'batting_slg': 0.0,
        'batting_ops': 0.0,
        'pitching_w': 0,
        'pitching_l': 0,
        'pitching_era': 0.0,
        'pitching_sv': 0,
        'pitching_cg': 0,
        'pitching_sho': 0,
        'pitching_qs': 0,
        'pitching_ip': 0.0,
        'pitching_h': 0,
        'pitching_er': 0,
        'pitching_hr': 0,
        'pitching_bb': 0,
        'pitching_k': 0,
        'pitching_oba': 0.0,
        'pitching_whip': 0.0,
        'fielding_e': 0,
        'fielding_fp': 0.0,
        'fielding_tc': 0,
        'fielding_po': 0,
        'fielding_a': 0,
    }

def calculate_derived_stats(stats):
    """Calculate batting averages and rate stats from cumulative totals."""
    # Batting averages
    if stats['batting_ab'] > 0:
        stats['batting_avg'] = round(stats['batting_h'] / stats['batting_ab'], 3)
        stats['batting_slg'] = round(stats['batting_tb'] / stats['batting_ab'], 3)
    
    # OBP: (H + BB + HBP) / (AB + BB + HBP + SF)
    # We don't have HBP and SF in the data, so approximate
    if stats['batting_ab'] + stats['batting_bb'] > 0:
        stats['batting_obp'] = round((stats['batting_h'] + stats['batting_bb']) / 
                                     (stats['batting_ab'] + stats['batting_bb']), 3)
    
    stats['batting_ops'] = round(stats['batting_obp'] + stats['batting_slg'], 3)
    
    # Pitching ERA
    if stats['pitching_ip'] > 0:
        stats['pitching_era'] = round((stats['pitching_er'] * 9.0) / stats['pitching_ip'], 2)
        stats['pitching_whip'] = round((stats['pitching_h'] + stats['pitching_bb']) / 
                                       stats['pitching_ip'], 2)
    
    # Pitching OBA (opponent batting average)
    # This would need opponent AB, which we approximate from hits and outs
    # For now, leave as 0.0 or calculate if we have the data
    
    # Fielding percentage
    if stats['fielding_tc'] > 0:
        stats['fielding_fp'] = round((stats['fielding_tc'] - stats['fielding_e']) / 
                                     stats['fielding_tc'], 3)
    
    return stats

def convert_ip_to_float(ip_str):
    """Convert innings pitched string (e.g., '9.0') to float with proper fractional innings."""
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

def update_team_stats(team_stats, game_row, is_home):
    """Update team statistics with a game's results."""
    prefix = 'home_' if is_home else 'away_'
    
    # Update games played
    team_stats['gp'] += 1
    
    # Update batting stats
    team_stats['batting_ab'] += int(game_row[f'{prefix}batting_ab'])
    team_stats['batting_r'] += int(game_row[f'{prefix}batting_r'])
    team_stats['batting_h'] += int(game_row[f'{prefix}batting_h'])
    team_stats['batting_2b'] += int(game_row[f'{prefix}batting_2b'])
    team_stats['batting_3b'] += int(game_row[f'{prefix}batting_3b'])
    team_stats['batting_hr'] += int(game_row[f'{prefix}batting_hr'])
    team_stats['batting_rbi'] += int(game_row[f'{prefix}batting_rbi'])
    team_stats['batting_tb'] += int(game_row[f'{prefix}batting_tb'])
    team_stats['batting_bb'] += int(game_row[f'{prefix}batting_bb'])
    team_stats['batting_so'] += int(game_row[f'{prefix}batting_so'])
    team_stats['batting_sb'] += int(game_row[f'{prefix}batting_sb'])
    
    # Update pitching stats
    team_stats['pitching_w'] += int(game_row[f'{prefix}pitching_w'])
    team_stats['pitching_l'] += int(game_row[f'{prefix}pitching_l'])
    team_stats['pitching_ip'] += convert_ip_to_float(game_row[f'{prefix}pitching_ip'])
    team_stats['pitching_h'] += int(game_row[f'{prefix}pitching_h'])
    team_stats['pitching_er'] += int(game_row[f'{prefix}pitching_er'])
    team_stats['pitching_hr'] += int(game_row[f'{prefix}pitching_hr'])
    team_stats['pitching_bb'] += int(game_row[f'{prefix}pitching_bb'])
    team_stats['pitching_k'] += int(game_row[f'{prefix}pitching_k'])
    
    # Check for quality start, complete game, shutout (would need game log detail)
    # For now, approximate from the game data:
    # QS: if starting pitcher went 6+ IP with 3 or fewer ER (we don't have this granularity)
    # CG: if IP = 9.0 (or more for extra innings) 
    # SHO: if CG and ER = 0
    
    # Update fielding stats
    team_stats['fielding_e'] += int(game_row[f'{prefix}fielding_e'])
    
    # Fielding chances calculation (putouts + assists + errors)
    # We don't have PO and A in the box score, so we'll estimate:
    # Each inning = 3 outs, and outs are mostly PO with some assists
    # This is a rough estimate
    opponent_ip = convert_ip_to_float(game_row[f'{"away_" if is_home else "home_"}pitching_ip'])
    outs_recorded = int(opponent_ip * 3)
    team_stats['fielding_po'] += outs_recorded
    team_stats['fielding_a'] += 0  # Can't determine from box score
    team_stats['fielding_tc'] += outs_recorded + int(game_row[f'{prefix}fielding_e'])
    
    # Recalculate derived stats
    team_stats = calculate_derived_stats(team_stats)
    
    return team_stats

def process_team_season_stats():
    """Process all box scores and generate team season stats."""
    
    # Get all box score files
    boxscore_files = sorted(glob.glob('data/bdl_data/boxscores/boxscores_*.csv'))
    
    print(f"Found {len(boxscore_files)} box score files")
    
    # Create output directory
    output_dir = 'data/bdl_data/team_season_stats'
    os.makedirs(output_dir, exist_ok=True)
    
    # Dictionary to store cumulative stats for each team
    team_stats = defaultdict(initialize_team_stats)
    
    total_games = 0
    processed_games = 0
    
    for boxscore_file in boxscore_files:
        # Extract date from filename
        date_str = boxscore_file.split('_')[-1].replace('.csv', '')
        
        # Load box scores
        df = pd.read_csv(boxscore_file)
        
        print(f"\nProcessing {date_str}: {len(df)} games")
        total_games += len(df)
        
        # Collect stats for all games on this date
        game_stats = []
        
        for _, row in df.iterrows():
            home_team_id = row['home_team_id']
            away_team_id = row['away_team_id']
            
            # Get current cumulative stats for both teams (BEFORE this game)
            home_current = team_stats[home_team_id].copy()
            away_current = team_stats[away_team_id].copy()
            
            # Create game stat record
            game_stat = {
                'balldontlie_game_id': row['balldontlie_game_id'],
                'id': row['id'],
                'date': row['date'],
                'home_team_id': home_team_id,
                'away_team_id': away_team_id,
                'home_team_abbreviation': row['home_team_abbreviation'],
                'away_team_abbreviation': row['away_team_abbreviation'],
                'home_team_display_name': row['home_team_display_name'],
                'away_team_display_name': row['away_team_display_name'],
                'home_team_name': row['home_team_name'],
                'away_team_name': row['away_team_name'],
            }
            
            # Add home team cumulative stats (with prefix)
            for key, value in home_current.items():
                game_stat[f'home_{key}'] = value
            
            # Add away team cumulative stats (with prefix)
            for key, value in away_current.items():
                game_stat[f'away_{key}'] = value
            
            game_stats.append(game_stat)
            
            # Now update team stats with this game's results
            team_stats[home_team_id] = update_team_stats(team_stats[home_team_id], row, is_home=True)
            team_stats[away_team_id] = update_team_stats(team_stats[away_team_id], row, is_home=False)
            
            processed_games += 1
        
        # Save to CSV
        if game_stats:
            output_file = f'{output_dir}/team_season_stats_{date_str}.csv'
            stats_df = pd.DataFrame(game_stats)
            
            # Ensure column order matches requested format
            column_order = [
                'balldontlie_game_id', 'id', 'date',
                'home_team_id', 'away_team_id',
                'home_team_abbreviation', 'away_team_abbreviation',
                'home_team_display_name', 'away_team_display_name',
                'home_team_name', 'away_team_name',
                'home_postseason', 'away_postseason',
                'home_season_type', 'away_season_type',
                'home_season', 'away_season',
                'home_gp', 'away_gp',
                'home_batting_ab', 'away_batting_ab',
                'home_batting_r', 'away_batting_r',
                'home_batting_h', 'away_batting_h',
                'home_batting_2b', 'away_batting_2b',
                'home_batting_3b', 'away_batting_3b',
                'home_batting_hr', 'away_batting_hr',
                'home_batting_rbi', 'away_batting_rbi',
                'home_batting_tb', 'away_batting_tb',
                'home_batting_bb', 'away_batting_bb',
                'home_batting_so', 'away_batting_so',
                'home_batting_sb', 'away_batting_sb',
                'home_batting_avg', 'away_batting_avg',
                'home_batting_obp', 'away_batting_obp',
                'home_batting_slg', 'away_batting_slg',
                'home_batting_ops', 'away_batting_ops',
                'home_pitching_w', 'away_pitching_w',
                'home_pitching_l', 'away_pitching_l',
                'home_pitching_era', 'away_pitching_era',
                'home_pitching_sv', 'away_pitching_sv',
                'home_pitching_cg', 'away_pitching_cg',
                'home_pitching_sho', 'away_pitching_sho',
                'home_pitching_qs', 'away_pitching_qs',
                'home_pitching_ip', 'away_pitching_ip',
                'home_pitching_h', 'away_pitching_h',
                'home_pitching_er', 'away_pitching_er',
                'home_pitching_hr', 'away_pitching_hr',
                'home_pitching_bb', 'away_pitching_bb',
                'home_pitching_k', 'away_pitching_k',
                'home_pitching_oba', 'away_pitching_oba',
                'home_pitching_whip', 'away_pitching_whip',
                'home_fielding_e', 'away_fielding_e',
                'home_fielding_fp', 'away_fielding_fp',
                'home_fielding_tc', 'away_fielding_tc',
                'home_fielding_po', 'away_fielding_po',
                'home_fielding_a', 'away_fielding_a',
            ]
            
            stats_df = stats_df[column_order]
            stats_df.to_csv(output_file, index=False)
            print(f"Saved {output_file} ({len(stats_df)} games)")
    
    print(f"\n{'='*60}")
    print(f"Complete! Processed {processed_games}/{total_games} games")
    print(f"Files saved to: {output_dir}/")
    print(f"{'='*60}")
    
    # Show sample stats for a team
    print("\nSample final season stats (Team ID 147 - Yankees):")
    if 147 in team_stats:
        stats = team_stats[147]
        print(f"  Games: {stats['gp']}")
        print(f"  Batting: .{int(stats['batting_avg']*1000):03d} AVG, {stats['batting_hr']} HR, {stats['batting_r']} R")
        print(f"  Pitching: {stats['pitching_w']}-{stats['pitching_l']}, {stats['pitching_era']:.2f} ERA")

if __name__ == '__main__':
    process_team_season_stats()
