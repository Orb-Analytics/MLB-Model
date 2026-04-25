"""
Compute season-to-date team bullpen stats for historical years (2009-2024).
For each game, calculate both teams' cumulative bullpen stats BEFORE that game is played.
Outputs daily CSV files aligned with boxscores.
"""

import pandas as pd
import numpy as np
import glob
import os
from collections import defaultdict
import sys


def safe_divide(numerator, denominator):
    """Safely divide, returning 0.0 if denominator is 0 or NaN."""
    if pd.isna(denominator) or denominator == 0:
        return 0.0
    return numerator / denominator


def process_year(year, verbose=True):
    """Process one year's worth of games."""
    
    if verbose:
        print("="*80)
        print(f"COMPUTING SEASON-TO-DATE TEAM BULLPEN STATS FOR {year}")
        print("="*80)
        print()
    
    # Load all team bullpen boxscores for this year
    if year == 2025:
        bullpen_pattern = f'data/{year}_data/mlb_data/team_bullpen_boxscores/team_bullpen_boxscores_*.csv'
    else:
        bullpen_pattern = f'data/{year}_data/mlb_data/raw/team_bullpen_boxscores/team_bullpen_boxscores_*.csv'
    bullpen_files = sorted(glob.glob(bullpen_pattern))
    
    if not bullpen_files:
        print(f"❌ No team bullpen boxscore files found for {year}")
        return
    
    if verbose:
        print(f"Loading {len(bullpen_files)} team bullpen boxscore files...")
    
    bullpen_boxscores = pd.concat([pd.read_csv(f) for f in bullpen_files], ignore_index=True)
    bullpen_boxscores = bullpen_boxscores.drop_duplicates(subset='game_pk', keep='first')
    
    # Also load regular boxscores to get team names
    if year == 2025:
        boxscore_pattern = f'data/{year}_data/mlb_data/team_boxscores/team_boxscores_*.csv'
    else:
        boxscore_pattern = f'data/{year}_data/mlb_data/raw/boxscores/boxscores_*.csv'
    boxscore_files = sorted(glob.glob(boxscore_pattern))
    boxscores = pd.concat([pd.read_csv(f) for f in boxscore_files], ignore_index=True)
    # 2025 uses 'id' column instead of 'game_pk'
    if year == 2025 and 'id' in boxscores.columns and 'game_pk' not in boxscores.columns:
        boxscores = boxscores.rename(columns={'id': 'game_pk'})
    boxscores = boxscores.drop_duplicates(subset='game_pk', keep='first')
    
    if verbose:
        print(f"Loaded {len(bullpen_boxscores)} bullpen game records")
        print(f"Loaded {len(boxscores)} team boxscores")
        print()
    
    # Merge to get team IDs and names
    bullpen_boxscores = bullpen_boxscores.merge(
        boxscores[['game_pk', 'home_team_id', 'away_team_id', 'home_team_name', 'away_team_name']],
        on='game_pk',
        how='left'
    )
    
    # Sort by date to process chronologically
    bullpen_boxscores['date_dt'] = pd.to_datetime(bullpen_boxscores['date'])
    bullpen_boxscores = bullpen_boxscores.sort_values('date_dt').reset_index(drop=True)
    
    # Initialize team tracking dictionary
    team_stats = defaultdict(lambda: {
        'team_id': 0,
        'team_name': '',
        'games': 0,
        'total_ip': 0.0,
        'total_hits': 0,
        'total_earned_runs': 0,
        'total_walks': 0,
        'total_strikeouts': 0,
        'total_homeruns': 0
    })
    
    # Create output directory
    if year == 2025:
        output_dir = f'data/{year}_data/mlb_data/derived_stats/team_bullpen_season_to_date_stats'
    else:
        output_dir = f'data/{year}_data/mlb_data/season_to_date_stats/team_bullpen_stats'
    os.makedirs(output_dir, exist_ok=True)
    
    stats_data = []
    
    if verbose:
        print("Processing games chronologically...")
        print()
    
    for idx, game in bullpen_boxscores.iterrows():
        if verbose and idx % 500 == 0 and idx > 0:
            print(f"  Processed {idx}/{len(bullpen_boxscores)} games...")
        
        home_team_id = int(game['home_team_id'])
        away_team_id = int(game['away_team_id'])
        
        # Get current stats BEFORE this game
        home_current = team_stats[home_team_id].copy()
        away_current = team_stats[away_team_id].copy()
        
        # Update team info if not set yet
        if not home_current['team_name']:
            home_current['team_id'] = home_team_id
            home_current['team_name'] = game['home_team_name']
        
        if not away_current['team_name']:
            away_current['team_id'] = away_team_id
            away_current['team_name'] = game['away_team_name']
        
        # Calculate per-IP stats
        home_hits_per_ip = safe_divide(home_current['total_hits'], home_current['total_ip'])
        away_hits_per_ip = safe_divide(away_current['total_hits'], away_current['total_ip'])
        
        home_er_per_ip = safe_divide(home_current['total_earned_runs'], home_current['total_ip'])
        away_er_per_ip = safe_divide(away_current['total_earned_runs'], away_current['total_ip'])
        
        home_walks_per_ip = safe_divide(home_current['total_walks'], home_current['total_ip'])
        away_walks_per_ip = safe_divide(away_current['total_walks'], away_current['total_ip'])
        
        home_k_per_ip = safe_divide(home_current['total_strikeouts'], home_current['total_ip'])
        away_k_per_ip = safe_divide(away_current['total_strikeouts'], away_current['total_ip'])
        
        home_hr_per_ip = safe_divide(home_current['total_homeruns'], home_current['total_ip'])
        away_hr_per_ip = safe_divide(away_current['total_homeruns'], away_current['total_ip'])
        
        # Calculate ERA (ER * 9 / IP)
        home_era = safe_divide(home_current['total_earned_runs'] * 9, home_current['total_ip'])
        away_era = safe_divide(away_current['total_earned_runs'] * 9, away_current['total_ip'])
        
        # Calculate WHIP ((H + BB) / IP)
        home_whip = safe_divide(home_current['total_hits'] + home_current['total_walks'], home_current['total_ip'])
        away_whip = safe_divide(away_current['total_hits'] + away_current['total_walks'], away_current['total_ip'])
        
        # Calculate K/9
        home_k_per_9 = safe_divide(home_current['total_strikeouts'] * 9, home_current['total_ip'])
        away_k_per_9 = safe_divide(away_current['total_strikeouts'] * 9, away_current['total_ip'])
        
        # Calculate K/BB ratio
        home_k_bb_ratio = safe_divide(home_current['total_strikeouts'], home_current['total_walks'])
        away_k_bb_ratio = safe_divide(away_current['total_strikeouts'], away_current['total_walks'])
        
        # Calculate HR/9
        home_hr_per_9 = safe_divide(home_current['total_homeruns'] * 9, home_current['total_ip'])
        away_hr_per_9 = safe_divide(away_current['total_homeruns'] * 9, away_current['total_ip'])
        
        # Calculate BB/9
        home_bb_per_9 = safe_divide(home_current['total_walks'] * 9, home_current['total_ip'])
        away_bb_per_9 = safe_divide(away_current['total_walks'] * 9, away_current['total_ip'])
        
        # Build stats row
        stats_row = {
            'game_pk': game['game_pk'],
            'date': game['date'],
            'home_team_id': home_team_id,
            'away_team_id': away_team_id,
            'home_team_name': home_current['team_name'],
            'away_team_name': away_current['team_name'],
            'home_games': home_current['games'],
            'away_games': away_current['games'],
            'home_total_ip': round(home_current['total_ip'], 1),
            'away_total_ip': round(away_current['total_ip'], 1),
            'home_total_hits': home_current['total_hits'],
            'away_total_hits': away_current['total_hits'],
            'home_total_hits_per_ip': round(home_hits_per_ip, 2),
            'away_total_hits_per_ip': round(away_hits_per_ip, 2),
            'home_total_earned_runs': home_current['total_earned_runs'],
            'away_total_earned_runs': away_current['total_earned_runs'],
            'home_total_earned_runs_per_ip': round(home_er_per_ip, 2),
            'away_total_earned_runs_per_ip': round(away_er_per_ip, 2),
            'home_total_walks': home_current['total_walks'],
            'away_total_walks': away_current['total_walks'],
            'home_total_walks_per_ip': round(home_walks_per_ip, 2),
            'away_total_walks_per_ip': round(away_walks_per_ip, 2),
            'home_total_strikeouts': home_current['total_strikeouts'],
            'away_total_strikeouts': away_current['total_strikeouts'],
            'home_total_strikeouts_per_ip': round(home_k_per_ip, 2),
            'away_total_strikeouts_per_ip': round(away_k_per_ip, 2),
            'home_total_homeruns': home_current['total_homeruns'],
            'away_total_homeruns': away_current['total_homeruns'],
            'home_total_homeruns_per_ip': round(home_hr_per_ip, 2),
            'away_total_homeruns_per_ip': round(away_hr_per_ip, 2),
            'home_era': round(home_era, 2),
            'away_era': round(away_era, 2),
            'home_whip': round(home_whip, 2),
            'away_whip': round(away_whip, 2),
            'home_k_per_9': round(home_k_per_9, 2),
            'away_k_per_9': round(away_k_per_9, 2),
            'home_k_bb_ratio': round(home_k_bb_ratio, 2),
            'away_k_bb_ratio': round(away_k_bb_ratio, 2),
            'home_hr_per_9': round(home_hr_per_9, 2),
            'away_hr_per_9': round(away_hr_per_9, 2),
            'home_bb_per_9': round(home_bb_per_9, 2),
            'away_bb_per_9': round(away_bb_per_9, 2)
        }
        
        stats_data.append(stats_row)
        
        # NOW update team stats with this game's results
        # Update team info
        team_stats[home_team_id]['team_id'] = home_team_id
        team_stats[home_team_id]['team_name'] = game['home_team_name']
        team_stats[away_team_id]['team_id'] = away_team_id
        team_stats[away_team_id]['team_name'] = game['away_team_name']
        
        # Update home team stats (only if they used bullpen - IP > 0)
        home_ip = float(game['home_bullpen_ip'])
        if home_ip > 0:
            team_stats[home_team_id]['games'] += 1
            team_stats[home_team_id]['total_ip'] += home_ip
            team_stats[home_team_id]['total_hits'] += int(game['home_bullpen_hits'])
            team_stats[home_team_id]['total_earned_runs'] += int(game['home_bullpen_earned_runs'])
            team_stats[home_team_id]['total_walks'] += int(game['home_bullpen_walks'])
            team_stats[home_team_id]['total_strikeouts'] += int(game['home_bullpen_strikeouts'])
            team_stats[home_team_id]['total_homeruns'] += int(game['home_bullpen_homeruns'])
        
        # Update away team stats (only if they used bullpen - IP > 0)
        away_ip = float(game['away_bullpen_ip'])
        if away_ip > 0:
            team_stats[away_team_id]['games'] += 1
            team_stats[away_team_id]['total_ip'] += away_ip
            team_stats[away_team_id]['total_hits'] += int(game['away_bullpen_hits'])
            team_stats[away_team_id]['total_earned_runs'] += int(game['away_bullpen_earned_runs'])
            team_stats[away_team_id]['total_walks'] += int(game['away_bullpen_walks'])
            team_stats[away_team_id]['total_strikeouts'] += int(game['away_bullpen_strikeouts'])
            team_stats[away_team_id]['total_homeruns'] += int(game['away_bullpen_homeruns'])
    
    if verbose:
        print(f"  Processed {len(bullpen_boxscores)}/{len(bullpen_boxscores)} games... DONE")
        print()
    
    # Create DataFrame
    stats_df = pd.DataFrame(stats_data)
    
    # Save by date
    if verbose:
        print(f"Saving team bullpen stats files by date...")
    
    saved_files = 0
    for date_str, group in stats_df.groupby('date'):
        if year == 2025:
            file_path = f'{output_dir}/team_bullpen_season_to_date_{date_str}.csv'
        else:
            file_path = f'{output_dir}/team_bullpen_stats_{date_str}.csv'
        group.to_csv(file_path, index=False)
        saved_files += 1
    
    if verbose:
        print(f"✓ Saved {saved_files} files to {output_dir}/")
        print()
        print("="*80)
        print(f"SUMMARY FOR {year}")
        print("="*80)
        print(f"  Total games processed: {len(stats_df):,}")
        print(f"  Files created: {saved_files}")
        print(f"  Output directory: {output_dir}")
        print("="*80)
        print()
    
    return {
        'year': year,
        'games': len(stats_df),
        'files': saved_files
    }


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        years = [int(y) for y in sys.argv[1:]]
    else:
        years = list(range(2009, 2025))
    
    print("="*80)
    print("SEASON-TO-DATE TEAM BULLPEN STATS - HISTORICAL YEARS")
    print("="*80)
    print(f"\nYears to process: {', '.join(map(str, years))}")
    print()
    
    results = []
    
    for year in years:
        result = process_year(year, verbose=True)
        if result:
            results.append(result)
    
    # Final summary
    if len(results) > 1:
        print("="*80)
        print("FINAL SUMMARY - ALL YEARS")
        print("="*80)
        
        total_games = sum(r['games'] for r in results)
        total_files = sum(r['files'] for r in results)
        
        print(f"\nTotal games processed: {total_games:,}")
        print(f"Total files created:   {total_files:,}")
        
        print(f"\nBreakdown by year:")
        for r in results:
            print(f"  {r['year']}: {r['files']:3d} files, {r['games']:5,d} games")
        
        print("="*80)


if __name__ == "__main__":
    main()
