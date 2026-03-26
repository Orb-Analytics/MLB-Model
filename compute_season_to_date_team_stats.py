"""
Compute season-to-date team stats for historical years (2009-2024).
For each game, calculate both teams' cumulative stats BEFORE that game is played.
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
        print(f"COMPUTING SEASON-TO-DATE TEAM STATS FOR {year}")
        print("="*80)
        print()
    
    # Load all boxscores for this year
    boxscore_pattern = f'data/{year}_data/mlb_data/raw/boxscores/boxscores_*.csv'
    boxscore_files = sorted(glob.glob(boxscore_pattern))
    
    if not boxscore_files:
        print(f"❌ No boxscore files found for {year}")
        return
    
    if verbose:
        print(f"Loading {len(boxscore_files)} boxscore files...")
    
    boxscores = pd.concat([pd.read_csv(f) for f in boxscore_files], ignore_index=True)
    
    if verbose:
        print(f"Loaded {len(boxscores)} games")
        print()
    
    # Sort by date to process chronologically
    boxscores['date_dt'] = pd.to_datetime(boxscores['date'])
    boxscores = boxscores.sort_values('date_dt').reset_index(drop=True)
    
    # Initialize team tracking dictionary
    team_stats = defaultdict(lambda: {
        # Games played
        'gp': 0,
        
        # Batting stats (cumulative)
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
        
        # Pitching stats (cumulative)
        'pitching_w': 0,
        'pitching_l': 0,
        'pitching_ip': 0.0,
        'pitching_h': 0,
        'pitching_er': 0,
        'pitching_hr': 0,
        'pitching_bb': 0,
        'pitching_k': 0,
        
        # Fielding stats (cumulative)
        'fielding_e': 0
    })
    
    # Create output directory
    output_dir = f'data/{year}_data/mlb_data/season_to_date_stats/team_stats'
    os.makedirs(output_dir, exist_ok=True)
    
    stats_data = []
    
    if verbose:
        print("Processing games chronologically...")
        print()
    
    for idx, game in boxscores.iterrows():
        if verbose and idx % 500 == 0 and idx > 0:
            print(f"  Processed {idx}/{len(boxscores)} games...")
        
        home_team_id = int(game['home_team_id'])
        away_team_id = int(game['away_team_id'])
        home_abbr = game['home_team_abbreviation']
        away_abbr = game['away_team_abbreviation']
        
        # Get current stats BEFORE this game
        home_current = team_stats[home_abbr].copy()
        away_current = team_stats[away_abbr].copy()
        
        # Calculate batting averages and derived stats
        home_batting_avg = safe_divide(home_current['batting_h'], home_current['batting_ab'])
        away_batting_avg = safe_divide(away_current['batting_h'], away_current['batting_ab'])
        
        home_batting_obp = safe_divide(
            home_current['batting_h'] + home_current['batting_bb'],
            home_current['batting_ab'] + home_current['batting_bb']
        )
        away_batting_obp = safe_divide(
            away_current['batting_h'] + away_current['batting_bb'],
            away_current['batting_ab'] + away_current['batting_bb']
        )
        
        home_batting_slg = safe_divide(home_current['batting_tb'], home_current['batting_ab'])
        away_batting_slg = safe_divide(away_current['batting_tb'], away_current['batting_ab'])
        
        home_batting_ops = home_batting_obp + home_batting_slg
        away_batting_ops = away_batting_obp + away_batting_slg
        
        # Calculate pitching ERA and derived stats
        home_pitching_era = safe_divide(home_current['pitching_er'] * 9, home_current['pitching_ip'])
        away_pitching_era = safe_divide(away_current['pitching_er'] * 9, away_current['pitching_ip'])
        
        home_pitching_oba = safe_divide(home_current['pitching_h'], home_current['batting_ab'])  # Opponent batting avg
        away_pitching_oba = safe_divide(away_current['pitching_h'], away_current['batting_ab'])
        
        home_pitching_whip = safe_divide(
            home_current['pitching_h'] + home_current['pitching_bb'],
            home_current['pitching_ip']
        )
        away_pitching_whip = safe_divide(
            away_current['pitching_h'] + away_current['pitching_bb'],
            away_current['pitching_ip']
        )
        
        # Fielding percentage not calculable without TC (total chances)
        home_fielding_fp = 0.0
        away_fielding_fp = 0.0
        
        # Build stats row
        stats_row = {
            'game_pk': game['game_pk'],
            'date': game['date'],
            'home_team_id': home_team_id,
            'away_team_id': away_team_id,
            'home_team_abbreviation': home_abbr,
            'away_team_abbreviation': away_abbr,
            'home_team_display_name': game['home_team_display_name'],
            'away_team_display_name': game['away_team_display_name'],
            'home_team_name': game['home_team_name'],
            'away_team_name': game['away_team_name'],
            'home_postseason': 0,
            'away_postseason': 0,
            'home_season_type': 'regular',
            'away_season_type': 'regular',
            'home_season': year,
            'away_season': year,
            'home_gp': home_current['gp'],
            'away_gp': away_current['gp'],
            
            # Batting stats
            'home_batting_ab': home_current['batting_ab'],
            'away_batting_ab': away_current['batting_ab'],
            'home_batting_r': home_current['batting_r'],
            'away_batting_r': away_current['batting_r'],
            'home_batting_h': home_current['batting_h'],
            'away_batting_h': away_current['batting_h'],
            'home_batting_2b': home_current['batting_2b'],
            'away_batting_2b': away_current['batting_2b'],
            'home_batting_3b': home_current['batting_3b'],
            'away_batting_3b': away_current['batting_3b'],
            'home_batting_hr': home_current['batting_hr'],
            'away_batting_hr': away_current['batting_hr'],
            'home_batting_rbi': home_current['batting_rbi'],
            'away_batting_rbi': away_current['batting_rbi'],
            'home_batting_tb': home_current['batting_tb'],
            'away_batting_tb': away_current['batting_tb'],
            'home_batting_bb': home_current['batting_bb'],
            'away_batting_bb': away_current['batting_bb'],
            'home_batting_so': home_current['batting_so'],
            'away_batting_so': away_current['batting_so'],
            'home_batting_sb': home_current['batting_sb'],
            'away_batting_sb': away_current['batting_sb'],
            'home_batting_avg': round(home_batting_avg, 3),
            'away_batting_avg': round(away_batting_avg, 3),
            'home_batting_obp': round(home_batting_obp, 3),
            'away_batting_obp': round(away_batting_obp, 3),
            'home_batting_slg': round(home_batting_slg, 3),
            'away_batting_slg': round(away_batting_slg, 3),
            'home_batting_ops': round(home_batting_ops, 3),
            'away_batting_ops': round(away_batting_ops, 3),
            
            # Pitching stats
            'home_pitching_w': home_current['pitching_w'],
            'away_pitching_w': away_current['pitching_w'],
            'home_pitching_l': home_current['pitching_l'],
            'away_pitching_l': away_current['pitching_l'],
            'home_pitching_era': round(home_pitching_era, 2),
            'away_pitching_era': round(away_pitching_era, 2),
            'home_pitching_sv': 0,  # Not available in boxscores
            'away_pitching_sv': 0,
            'home_pitching_cg': 0,  # Not available in boxscores
            'away_pitching_cg': 0,
            'home_pitching_sho': 0,  # Not available in boxscores
            'away_pitching_sho': 0,
            'home_pitching_qs': 0,  # Not available in boxscores
            'away_pitching_qs': 0,
            'home_pitching_ip': round(home_current['pitching_ip'], 1),
            'away_pitching_ip': round(away_current['pitching_ip'], 1),
            'home_pitching_h': home_current['pitching_h'],
            'away_pitching_h': away_current['pitching_h'],
            'home_pitching_er': home_current['pitching_er'],
            'away_pitching_er': away_current['pitching_er'],
            'home_pitching_hr': home_current['pitching_hr'],
            'away_pitching_hr': away_current['pitching_hr'],
            'home_pitching_bb': home_current['pitching_bb'],
            'away_pitching_bb': away_current['pitching_bb'],
            'home_pitching_k': home_current['pitching_k'],
            'away_pitching_k': away_current['pitching_k'],
            'home_pitching_oba': round(home_pitching_oba, 3),
            'away_pitching_oba': round(away_pitching_oba, 3),
            'home_pitching_whip': round(home_pitching_whip, 2),
            'away_pitching_whip': round(away_pitching_whip, 2),
            
            # Fielding stats
            'home_fielding_e': home_current['fielding_e'],
            'away_fielding_e': away_current['fielding_e'],
            'home_fielding_fp': 0.0,  # Not calculable without TC
            'away_fielding_fp': 0.0,
            'home_fielding_tc': 0,  # Not available in boxscores
            'away_fielding_tc': 0,
            'home_fielding_po': 0,  # Not available in boxscores
            'away_fielding_po': 0,
            'home_fielding_a': 0,  # Not available in boxscores
            'away_fielding_a': 0
        }
        
        stats_data.append(stats_row)
        
        # NOW update team stats with this game's results
        # Home team
        team_stats[home_abbr]['gp'] += 1
        team_stats[home_abbr]['batting_ab'] += int(game['home_batting_ab'])
        team_stats[home_abbr]['batting_r'] += int(game['home_batting_r'])
        team_stats[home_abbr]['batting_h'] += int(game['home_batting_h'])
        team_stats[home_abbr]['batting_2b'] += int(game['home_batting_2b'])
        team_stats[home_abbr]['batting_3b'] += int(game['home_batting_3b'])
        team_stats[home_abbr]['batting_hr'] += int(game['home_batting_hr'])
        team_stats[home_abbr]['batting_rbi'] += int(game['home_batting_rbi'])
        team_stats[home_abbr]['batting_tb'] += int(game['home_batting_tb'])
        team_stats[home_abbr]['batting_bb'] += int(game['home_batting_bb'])
        team_stats[home_abbr]['batting_so'] += int(game['home_batting_so'])
        team_stats[home_abbr]['batting_sb'] += int(game['home_batting_sb'])
        
        team_stats[home_abbr]['pitching_ip'] += float(game['home_pitching_ip'])
        team_stats[home_abbr]['pitching_h'] += int(game['home_pitching_h'])
        team_stats[home_abbr]['pitching_er'] += int(game['home_pitching_er'])
        team_stats[home_abbr]['pitching_hr'] += int(game['home_pitching_hr'])
        team_stats[home_abbr]['pitching_bb'] += int(game['home_pitching_bb'])
        team_stats[home_abbr]['pitching_k'] += int(game['home_pitching_k'])
        
        team_stats[home_abbr]['fielding_e'] += int(game['home_fielding_e'])
        
        # Away team
        team_stats[away_abbr]['gp'] += 1
        team_stats[away_abbr]['batting_ab'] += int(game['away_batting_ab'])
        team_stats[away_abbr]['batting_r'] += int(game['away_batting_r'])
        team_stats[away_abbr]['batting_h'] += int(game['away_batting_h'])
        team_stats[away_abbr]['batting_2b'] += int(game['away_batting_2b'])
        team_stats[away_abbr]['batting_3b'] += int(game['away_batting_3b'])
        team_stats[away_abbr]['batting_hr'] += int(game['away_batting_hr'])
        team_stats[away_abbr]['batting_rbi'] += int(game['away_batting_rbi'])
        team_stats[away_abbr]['batting_tb'] += int(game['away_batting_tb'])
        team_stats[away_abbr]['batting_bb'] += int(game['away_batting_bb'])
        team_stats[away_abbr]['batting_so'] += int(game['away_batting_so'])
        team_stats[away_abbr]['batting_sb'] += int(game['away_batting_sb'])
        
        team_stats[away_abbr]['pitching_ip'] += float(game['away_pitching_ip'])
        team_stats[away_abbr]['pitching_h'] += int(game['away_pitching_h'])
        team_stats[away_abbr]['pitching_er'] += int(game['away_pitching_er'])
        team_stats[away_abbr]['pitching_hr'] += int(game['away_pitching_hr'])
        team_stats[away_abbr]['pitching_bb'] += int(game['away_pitching_bb'])
        team_stats[away_abbr]['pitching_k'] += int(game['away_pitching_k'])
        
        team_stats[away_abbr]['fielding_e'] += int(game['away_fielding_e'])
        
        # Update W/L (pitching stats)
        home_runs = int(game['home_batting_r'])
        away_runs = int(game['away_batting_r'])
        
        if home_runs > away_runs:
            team_stats[home_abbr]['pitching_w'] += 1
            team_stats[away_abbr]['pitching_l'] += 1
        else:
            team_stats[home_abbr]['pitching_l'] += 1
            team_stats[away_abbr]['pitching_w'] += 1
    
    if verbose:
        print(f"  Processed {len(boxscores)}/{len(boxscores)} games... DONE")
        print()
    
    # Create DataFrame
    stats_df = pd.DataFrame(stats_data)
    
    # Save by date
    if verbose:
        print(f"Saving team stats files by date...")
    
    saved_files = 0
    for date_str, group in stats_df.groupby('date'):
        file_path = f'{output_dir}/team_season_stats_{date_str}.csv'
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
    print("SEASON-TO-DATE TEAM STATS COMPUTATION - HISTORICAL YEARS")
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
