"""
Compute rolling average derived stats for starting pitcher performance - HISTORICAL VERSION
This script processes historical years (2009-2024) and creates derived stats
for each year separately.

Usage:
    python compute_historical_starting_pitcher_rolling_stats.py 2024
    python compute_historical_starting_pitcher_rolling_stats.py 2009 2010 2011
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import glob

def safe_divide(numerator, denominator, default=0.0):
    """Safely divide, returning default when denominator is 0."""
    if denominator == 0 or pd.isna(denominator):
        return default
    return numerator / denominator

def compute_pitcher_rolling_stats(df):
    """
    Compute rolling average stats for each starting pitcher.
    Returns df with rolling stats added.
    """
    # Create a copy
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    # Sort by pitcher and date
    df = df.sort_values(['pitcher_id', 'date']).reset_index(drop=True)
    
    # Group by pitcher
    grouped = df.groupby('pitcher_id')
    
    # For rate stats (ERA, WHIP, K/9, etc.), we need to sum counting stats over the rolling window
    # then calculate the rate from those sums
    
    # Rolling sums of counting stats (shifted to use only previous games)
    df['ip_sum_5'] = grouped['ip'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['ip_sum_10'] = grouped['ip'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    
    df['er_sum_5'] = grouped['earned_runs'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['er_sum_10'] = grouped['earned_runs'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    
    df['h_sum_5'] = grouped['hits'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['h_sum_10'] = grouped['hits'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    
    df['bb_sum_5'] = grouped['walks'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['bb_sum_10'] = grouped['walks'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    
    df['k_sum_5'] = grouped['strikeouts'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['k_sum_10'] = grouped['strikeouts'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    
    df['hr_sum_10'] = grouped['homeruns'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    
    # Now calculate rate stats from the sums
    # ERA rolling averages
    df['era_rolling_5'] = df.apply(lambda row: safe_divide(row['er_sum_5'] * 9, row['ip_sum_5']), axis=1)
    df['era_rolling_10'] = df.apply(lambda row: safe_divide(row['er_sum_10'] * 9, row['ip_sum_10']), axis=1)
    
    # WHIP rolling averages
    df['whip_rolling_5'] = df.apply(lambda row: safe_divide(row['h_sum_5'] + row['bb_sum_5'], row['ip_sum_5']), axis=1)
    df['whip_rolling_10'] = df.apply(lambda row: safe_divide(row['h_sum_10'] + row['bb_sum_10'], row['ip_sum_10']), axis=1)
    
    # K/9 rolling averages
    df['k_per_9_rolling_5'] = df.apply(lambda row: safe_divide(row['k_sum_5'] * 9, row['ip_sum_5']), axis=1)
    df['k_per_9_rolling_10'] = df.apply(lambda row: safe_divide(row['k_sum_10'] * 9, row['ip_sum_10']), axis=1)
    
    # K/BB ratio rolling averages
    df['k_bb_ratio_rolling_5'] = df.apply(lambda row: safe_divide(row['k_sum_5'], row['bb_sum_5']), axis=1)
    df['k_bb_ratio_rolling_10'] = df.apply(lambda row: safe_divide(row['k_sum_10'], row['bb_sum_10']), axis=1)
    
    # IP per GS rolling average (rolling 5 only)
    df['ip_per_gs_rolling_5'] = grouped['ip'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
    
    # HR/9 rolling average (rolling 10 only)
    df['hr_per_9_rolling_10'] = df.apply(lambda row: safe_divide(row['hr_sum_10'] * 9, row['ip_sum_10']), axis=1)
    
    # BB/9 rolling average (rolling 5 only)
    df['bb_per_9_rolling_5'] = df.apply(lambda row: safe_divide(row['bb_sum_5'] * 9, row['ip_sum_5']), axis=1)
    
    return df

def reshape_to_long(df):
    """
    Reshape from wide format (home/away in same row) to long format (one row per pitcher).
    """
    # Home pitchers
    home = df[['game_pk', 'date', 'home_starter_id', 'home_starter_name', 'home_starter_team',
               'home_starter_ip', 'home_starter_hits', 'home_starter_earned_runs',
               'home_starter_walks', 'home_starter_strikeouts', 'home_starter_homeruns']].copy()
    
    home.columns = ['game_pk', 'date', 'pitcher_id', 'pitcher_name', 'team',
                    'ip', 'hits', 'earned_runs', 'walks', 'strikeouts', 'homeruns']
    home['location'] = 'home'
    
    # Away pitchers
    away = df[['game_pk', 'date', 'away_starter_id', 'away_starter_name', 'away_starter_team',
               'away_starter_ip', 'away_starter_hits', 'away_starter_earned_runs',
               'away_starter_walks', 'away_starter_strikeouts', 'away_starter_homeruns']].copy()
    
    away.columns = ['game_pk', 'date', 'pitcher_id', 'pitcher_name', 'team',
                    'ip', 'hits', 'earned_runs', 'walks', 'strikeouts', 'homeruns']
    away['location'] = 'away'
    
    # Combine
    long_df = pd.concat([home, away], ignore_index=True)
    long_df['date'] = pd.to_datetime(long_df['date'])
    
    return long_df

def reshape_to_wide(long_df, stat_name):
    """
    Reshape from long format back to wide format with alternating home/away columns.
    """
    # Separate home and away
    home = long_df[long_df['location'] == 'home'].copy()
    away = long_df[long_df['location'] == 'away'].copy()
    
    # Select relevant columns
    home_cols = ['game_pk', 'date', stat_name]
    away_cols = ['game_pk', stat_name]
    
    home_subset = home[home_cols].copy()
    away_subset = away[away_cols].copy()
    
    # Rename columns
    home_subset.columns = ['game_pk', 'date', f'home_{stat_name}']
    away_subset.columns = ['game_pk', f'away_{stat_name}']
    
    # Merge
    wide_df = home_subset.merge(away_subset, on='game_pk', how='inner')
    
    return wide_df

def process_year(year):
    """Process a single year and create derived stats."""
    print()
    print("="*80)
    print(f"COMPUTING STARTING PITCHER ROLLING STATS FOR {year}")
    print("="*80)
    print()
    
    # Input directory
    input_dir = Path(f"data/{year}_data/mlb_data/raw/starting_pitcher_boxscores")
    
    # Check if input directory exists
    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        return False
    
    # Load all boxscore files for this year
    print(f"Loading starting pitcher boxscores from {input_dir}...")
    boxscore_files = sorted(glob.glob(str(input_dir / "*.csv")))
    
    if not boxscore_files:
        print(f"❌ No boxscore files found in {input_dir}")
        return False
    
    print(f"Found {len(boxscore_files)} boxscore files")
    
    # Load and concatenate all files
    dfs = []
    for file in boxscore_files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
        except Exception as e:
            print(f"⚠️  Warning: Could not load {file}: {e}")
    
    df = pd.concat(dfs, ignore_index=True)
    df = df.drop_duplicates(subset='game_pk', keep='first')
    print(f"Loaded {len(df):,} games")
    print()
    
    # Reshape to long format
    print("Reshaping to long format...")
    long_df = reshape_to_long(df)
    print(f"Reshaped to {len(long_df):,} pitcher-game observations")
    print()
    
    # Compute rolling stats
    print("Computing rolling average stats for each pitcher...")
    long_df = compute_pitcher_rolling_stats(long_df)
    print("✓ Rolling stats computed")
    print()
    
    # Create output directory
    output_dir = Path(f"data/{year}_data/mlb_data/season_to_date_stats/starting_pitcher_stats/derived_stats")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    print()
    
    # Define stat groups to save
    stat_groups = {
        'era_rolling': ['era_rolling_5', 'era_rolling_10'],
        'whip_rolling': ['whip_rolling_5', 'whip_rolling_10'],
        'k_per_9_rolling': ['k_per_9_rolling_5', 'k_per_9_rolling_10'],
        'k_bb_ratio_rolling': ['k_bb_ratio_rolling_5', 'k_bb_ratio_rolling_10'],
        'ip_per_gs_rolling': ['ip_per_gs_rolling_5'],
        'hr_per_9_rolling': ['hr_per_9_rolling_10'],
        'bb_per_9_rolling': ['bb_per_9_rolling_5']
    }
    
    # Create CSV for each stat group
    print("Creating CSV files...")
    print("-" * 40)
    
    for stat_group_name, stat_columns in stat_groups.items():
        # Reshape each stat to wide format
        wide_dfs = []
        for stat_col in stat_columns:
            wide = reshape_to_wide(long_df, stat_col)
            if len(wide_dfs) == 0:
                wide_dfs.append(wide)
            else:
                # Merge with previous (keep game_pk and date from first)
                wide_dfs.append(wide.drop(columns=['date']))
        
        # Merge all stats in this group
        result = wide_dfs[0]
        for i in range(1, len(wide_dfs)):
            result = result.merge(wide_dfs[i], on='game_pk', how='inner')
        
        # Reorder columns to alternate home/away
        cols = ['game_pk', 'date']
        for stat_col in stat_columns:
            cols.append(f'home_{stat_col}')
            cols.append(f'away_{stat_col}')
        
        result = result[cols]
        
        # Sort by date and game_pk
        result = result.sort_values(['date', 'game_pk']).reset_index(drop=True)
        
        # Save to CSV
        output_file = output_dir / f"{stat_group_name}.csv"
        result.to_csv(output_file, index=False)
        
        print(f"✓ {stat_group_name}.csv")
        print(f"    Rows: {len(result):,}")
        print(f"    Columns: {len(result.columns)}")
    
    print()
    print("="*80)
    print(f"✓ {year} ROLLING STATS COMPLETED")
    print("="*80)
    print(f"Files created: {len(stat_groups)}")
    print(f"Output location: {output_dir}")
    
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python compute_historical_starting_pitcher_rolling_stats.py YEAR [YEAR2 YEAR3 ...]")
        print("Example: python compute_historical_starting_pitcher_rolling_stats.py 2024")
        print("Example: python compute_historical_starting_pitcher_rolling_stats.py 2009 2010 2011")
        sys.exit(1)
    
    years = sys.argv[1:]
    
    print("="*80)
    print("STARTING PITCHER ROLLING STATS - HISTORICAL YEARS")
    print("="*80)
    print()
    print(f"Years to process: {', '.join(years)}")
    
    success_count = 0
    failed_years = []
    
    for year in years:
        success = process_year(year)
        if success:
            success_count += 1
        else:
            failed_years.append(year)
    
    # Final summary
    print()
    print("="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"Total years processed: {len(years)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(failed_years)}")
    
    if failed_years:
        print(f"Failed years: {', '.join(failed_years)}")
    
    print("="*80)

if __name__ == "__main__":
    main()
