"""
Compute season-to-date starting pitcher stats for historical years (2009-2024).
For each game, calculate both starters' cumulative stats BEFORE that game is played.
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
        print(f"COMPUTING SEASON-TO-DATE STARTING PITCHER STATS FOR {year}")
        print("="*80)
        print()
    
    # Load all starting pitcher boxscores for this year
    pitcher_pattern = f'data/{year}_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_*.csv'
    pitcher_files = sorted(glob.glob(pitcher_pattern))
    
    if not pitcher_files:
        print(f"❌ No starting pitcher boxscore files found for {year}")
        return
    
    if verbose:
        print(f"Loading {len(pitcher_files)} starting pitcher boxscore files...")
    
    pitcher_boxscores = pd.concat([pd.read_csv(f) for f in pitcher_files], ignore_index=True)
    
    # Also load regular boxscores to get team info and game outcomes
    boxscore_pattern = f'data/{year}_data/mlb_data/raw/boxscores/boxscores_*.csv'
    boxscore_files = sorted(glob.glob(boxscore_pattern))
    boxscores = pd.concat([pd.read_csv(f) for f in boxscore_files], ignore_index=True)
    
    if verbose:
        print(f"Loaded {len(pitcher_boxscores)} pitcher game records")
        print(f"Loaded {len(boxscores)} team boxscores")
        print()
    
    # Merge to get team abbreviations and outcomes
    pitcher_boxscores = pitcher_boxscores.merge(
        boxscores[['game_pk', 'home_team_id', 'away_team_id', 
                   'home_team_abbreviation', 'away_team_abbreviation',
                   'home_batting_r', 'away_batting_r']],
        on='game_pk',
        how='left'
    )
    
    # Sort by date to process chronologically
    pitcher_boxscores['date_dt'] = pd.to_datetime(pitcher_boxscores['date'])
    pitcher_boxscores = pitcher_boxscores.sort_values('date_dt').reset_index(drop=True)
    
    # Initialize pitcher tracking dictionary
    pitcher_stats = defaultdict(lambda: {
        'full_name': '',
        'team_id': 0,
        'team_abbreviation': '',
        'gp': 0,
        'gs': 0,
        'qs': 0,
        'w': 0,
        'l': 0,
        'ip': 0.0,
        'h': 0,
        'er': 0,
        'hr': 0,
        'bb': 0,
        'k': 0
    })
    
    # Create output directory
    output_dir = f'data/{year}_data/mlb_data/season_to_date_stats/starting_pitcher_stats'
    os.makedirs(output_dir, exist_ok=True)
    
    stats_data = []
    
    if verbose:
        print("Processing games chronologically...")
        print()
    
    for idx, game in pitcher_boxscores.iterrows():
        if verbose and idx % 500 == 0 and idx > 0:
            print(f"  Processed {idx}/{len(pitcher_boxscores)} games...")
        
        home_starter_id = int(game['home_starter_id']) if pd.notna(game['home_starter_id']) else 0
        away_starter_id = int(game['away_starter_id']) if pd.notna(game['away_starter_id']) else 0
        
        # Skip if no valid starter IDs
        if home_starter_id == 0 or away_starter_id == 0:
            continue
        
        # Get current stats BEFORE this game
        home_current = pitcher_stats[home_starter_id].copy()
        away_current = pitcher_stats[away_starter_id].copy()
        
        # Update names and teams if not set yet
        if not home_current['full_name']:
            home_current['full_name'] = game['home_starter_name']
            home_current['team_id'] = int(game['home_team_id'])
            home_current['team_abbreviation'] = game['home_team_abbreviation']
        
        if not away_current['full_name']:
            away_current['full_name'] = game['away_starter_name']
            away_current['team_id'] = int(game['away_team_id'])
            away_current['team_abbreviation'] = game['away_team_abbreviation']
        
        # Calculate derived stats
        home_era = safe_divide(home_current['er'] * 9, home_current['ip'])
        away_era = safe_divide(away_current['er'] * 9, away_current['ip'])
        
        home_whip = safe_divide(home_current['h'] + home_current['bb'], home_current['ip'])
        away_whip = safe_divide(away_current['h'] + away_current['bb'], away_current['ip'])
        
        home_k_per_9 = safe_divide(home_current['k'] * 9, home_current['ip'])
        away_k_per_9 = safe_divide(away_current['k'] * 9, away_current['ip'])
        
        # Build stats row
        stats_row = {
            'game_pk': game['game_pk'],
            'date': game['date'],
            'home_starter_id': home_starter_id,
            'away_starter_id': away_starter_id,
            'home_starter_full_name': home_current['full_name'],
            'away_starter_full_name': away_current['full_name'],
            'home_starter_team_id': home_current['team_id'],
            'away_starter_team_id': away_current['team_id'],
            'home_starter_team_abbreviation': home_current['team_abbreviation'],
            'away_starter_team_abbreviation': away_current['team_abbreviation'],
            'home_starter_season': year,
            'away_starter_season': year,
            'home_starter_postseason': 0,
            'away_starter_postseason': 0,
            'home_starter_season_type': 'regular',
            'away_starter_season_type': 'regular',
            'home_starter_pitching_gp': home_current['gp'],
            'away_starter_pitching_gp': away_current['gp'],
            'home_starter_pitching_gs': home_current['gs'],
            'away_starter_pitching_gs': away_current['gs'],
            'home_starter_pitching_qs': home_current['qs'],
            'away_starter_pitching_qs': away_current['qs'],
            'home_starter_pitching_w': home_current['w'],
            'away_starter_pitching_w': away_current['w'],
            'home_starter_pitching_l': home_current['l'],
            'away_starter_pitching_l': away_current['l'],
            'home_starter_pitching_era': round(home_era, 2),
            'away_starter_pitching_era': round(away_era, 2),
            'home_starter_pitching_sv': 0,  # Not applicable for starters
            'away_starter_pitching_sv': 0,
            'home_starter_pitching_hld': 0,  # Not applicable for starters
            'away_starter_pitching_hld': 0,
            'home_starter_pitching_ip': round(home_current['ip'], 1),
            'away_starter_pitching_ip': round(away_current['ip'], 1),
            'home_starter_pitching_h': home_current['h'],
            'away_starter_pitching_h': away_current['h'],
            'home_starter_pitching_er': home_current['er'],
            'away_starter_pitching_er': away_current['er'],
            'home_starter_pitching_hr': home_current['hr'],
            'away_starter_pitching_hr': away_current['hr'],
            'home_starter_pitching_bb': home_current['bb'],
            'away_starter_pitching_bb': away_current['bb'],
            'home_starter_pitching_whip': round(home_whip, 2),
            'away_starter_pitching_whip': round(away_whip, 2),
            'home_starter_pitching_k': home_current['k'],
            'away_starter_pitching_k': away_current['k'],
            'home_starter_pitching_k_per_9': round(home_k_per_9, 2),
            'away_starter_pitching_k_per_9': round(away_k_per_9, 2),
            'home_starter_pitching_war': '',  # Not available
            'away_starter_pitching_war': ''
        }
        
        stats_data.append(stats_row)
        
        # NOW update pitcher stats with this game's results
        # Update names/teams (in case they changed teams mid-season)
        pitcher_stats[home_starter_id]['full_name'] = game['home_starter_name']
        pitcher_stats[home_starter_id]['team_id'] = int(game['home_team_id'])
        pitcher_stats[home_starter_id]['team_abbreviation'] = game['home_team_abbreviation']
        
        pitcher_stats[away_starter_id]['full_name'] = game['away_starter_name']
        pitcher_stats[away_starter_id]['team_id'] = int(game['away_team_id'])
        pitcher_stats[away_starter_id]['team_abbreviation'] = game['away_team_abbreviation']
        
        # Update home starter stats
        pitcher_stats[home_starter_id]['gp'] += 1
        pitcher_stats[home_starter_id]['gs'] += 1
        pitcher_stats[home_starter_id]['ip'] += float(game['home_starter_ip'])
        pitcher_stats[home_starter_id]['h'] += int(game['home_starter_hits'])
        pitcher_stats[home_starter_id]['er'] += int(game['home_starter_earned_runs'])
        pitcher_stats[home_starter_id]['hr'] += int(game['home_starter_homeruns'])
        pitcher_stats[home_starter_id]['bb'] += int(game['home_starter_walks'])
        pitcher_stats[home_starter_id]['k'] += int(game['home_starter_strikeouts'])
        
        # Check for quality start (6+ IP, 3 or fewer ER)
        if float(game['home_starter_ip']) >= 6.0 and int(game['home_starter_earned_runs']) <= 3:
            pitcher_stats[home_starter_id]['qs'] += 1
        
        # Update away starter stats
        pitcher_stats[away_starter_id]['gp'] += 1
        pitcher_stats[away_starter_id]['gs'] += 1
        pitcher_stats[away_starter_id]['ip'] += float(game['away_starter_ip'])
        pitcher_stats[away_starter_id]['h'] += int(game['away_starter_hits'])
        pitcher_stats[away_starter_id]['er'] += int(game['away_starter_earned_runs'])
        pitcher_stats[away_starter_id]['hr'] += int(game['away_starter_homeruns'])
        pitcher_stats[away_starter_id]['bb'] += int(game['away_starter_walks'])
        pitcher_stats[away_starter_id]['k'] += int(game['away_starter_strikeouts'])
        
        # Check for quality start
        if float(game['away_starter_ip']) >= 6.0 and int(game['away_starter_earned_runs']) <= 3:
            pitcher_stats[away_starter_id]['qs'] += 1
        
        # Determine W/L (simplified - starter gets decision if still in game)
        home_runs = int(game['home_batting_r'])
        away_runs = int(game['away_batting_r'])
        
        # Home starter gets W if home team won and they pitched at least 5 IP
        if home_runs > away_runs and float(game['home_starter_ip']) >= 5.0:
            pitcher_stats[home_starter_id]['w'] += 1
        elif away_runs > home_runs and float(game['home_starter_ip']) >= 4.0:
            pitcher_stats[home_starter_id]['l'] += 1
        
        # Away starter gets W if away team won and they pitched at least 5 IP
        if away_runs > home_runs and float(game['away_starter_ip']) >= 5.0:
            pitcher_stats[away_starter_id]['w'] += 1
        elif home_runs > away_runs and float(game['away_starter_ip']) >= 4.0:
            pitcher_stats[away_starter_id]['l'] += 1
    
    if verbose:
        print(f"  Processed {len(pitcher_boxscores)}/{len(pitcher_boxscores)} games... DONE")
        print()
    
    # Create DataFrame
    stats_df = pd.DataFrame(stats_data)
    
    # Save by date
    if verbose:
        print(f"Saving starting pitcher stats files by date...")
    
    saved_files = 0
    for date_str, group in stats_df.groupby('date'):
        file_path = f'{output_dir}/starting_pitcher_stats_{date_str}.csv'
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
    print("SEASON-TO-DATE STARTING PITCHER STATS - HISTORICAL YEARS")
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
