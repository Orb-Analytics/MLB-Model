"""
Compute rolling average derived stats for team bullpen performance - HISTORICAL VERSION
This script processes historical years (2009-2024) and creates derived stats
for each year separately.

Usage:
    python compute_historical_team_bullpen_rolling_stats.py 2024
    python compute_historical_team_bullpen_rolling_stats.py 2009 2010 2011
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import glob


def safe_divide(numerator, denominator, fill_value=np.nan):
    """Safely divide two arrays, handling division by zero."""
    result = np.where(denominator != 0, numerator / denominator, fill_value)
    return result


def reshape_to_long(df):
    """
    Reshape wide format (home/away in same row) to long format
    (one row per team per game).
    
    Returns DataFrame with columns:
    - game_pk, date, team_id, is_home, ip, h, er, bb, k, hr
    """
    # Home teams
    home_df = df[['game_pk', 'date', 'home_team_id', 
                   'home_bullpen_ip', 'home_bullpen_hits', 
                   'home_bullpen_earned_runs', 'home_bullpen_walks',
                   'home_bullpen_strikeouts', 'home_bullpen_homeruns']].copy()
    home_df.columns = ['game_pk', 'date', 'team_id', 'ip', 'h', 'er', 'bb', 'k', 'hr']
    home_df['is_home'] = True
    
    # Away teams
    away_df = df[['game_pk', 'date', 'away_team_id',
                   'away_bullpen_ip', 'away_bullpen_hits',
                   'away_bullpen_earned_runs', 'away_bullpen_walks',
                   'away_bullpen_strikeouts', 'away_bullpen_homeruns']].copy()
    away_df.columns = ['game_pk', 'date', 'team_id', 'ip', 'h', 'er', 'bb', 'k', 'hr']
    away_df['is_home'] = False
    
    # Combine
    long_df = pd.concat([home_df, away_df], ignore_index=True)
    
    # Convert date to datetime
    long_df['date'] = pd.to_datetime(long_df['date'])
    
    # Sort by team_id then date (chronological for each team)
    long_df = long_df.sort_values(['team_id', 'date']).reset_index(drop=True)
    
    return long_df


def compute_bullpen_rolling_stats(df):
    """
    Compute rolling average stats for each team's bullpen.
    Uses shift(1) to only include previous games (no data leakage).
    """
    # Group by team
    grouped = df.groupby('team_id')
    
    # Compute rolling sums for rolling_5
    df['ip_sum_5'] = grouped['ip'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['er_sum_5'] = grouped['er'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['h_sum_5'] = grouped['h'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['bb_sum_5'] = grouped['bb'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['k_sum_5'] = grouped['k'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['hr_sum_5'] = grouped['hr'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    
    # Compute rolling sums for rolling_10
    df['ip_sum_10'] = grouped['ip'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['er_sum_10'] = grouped['er'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['h_sum_10'] = grouped['h'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['bb_sum_10'] = grouped['bb'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['k_sum_10'] = grouped['k'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['hr_sum_10'] = grouped['hr'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    
    # Calculate rate stats from rolling sums
    # ERA = (ER * 9) / IP
    df['bp_era_rolling_5'] = safe_divide(df['er_sum_5'] * 9, df['ip_sum_5'])
    df['bp_era_rolling_10'] = safe_divide(df['er_sum_10'] * 9, df['ip_sum_10'])
    
    # WHIP = (H + BB) / IP
    df['bp_whip_rolling_5'] = safe_divide(df['h_sum_5'] + df['bb_sum_5'], df['ip_sum_5'])
    df['bp_whip_rolling_10'] = safe_divide(df['h_sum_10'] + df['bb_sum_10'], df['ip_sum_10'])
    
    # K/9 = (K * 9) / IP
    df['bp_k_per_9_rolling_5'] = safe_divide(df['k_sum_5'] * 9, df['ip_sum_5'])
    df['bp_k_per_9_rolling_10'] = safe_divide(df['k_sum_10'] * 9, df['ip_sum_10'])
    
    # K/BB ratio = K / BB
    df['bp_k_bb_ratio_rolling_5'] = safe_divide(df['k_sum_5'], df['bb_sum_5'])
    df['bp_k_bb_ratio_rolling_10'] = safe_divide(df['k_sum_10'], df['bb_sum_10'])
    
    # HR/9 = (HR * 9) / IP
    df['bp_hr_per_9_rolling_10'] = safe_divide(df['hr_sum_10'] * 9, df['ip_sum_10'])
    
    # BB/9 = (BB * 9) / IP
    df['bp_bb_per_9_rolling_5'] = safe_divide(df['bb_sum_5'] * 9, df['ip_sum_5'])
    
    return df


def reshape_to_wide(long_df, game_pks):
    """
    Reshape long format back to wide format with home/away in same row.
    Maintains original game order from the input files.
    """
    # Split back into home and away
    home_df = long_df[long_df['is_home']].copy()
    away_df = long_df[~long_df['is_home']].copy()
    
    # Merge on game_pk
    wide_df = pd.merge(
        game_pks[['game_pk']],
        home_df[['game_pk'] + [col for col in home_df.columns if col.startswith('bp_')]],
        on='game_pk',
        how='left'
    )
    
    away_stats = away_df[['game_pk'] + [col for col in away_df.columns if col.startswith('bp_')]]
    wide_df = pd.merge(wide_df, away_stats, on='game_pk', how='left', suffixes=('_home', '_away'))
    
    return wide_df


def create_alternating_columns(df, stat_name, windows):
    """
    Create alternating home/away columns for a given stat.
    Pattern: home_stat, away_stat, home_stat, away_stat
    """
    columns = ['game_pk']
    
    for window in windows:
        home_col = f'bp_{stat_name}_rolling_{window}_home'
        away_col = f'bp_{stat_name}_rolling_{window}_away'
        
        if home_col in df.columns and away_col in df.columns:
            # Rename to final format
            df.rename(columns={
                home_col: f'home_bp_{stat_name}_rolling_{window}',
                away_col: f'away_bp_{stat_name}_rolling_{window}'
            }, inplace=True)
            
            columns.append(f'home_bp_{stat_name}_rolling_{window}')
            columns.append(f'away_bp_{stat_name}_rolling_{window}')
    
    return df[columns]


def process_year(year):
    """Process a single year and create derived stats."""
    print()
    print("="*80)
    print(f"COMPUTING TEAM BULLPEN ROLLING STATS FOR {year}")
    print("="*80)
    print()
    
    # Input directories
    bullpen_dir = Path(f"data/{year}_data/mlb_data/raw/team_bullpen_boxscores")
    boxscore_dir = Path(f"data/{year}_data/mlb_data/raw/boxscores")
    
    # Check if input directories exist
    if not bullpen_dir.exists():
        print(f"❌ Bullpen directory not found: {bullpen_dir}")
        return False
    
    if not boxscore_dir.exists():
        print(f"❌ Boxscore directory not found: {boxscore_dir}")
        return False
    
    # Load all bullpen boxscore files for this year
    print(f"Loading bullpen boxscores from {bullpen_dir}...")
    bullpen_files = sorted(glob.glob(str(bullpen_dir / "*.csv")))
    
    if not bullpen_files:
        print(f"❌ No bullpen files found in {bullpen_dir}")
        return False
    
    print(f"Found {len(bullpen_files)} bullpen boxscore files")
    
    # Load and concatenate all bullpen files
    bullpen_dfs = []
    for file in bullpen_files:
        try:
            df = pd.read_csv(file)
            bullpen_dfs.append(df)
        except Exception as e:
            print(f"⚠️  Warning: Could not load {file}: {e}")
    
    bullpen_df = pd.concat(bullpen_dfs, ignore_index=True)
    bullpen_df = bullpen_df.drop_duplicates(subset='game_pk', keep='first')
    print(f"Loaded {len(bullpen_df):,} bullpen game records")
    
    # Load team boxscores to get team IDs
    print(f"Loading team boxscores from {boxscore_dir}...")
    boxscore_files = sorted(glob.glob(str(boxscore_dir / "*.csv")))
    
    if not boxscore_files:
        print(f"❌ No boxscore files found in {boxscore_dir}")
        return False
    
    # Load and concatenate team boxscores (just need game_pk and team IDs)
    boxscore_dfs = []
    for file in boxscore_files:
        try:
            df = pd.read_csv(file, usecols=['game_pk', 'date', 'home_team_id', 'away_team_id'])
            boxscore_dfs.append(df)
        except Exception as e:
            print(f"⚠️  Warning: Could not load {file}: {e}")
    
    team_df = pd.concat(boxscore_dfs, ignore_index=True)
    team_df = team_df.drop_duplicates(subset='game_pk', keep='first')
    print(f"Loaded {len(team_df):,} team boxscores")
    print()
    
    # Merge bullpen data with team IDs
    print("Merging team IDs with bullpen data...")
    merged_df = pd.merge(bullpen_df, team_df, on=['game_pk', 'date'], how='left')
    
    # Check for missing team IDs
    missing_home = merged_df['home_team_id'].isna().sum()
    missing_away = merged_df['away_team_id'].isna().sum()
    if missing_home > 0 or missing_away > 0:
        print(f"⚠️  Warning: {missing_home} rows missing home_team_id, {missing_away} missing away_team_id")
    
    print(f"Merged data: {len(merged_df):,} games")
    print()
    
    # Keep game_pk order for final output
    game_pk_df = merged_df[['game_pk']].copy()
    
    print("Reshaping to long format...")
    long_df = reshape_to_long(merged_df)
    print(f"Long format: {len(long_df):,} team-game observations")
    print()
    
    print("Computing rolling average stats...")
    long_df = compute_bullpen_rolling_stats(long_df)
    print("✓ Rolling stats computed")
    print()
    
    print("Reshaping back to wide format...")
    wide_df = reshape_to_wide(long_df, game_pk_df)
    print()
    
    # Create output directory
    output_dir = Path(f"data/{year}_data/mlb_data/season_to_date_stats/team_bullpen_stats/derived_stats")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    print()
    
    # Save each stat to a separate file
    print("Creating CSV files...")
    print("-" * 40)
    
    # ERA (rolling_5, rolling_10)
    era_df = create_alternating_columns(wide_df.copy(), 'era', [5, 10])
    era_file = output_dir / 'bp_era_rolling.csv'
    era_df.to_csv(era_file, index=False)
    print(f"✓ bp_era_rolling.csv")
    print(f"    Rows: {len(era_df):,}, Columns: {len(era_df.columns)}")
    
    # WHIP (rolling_5, rolling_10)
    whip_df = create_alternating_columns(wide_df.copy(), 'whip', [5, 10])
    whip_file = output_dir / 'bp_whip_rolling.csv'
    whip_df.to_csv(whip_file, index=False)
    print(f"✓ bp_whip_rolling.csv")
    print(f"    Rows: {len(whip_df):,}, Columns: {len(whip_df.columns)}")
    
    # K/9 (rolling_5, rolling_10)
    k9_df = create_alternating_columns(wide_df.copy(), 'k_per_9', [5, 10])
    k9_file = output_dir / 'bp_k_per_9_rolling.csv'
    k9_df.to_csv(k9_file, index=False)
    print(f"✓ bp_k_per_9_rolling.csv")
    print(f"    Rows: {len(k9_df):,}, Columns: {len(k9_df.columns)}")
    
    # K/BB ratio (rolling_5, rolling_10)
    kbb_df = create_alternating_columns(wide_df.copy(), 'k_bb_ratio', [5, 10])
    kbb_file = output_dir / 'bp_k_bb_ratio_rolling.csv'
    kbb_df.to_csv(kbb_file, index=False)
    print(f"✓ bp_k_bb_ratio_rolling.csv")
    print(f"    Rows: {len(kbb_df):,}, Columns: {len(kbb_df.columns)}")
    
    # HR/9 (rolling_10 only)
    hr9_df = create_alternating_columns(wide_df.copy(), 'hr_per_9', [10])
    hr9_file = output_dir / 'bp_hr_per_9_rolling.csv'
    hr9_df.to_csv(hr9_file, index=False)
    print(f"✓ bp_hr_per_9_rolling.csv")
    print(f"    Rows: {len(hr9_df):,}, Columns: {len(hr9_df.columns)}")
    
    # BB/9 (rolling_5 only)
    bb9_df = create_alternating_columns(wide_df.copy(), 'bb_per_9', [5])
    bb9_file = output_dir / 'bp_bb_per_9_rolling.csv'
    bb9_df.to_csv(bb9_file, index=False)
    print(f"✓ bp_bb_per_9_rolling.csv")
    print(f"    Rows: {len(bb9_df):,}, Columns: {len(bb9_df.columns)}")
    
    print()
    print("="*80)
    print(f"✓ {year} ROLLING STATS COMPLETED")
    print("="*80)
    print(f"Files created: 6")
    print(f"Output location: {output_dir}")
    
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python compute_historical_team_bullpen_rolling_stats.py YEAR [YEAR2 YEAR3 ...]")
        print("Example: python compute_historical_team_bullpen_rolling_stats.py 2024")
        print("Example: python compute_historical_team_bullpen_rolling_stats.py 2009 2010 2011")
        sys.exit(1)
    
    years = sys.argv[1:]
    
    print("="*80)
    print("TEAM BULLPEN ROLLING STATS - HISTORICAL YEARS")
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
