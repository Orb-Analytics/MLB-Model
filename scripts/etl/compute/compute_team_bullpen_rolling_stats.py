"""
Compute rolling average derived stats for team bullpen performance.
This script calculates rolling 5-game and 10-game averages for various
bullpen statistics at the team level.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Input files
TEAM_BOXSCORES = '/workspaces/MLB-Model/data/mlb_data/team_boxscores_all.csv'
BULLPEN_BOXSCORES = '/workspaces/MLB-Model/data/mlb_data/team_bullpen_boxscores_all.csv'
OUTPUT_DIR = Path('/workspaces/MLB-Model/data/mlb_data/derived_stats/team_bullpen_derived_stats')

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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


def main():
    print("Loading data...")
    
    # Load team boxscores to get team IDs
    team_df = pd.read_csv(TEAM_BOXSCORES)
    team_mapping = team_df[['id', 'date', 'home_team_id', 'away_team_id']].copy()
    team_mapping.rename(columns={'id': 'game_pk'}, inplace=True)
    
    # Load bullpen boxscores
    bullpen_df = pd.read_csv(BULLPEN_BOXSCORES)
    
    # Merge to add team IDs
    merged_df = pd.merge(bullpen_df, team_mapping, on=['game_pk', 'date'], how='left')
    
    # Check for missing team IDs
    if merged_df['home_team_id'].isna().any():
        print(f"WARNING: {merged_df['home_team_id'].isna().sum()} rows missing home_team_id")
    
    print(f"Loaded {len(merged_df)} games")
    
    # Keep game_pk order for final output
    game_pk_df = merged_df[['game_pk']].copy()
    
    print("\nReshaping to long format...")
    long_df = reshape_to_long(merged_df)
    print(f"Long format: {len(long_df)} rows (team-game combinations)")
    
    print("\nComputing rolling average stats...")
    long_df = compute_bullpen_rolling_stats(long_df)
    
    print("\nReshaping back to wide format...")
    
    # ERA (rolling_5, rolling_10)
    wide_df = reshape_to_wide(long_df, game_pk_df)
    era_df = create_alternating_columns(wide_df, 'era', [5, 10])
    era_file = OUTPUT_DIR / 'bp_era_rolling.csv'
    era_df.to_csv(era_file, index=False)
    print(f"✓ {era_file.name}: {len(era_df)} rows, {len(era_df.columns)} columns")
    
    # WHIP (rolling_5, rolling_10)
    whip_df = create_alternating_columns(wide_df, 'whip', [5, 10])
    whip_file = OUTPUT_DIR / 'bp_whip_rolling.csv'
    whip_df.to_csv(whip_file, index=False)
    print(f"✓ {whip_file.name}: {len(whip_df)} rows, {len(whip_df.columns)} columns")
    
    # K/9 (rolling_5, rolling_10)
    k9_df = create_alternating_columns(wide_df, 'k_per_9', [5, 10])
    k9_file = OUTPUT_DIR / 'bp_k_per_9_rolling.csv'
    k9_df.to_csv(k9_file, index=False)
    print(f"✓ {k9_file.name}: {len(k9_df)} rows, {len(k9_df.columns)} columns")
    
    # K/BB ratio (rolling_5, rolling_10)
    kbb_df = create_alternating_columns(wide_df, 'k_bb_ratio', [5, 10])
    kbb_file = OUTPUT_DIR / 'bp_k_bb_ratio_rolling.csv'
    kbb_df.to_csv(kbb_file, index=False)
    print(f"✓ {kbb_file.name}: {len(kbb_df)} rows, {len(kbb_df.columns)} columns")
    
    # HR/9 (rolling_10 only)
    hr9_df = create_alternating_columns(wide_df, 'hr_per_9', [10])
    hr9_file = OUTPUT_DIR / 'bp_hr_per_9_rolling.csv'
    hr9_df.to_csv(hr9_file, index=False)
    print(f"✓ {hr9_file.name}: {len(hr9_df)} rows, {len(hr9_df.columns)} columns")
    
    # BB/9 (rolling_5 only)
    bb9_df = create_alternating_columns(wide_df, 'bb_per_9', [5])
    bb9_file = OUTPUT_DIR / 'bp_bb_per_9_rolling.csv'
    bb9_df.to_csv(bb9_file, index=False)
    print(f"✓ {bb9_file.name}: {len(bb9_df)} rows, {len(bb9_df.columns)} columns")
    
    print("\n✅ Team bullpen rolling stats computed successfully!")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Show sample statistics
    print("\n📊 Sample statistics (rolling_5):")
    print(f"ERA - Mean: {era_df['home_bp_era_rolling_5'].mean():.2f}, "
          f"Range: [{era_df['home_bp_era_rolling_5'].min():.2f}, {era_df['home_bp_era_rolling_5'].max():.2f}]")
    print(f"WHIP - Mean: {whip_df['home_bp_whip_rolling_5'].mean():.2f}, "
          f"Range: [{whip_df['home_bp_whip_rolling_5'].min():.2f}, {whip_df['home_bp_whip_rolling_5'].max():.2f}]")
    print(f"K/9 - Mean: {k9_df['home_bp_k_per_9_rolling_5'].mean():.2f}, "
          f"Range: [{k9_df['home_bp_k_per_9_rolling_5'].min():.2f}, {k9_df['home_bp_k_per_9_rolling_5'].max():.2f}]")
    
    # Check data availability
    print(f"\nData availability (non-null values):")
    print(f"ERA rolling_5: {era_df['home_bp_era_rolling_5'].notna().sum()} / {len(era_df)} "
          f"({era_df['home_bp_era_rolling_5'].notna().sum() / len(era_df) * 100:.1f}%)")


if __name__ == '__main__':
    main()
