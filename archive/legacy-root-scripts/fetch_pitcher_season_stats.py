"""
Fetch season-to-date pitcher statistics for each game.
Calculates cumulative stats up to (but not including) each game.
"""

import requests
import pandas as pd
import time
from datetime import datetime
import glob
import os
from collections import defaultdict

# API configuration
MLB_API_BASE = "https://statsapi.mlb.com/api/v1"
REQUEST_DELAY = 0.3  # seconds between API calls

def get_pitcher_game_log(player_id, season):
    """Fetch game log for a pitcher for a given season."""
    url = f"{MLB_API_BASE}/people/{player_id}/stats"
    params = {
        'stats': 'gameLog',
        'season': season,
        'sportId': 1,
        'group': 'pitching'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'stats' in data and len(data['stats']) > 0:
            if 'splits' in data['stats'][0]:
                return data['stats'][0]['splits']
        return []
    except Exception as e:
        print(f"Error fetching game log for player {player_id}: {e}")
        return []

def calculate_quality_start(innings_pitched, earned_runs):
    """Calculate if a game was a quality start (6+ IP, 3 or fewer ER)."""
    try:
        # Convert IP string like "6.1" to float
        if isinstance(innings_pitched, str):
            parts = innings_pitched.split('.')
            ip = float(parts[0])
            if len(parts) > 1:
                ip += float(parts[1]) / 3.0
        else:
            ip = float(innings_pitched)
        
        er = int(earned_runs)
        return 1 if (ip >= 6.0 and er <= 3) else 0
    except:
        return 0

def calculate_cumulative_stats(game_log, cutoff_date):
    """
    Calculate cumulative stats up to (but not including) the cutoff date.
    
    Args:
        game_log: List of game splits from API
        cutoff_date: Date string in 'YYYY-MM-DD' format
    
    Returns:
        Dictionary of cumulative stats
    """
    # Initialize cumulative stats
    stats = {
        'season': None,
        'postseason': 0,
        'season_type': 'regular',
        'gp': 0,
        'gs': 0,
        'qs': 0,
        'w': 0,
        'l': 0,
        'era': 0.0,
        'sv': 0,
        'hld': 0,
        'ip': 0.0,
        'h': 0,
        'er': 0,
        'hr': 0,
        'bb': 0,
        'whip': 0.0,
        'k': 0,
        'k_per_9': 0.0,
        'war': None  # Not available from MLB API
    }
    
    # Filter games before cutoff date
    relevant_games = [
        game for game in game_log
        if 'date' in game and game['date'] < cutoff_date
    ]
    
    if not relevant_games:
        return stats
    
    # Get season info from first game
    if len(relevant_games) > 0:
        stats['season'] = relevant_games[0].get('season', '2025')
    
    # Calculate cumulative totals
    total_ip = 0.0
    total_er = 0
    total_h = 0
    total_bb = 0
    
    for game in relevant_games:
        game_stat = game.get('stat', {})
        
        stats['gp'] += game_stat.get('gamesPlayed', 0)
        stats['gs'] += game_stat.get('gamesStarted', 0)
        stats['w'] += game_stat.get('wins', 0)
        stats['l'] += game_stat.get('losses', 0)
        stats['sv'] += game_stat.get('saves', 0)
        stats['hld'] += game_stat.get('holds', 0)
        stats['hr'] += game_stat.get('homeRuns', 0)
        stats['bb'] += game_stat.get('baseOnBalls', 0)
        stats['k'] += game_stat.get('strikeOuts', 0)
        stats['h'] += game_stat.get('hits', 0)
        
        # Handle innings pitched (format: "6.1" means 6 and 1/3 innings)
        ip_str = str(game_stat.get('inningsPitched', '0'))
        if ip_str and ip_str != '0':
            parts = ip_str.split('.')
            ip_value = float(parts[0])
            if len(parts) > 1:
                ip_value += float(parts[1]) / 3.0
            total_ip += ip_value
        
        # Earned runs
        er_value = game_stat.get('earnedRuns', 0)
        total_er += er_value
        total_h += game_stat.get('hits', 0)
        total_bb += game_stat.get('baseOnBalls', 0)
        
        # Quality starts
        stats['qs'] += calculate_quality_start(
            game_stat.get('inningsPitched', '0'),
            er_value
        )
    
    stats['ip'] = total_ip
    stats['er'] = total_er
    
    # Calculate rate stats
    if total_ip > 0:
        stats['era'] = round((total_er * 9.0) / total_ip, 2)
        stats['whip'] = round((total_h + total_bb) / total_ip, 2)
        stats['k_per_9'] = round((stats['k'] * 9.0) / total_ip, 2)
    
    return stats

def process_games():
    """Process all games and collect pitcher stats."""
    
    # Get all starting pitcher info files
    pitcher_files = sorted(glob.glob('data/bdl_data/starting_pitcher_info/starting_pitchers_*.csv'))
    
    print(f"Found {len(pitcher_files)} pitcher info files")
    
    # Create output directory
    output_dir = 'data/bdl_data/starting_pitcher_stats'
    os.makedirs(output_dir, exist_ok=True)
    
    total_games = 0
    processed_games = 0
    
    for pitcher_file in pitcher_files:
        # Extract date from filename
        date_str = pitcher_file.split('_')[-1].replace('.csv', '')
        
        # Load pitcher info (already has balldontlie_game_id)
        pitcher_df = pd.read_csv(pitcher_file)
        
        print(f"\nProcessing {date_str}: {len(pitcher_df)} games")
        total_games += len(pitcher_df)
        
        # Collect stats for all games on this date
        game_stats = []
        
        for _, row in pitcher_df.iterrows():
            game_date = row['date']
            game_id = row['game_pk']
            balldontlie_game_id = row['balldontlie_game_id']
            
            home_starter_id = row['home_starter_id']
            away_starter_id = row['away_starter_id']
            
            print(f"  Game {game_id}: {row['away_team_abbreviation']} @ {row['home_team_abbreviation']}", end='')
            
            # Initialize stats dict for this game
            game_stat = {
                'balldontlie_game_id': balldontlie_game_id,
                'id': game_id,
                'date': game_date,
                'home_starter_id': home_starter_id,
                'away_starter_id': away_starter_id,
                'home_starter_full_name': row['home_starter_full_name'],
                'away_starter_full_name': row['away_starter_full_name'],
                'home_starter_team_id': row['home_team_id'],
                'away_starter_team_id': row['away_team_id'],
                'home_starter_team_abbreviation': row['home_team_abbreviation'],
                'away_starter_team_abbreviation': row['away_team_abbreviation'],
            }
            
            # Fetch home starter stats
            if pd.notna(home_starter_id):
                time.sleep(REQUEST_DELAY)
                home_log = get_pitcher_game_log(int(home_starter_id), '2025')
                home_stats = calculate_cumulative_stats(home_log, game_date)
                
                # Add home stats with prefix
                for key, value in home_stats.items():
                    game_stat[f'home_starter_{key}'] = value
            else:
                # Fill with None if no pitcher ID
                for key in ['season', 'postseason', 'season_type', 'gp', 'gs', 'qs', 'w', 'l', 
                           'era', 'sv', 'hld', 'ip', 'h', 'er', 'hr', 'bb', 'whip', 'k', 'k_per_9', 'war']:
                    game_stat[f'home_starter_{key}'] = None
            
            # Fetch away starter stats
            if pd.notna(away_starter_id):
                time.sleep(REQUEST_DELAY)
                away_log = get_pitcher_game_log(int(away_starter_id), '2025')
                away_stats = calculate_cumulative_stats(away_log, game_date)
                
                # Add away stats with prefix
                for key, value in away_stats.items():
                    game_stat[f'away_starter_{key}'] = value
            else:
                # Fill with None if no pitcher ID
                for key in ['season', 'postseason', 'season_type', 'gp', 'gs', 'qs', 'w', 'l', 
                           'era', 'sv', 'hld', 'ip', 'h', 'er', 'hr', 'bb', 'whip', 'k', 'k_per_9', 'war']:
                    game_stat[f'away_starter_{key}'] = None
            
            game_stats.append(game_stat)
            processed_games += 1
            print(f" ✓")
        
        # Save to CSV
        if game_stats:
            output_file = f'{output_dir}/starting_pitcher_stats_{date_str}.csv'
            stats_df = pd.DataFrame(game_stats)
            
            # Reorder columns to match requested format
            column_order = [
                'balldontlie_game_id', 'id', 'date',
                'home_starter_id', 'away_starter_id',
                'home_starter_full_name', 'away_starter_full_name',
                'home_starter_team_id', 'away_starter_team_id',
                'home_starter_team_abbreviation', 'away_starter_team_abbreviation',
                'home_starter_season', 'away_starter_season',
                'home_starter_postseason', 'away_starter_postseason',
                'home_starter_season_type', 'away_starter_season_type',
                'home_starter_pitching_gp', 'away_starter_pitching_gp',
                'home_starter_pitching_gs', 'away_starter_pitching_gs',
                'home_starter_pitching_qs', 'away_starter_pitching_qs',
                'home_starter_pitching_w', 'away_starter_pitching_w',
                'home_starter_pitching_l', 'away_starter_pitching_l',
                'home_starter_pitching_era', 'away_starter_pitching_era',
                'home_starter_pitching_sv', 'away_starter_pitching_sv',
                'home_starter_pitching_hld', 'away_starter_pitching_hld',
                'home_starter_pitching_ip', 'away_starter_pitching_ip',
                'home_starter_pitching_h', 'away_starter_pitching_h',
                'home_starter_pitching_er', 'away_starter_pitching_er',
                'home_starter_pitching_hr', 'away_starter_pitching_hr',
                'home_starter_pitching_bb', 'away_starter_pitching_bb',
                'home_starter_pitching_whip', 'away_starter_pitching_whip',
                'home_starter_pitching_k', 'away_starter_pitching_k',
                'home_starter_pitching_k_per_9', 'away_starter_pitching_k_per_9',
                'home_starter_pitching_war', 'away_starter_pitching_war',
            ]
            
            # Rename columns to match requested format
            stats_df = stats_df.rename(columns={
                'home_starter_gp': 'home_starter_pitching_gp',
                'away_starter_gp': 'away_starter_pitching_gp',
                'home_starter_gs': 'home_starter_pitching_gs',
                'away_starter_gs': 'away_starter_pitching_gs',
                'home_starter_qs': 'home_starter_pitching_qs',
                'away_starter_qs': 'away_starter_pitching_qs',
                'home_starter_w': 'home_starter_pitching_w',
                'away_starter_w': 'away_starter_pitching_w',
                'home_starter_l': 'home_starter_pitching_l',
                'away_starter_l': 'away_starter_pitching_l',
                'home_starter_era': 'home_starter_pitching_era',
                'away_starter_era': 'away_starter_pitching_era',
                'home_starter_sv': 'home_starter_pitching_sv',
                'away_starter_sv': 'away_starter_pitching_sv',
                'home_starter_hld': 'home_starter_pitching_hld',
                'away_starter_hld': 'away_starter_pitching_hld',
                'home_starter_ip': 'home_starter_pitching_ip',
                'away_starter_ip': 'away_starter_pitching_ip',
                'home_starter_h': 'home_starter_pitching_h',
                'away_starter_h': 'away_starter_pitching_h',
                'home_starter_er': 'home_starter_pitching_er',
                'away_starter_er': 'away_starter_pitching_er',
                'home_starter_hr': 'home_starter_pitching_hr',
                'away_starter_hr': 'away_starter_pitching_hr',
                'home_starter_bb': 'home_starter_pitching_bb',
                'away_starter_bb': 'away_starter_pitching_bb',
                'home_starter_whip': 'home_starter_pitching_whip',
                'away_starter_whip': 'away_starter_pitching_whip',
                'home_starter_k': 'home_starter_pitching_k',
                'away_starter_k': 'away_starter_pitching_k',
                'home_starter_k_per_9': 'home_starter_pitching_k_per_9',
                'away_starter_k_per_9': 'away_starter_pitching_k_per_9',
                'home_starter_war': 'home_starter_pitching_war',
                'away_starter_war': 'away_starter_pitching_war',
            })
            
            stats_df = stats_df[column_order]
            stats_df.to_csv(output_file, index=False)
            print(f"Saved {output_file}")
    
    print(f"\n{'='*60}")
    print(f"Complete! Processed {processed_games}/{total_games} games")
    print(f"Files saved to: {output_dir}/")
    print(f"{'='*60}")

if __name__ == '__main__':
    process_games()
