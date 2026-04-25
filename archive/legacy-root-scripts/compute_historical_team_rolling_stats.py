"""
Compute rolling average derived stats for team performance - HISTORICAL VERSION
This script processes historical years (2009-2024) and creates derived stats
for batting, pitching, and fielding for each year separately.

Usage:
    python compute_historical_team_rolling_stats.py 2024
    python compute_historical_team_rolling_stats.py 2009 2010 2011
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
    """
    # Select batting, pitching, and fielding columns for home
    batting_cols = [col for col in df.columns if col.startswith('home_batting_')]
    pitching_cols = [col for col in df.columns if col.startswith('home_pitching_')]
    fielding_cols = [col for col in df.columns if col.startswith('home_fielding_')]
    
    # Home teams
    home_df = df[['game_pk', 'date', 'home_team_id'] + batting_cols + pitching_cols + fielding_cols].copy()
    # Rename columns to remove home_ prefix
    home_df.columns = ['game_pk', 'date', 'team_id'] + \
                      [col.replace('home_', '') for col in batting_cols] + \
                      [col.replace('home_', '') for col in pitching_cols] + \
                      [col.replace('home_', '') for col in fielding_cols]
    home_df['is_home'] = True
    
    # Select batting, pitching, and fielding columns for away
    batting_cols_away = [col for col in df.columns if col.startswith('away_batting_')]
    pitching_cols_away = [col for col in df.columns if col.startswith('away_pitching_')]
    fielding_cols_away = [col for col in df.columns if col.startswith('away_fielding_')]
    
    # Away teams
    away_df = df[['game_pk', 'date', 'away_team_id'] + batting_cols_away + pitching_cols_away + fielding_cols_away].copy()
    # Rename columns to remove away_ prefix
    away_df.columns = ['game_pk', 'date', 'team_id'] + \
                      [col.replace('away_', '') for col in batting_cols_away] + \
                      [col.replace('away_', '') for col in pitching_cols_away] + \
                      [col.replace('away_', '') for col in fielding_cols_away]
    away_df['is_home'] = False
    
    # Combine
    long_df = pd.concat([home_df, away_df], ignore_index=True)
    
    # Convert date to datetime
    long_df['date'] = pd.to_datetime(long_df['date'])
    
    # Sort by team_id then date (chronological for each team)
    long_df = long_df.sort_values(['team_id', 'date']).reset_index(drop=True)
    
    return long_df


def compute_team_rolling_stats(df):
    """
    Compute rolling average stats for each team.
    Uses shift(1) to only include previous games (no data leakage).
    """
    # Group by team
    grouped = df.groupby('team_id')
    
    # ========== BATTING STATS ==========
    
    # Batting: Rolling sums for rolling_5
    df['ab_sum_5'] = grouped['batting_ab'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['h_sum_5'] = grouped['batting_h'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['bb_sum_5'] = grouped['batting_bb'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['tb_sum_5'] = grouped['batting_tb'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['r_sum_5'] = grouped['batting_r'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['hr_sum_5'] = grouped['batting_hr'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['so_sum_5'] = grouped['batting_so'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    
    # Batting: Rolling sums for rolling_10
    df['ab_sum_10'] = grouped['batting_ab'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['h_sum_10'] = grouped['batting_h'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['bb_sum_10'] = grouped['batting_bb'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['tb_sum_10'] = grouped['batting_tb'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['r_sum_10'] = grouped['batting_r'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['so_sum_10'] = grouped['batting_so'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    
    # Calculate batting rate stats from rolling sums
    # AVG = H / AB
    df['batting_avg_rolling_10'] = safe_divide(df['h_sum_10'], df['ab_sum_10'])
    
    # OBP = (H + BB) / (AB + BB)  [simplified - ignoring HBP and SF]
    df['batting_obp_rolling_5'] = safe_divide(df['h_sum_5'] + df['bb_sum_5'], df['ab_sum_5'] + df['bb_sum_5'])
    df['batting_obp_rolling_10'] = safe_divide(df['h_sum_10'] + df['bb_sum_10'], df['ab_sum_10'] + df['bb_sum_10'])
    
    # SLG = TB / AB
    df['batting_slg_rolling_5'] = safe_divide(df['tb_sum_5'], df['ab_sum_5'])
    
    # OPS = OBP + SLG
    df['batting_ops_rolling_5'] = df['batting_obp_rolling_5'] + df['batting_slg_rolling_5']
    # For rolling_10 OPS, we need OBP_10 + SLG_10
    df['batting_slg_rolling_10'] = safe_divide(df['tb_sum_10'], df['ab_sum_10'])
    df['batting_ops_rolling_10'] = df['batting_obp_rolling_10'] + df['batting_slg_rolling_10']
    
    # Derived per-game stats (use rolling mean since they're per-game)
    # R per game
    df['batting_r_per_g_rolling_5'] = grouped['batting_r'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
    df['batting_r_per_g_rolling_10'] = grouped['batting_r'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())
    
    # HR per game
    df['batting_hr_per_g_rolling_5'] = grouped['batting_hr'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
    
    # BB per game
    df['batting_bb_per_g_rolling_10'] = grouped['batting_bb'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())
    
    # K% = SO / AB
    df['batting_k_pct_rolling_10'] = safe_divide(df['so_sum_10'], df['ab_sum_10'])
    
    # ========== PITCHING STATS ==========
    
    # Pitching: Rolling sums for rolling_5
    df['ip_sum_5'] = grouped['pitching_ip'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['er_sum_5'] = grouped['pitching_er'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['pitching_h_sum_5'] = grouped['pitching_h'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['pitching_bb_sum_5'] = grouped['pitching_bb'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['pitching_k_sum_5'] = grouped['pitching_k'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    
    # Pitching: Rolling sums for rolling_10
    df['ip_sum_10'] = grouped['pitching_ip'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['er_sum_10'] = grouped['pitching_er'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['pitching_h_sum_10'] = grouped['pitching_h'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['pitching_bb_sum_10'] = grouped['pitching_bb'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['pitching_k_sum_10'] = grouped['pitching_k'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['pitching_hr_sum_10'] = grouped['pitching_hr'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    
    # Calculate pitching rate stats from rolling sums
    # ERA = (ER * 9) / IP
    df['pitching_era_rolling_5'] = safe_divide(df['er_sum_5'] * 9, df['ip_sum_5'])
    df['pitching_era_rolling_10'] = safe_divide(df['er_sum_10'] * 9, df['ip_sum_10'])
    
    # WHIP = (H + BB) / IP
    df['pitching_whip_rolling_5'] = safe_divide(df['pitching_h_sum_5'] + df['pitching_bb_sum_5'], df['ip_sum_5'])
    df['pitching_whip_rolling_10'] = safe_divide(df['pitching_h_sum_10'] + df['pitching_bb_sum_10'], df['ip_sum_10'])
    
    # K/BB ratio = K / BB
    df['pitching_k_bb_ratio_rolling_10'] = safe_divide(df['pitching_k_sum_10'], df['pitching_bb_sum_10'])
    
    # HR/9 = (HR * 9) / IP
    df['pitching_hr_per_9_rolling_10'] = safe_divide(df['pitching_hr_sum_10'] * 9, df['ip_sum_10'])
    
    # Quality Start Rate: A quality start is IP >= 6 and ER <= 3
    # Note: This is for team pitching (approximation)
    df['qs'] = ((df['pitching_ip'] >= 6) & (df['pitching_er'] <= 3)).astype(int)
    df['qs_sum_10'] = grouped['qs'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['games_count_10'] = grouped['qs'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).count())
    df['pitching_qs_rate_rolling_10'] = safe_divide(df['qs_sum_10'], df['games_count_10'])
    
    # ========== FIELDING STATS ==========
    
    # Errors per game
    df['fielding_e_per_g_rolling_10'] = grouped['fielding_e'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())
    
    return df


def reshape_to_wide(long_df, game_pks):
    """
    Reshape long format back to wide format with home/away in same row.
    Maintains original game order from the input files.
    """
    # Split back into home and away
    home_df = long_df[long_df['is_home']].copy()
    away_df = long_df[~long_df['is_home']].copy()
    
    # Get stat columns (those starting with batting_, pitching_, or fielding_)
    stat_cols = [col for col in home_df.columns if 
                 col.startswith('batting_') or 
                 col.startswith('pitching_') or 
                 col.startswith('fielding_')]
    
    # Merge on game_pk
    wide_df = pd.merge(
        game_pks[['game_pk']],
        home_df[['game_pk'] + stat_cols],
        on='game_pk',
        how='left'
    )
    
    away_stats = away_df[['game_pk'] + stat_cols]
    wide_df = pd.merge(wide_df, away_stats, on='game_pk', how='left', suffixes=('_home', '_away'))
    
    return wide_df


def create_alternating_columns(df, stat_name, windows):
    """
    Create alternating home/away columns for a given stat.
    Pattern: home_stat, away_stat, home_stat, away_stat
    """
    columns = ['game_pk']
    
    for window in windows:
        home_col = f'{stat_name}_rolling_{window}_home'
        away_col = f'{stat_name}_rolling_{window}_away'
        
        if home_col in df.columns and away_col in df.columns:
            # Rename to final format
            df.rename(columns={
                home_col: f'home_{stat_name}_rolling_{window}',
                away_col: f'away_{stat_name}_rolling_{window}'
            }, inplace=True)
            
            columns.append(f'home_{stat_name}_rolling_{window}')
            columns.append(f'away_{stat_name}_rolling_{window}')
    
    return df[columns]


def process_year(year):
    """Process a single year and create derived stats."""
    print()
    print("="*80)
    print(f"COMPUTING TEAM ROLLING STATS FOR {year}")
    print("="*80)
    print()
    
    # Input directory
    boxscore_dir = Path(f"data/{year}_data/mlb_data/raw/boxscores")
    
    # Check if input directory exists
    if not boxscore_dir.exists():
        print(f"❌ Boxscore directory not found: {boxscore_dir}")
        return False
    
    # Load all boxscore files for this year
    print(f"Loading boxscores from {boxscore_dir}...")
    boxscore_files = sorted(glob.glob(str(boxscore_dir / "*.csv")))
    
    if not boxscore_files:
        print(f"❌ No boxscore files found in {boxscore_dir}")
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
    
    team_df = pd.concat(dfs, ignore_index=True)
    # Remove duplicate game_pk entries (e.g. suspended games appearing under multiple dates)
    team_df = team_df.drop_duplicates(subset='game_pk', keep='first')
    print(f"Loaded {len(team_df):,} games")
    print()
    
    # Keep game_pk order for final output
    game_pk_df = team_df[['game_pk']].copy()
    
    print("Reshaping to long format...")
    long_df = reshape_to_long(team_df)
    print(f"Long format: {len(long_df):,} team-game observations")
    print()
    
    print("Computing rolling average stats...")
    long_df = compute_team_rolling_stats(long_df)
    print("✓ Rolling stats computed")
    print()
    
    print("Reshaping back to wide format...")
    wide_df = reshape_to_wide(long_df, game_pk_df)
    print()
    
    # Create output directory
    output_dir = Path(f"data/{year}_data/mlb_data/season_to_date_stats/team_stats/derived_stats")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    print()
    
    # Save each stat to a separate file
    print("Creating CSV files...")
    print("-" * 40)
    
    # ========== SAVE BATTING STATS ==========
    
    # batting_ops (rolling_5, rolling_10)
    ops_df = create_alternating_columns(wide_df.copy(), 'batting_ops', [5, 10])
    ops_file = output_dir / 'batting_ops_rolling.csv'
    ops_df.to_csv(ops_file, index=False)
    print(f"✓ batting_ops_rolling.csv")
    print(f"    Rows: {len(ops_df):,}, Columns: {len(ops_df.columns)}")
    
    # batting_r_per_g (rolling_5, rolling_10)
    r_per_g_df = create_alternating_columns(wide_df.copy(), 'batting_r_per_g', [5, 10])
    r_per_g_file = output_dir / 'batting_r_per_g_rolling.csv'
    r_per_g_df.to_csv(r_per_g_file, index=False)
    print(f"✓ batting_r_per_g_rolling.csv")
    print(f"    Rows: {len(r_per_g_df):,}, Columns: {len(r_per_g_df.columns)}")
    
    # batting_avg (rolling_10)
    avg_df = create_alternating_columns(wide_df.copy(), 'batting_avg', [10])
    avg_file = output_dir / 'batting_avg_rolling.csv'
    avg_df.to_csv(avg_file, index=False)
    print(f"✓ batting_avg_rolling.csv")
    print(f"    Rows: {len(avg_df):,}, Columns: {len(avg_df.columns)}")
    
    # batting_obp (rolling_5, rolling_10)
    obp_df = create_alternating_columns(wide_df.copy(), 'batting_obp', [5, 10])
    obp_file = output_dir / 'batting_obp_rolling.csv'
    obp_df.to_csv(obp_file, index=False)
    print(f"✓ batting_obp_rolling.csv")
    print(f"    Rows: {len(obp_df):,}, Columns: {len(obp_df.columns)}")
    
    # batting_slg (rolling_5)
    slg_df = create_alternating_columns(wide_df.copy(), 'batting_slg', [5])
    slg_file = output_dir / 'batting_slg_rolling.csv'
    slg_df.to_csv(slg_file, index=False)
    print(f"✓ batting_slg_rolling.csv")
    print(f"    Rows: {len(slg_df):,}, Columns: {len(slg_df.columns)}")
    
    # batting_hr_per_g (rolling_5)
    hr_per_g_df = create_alternating_columns(wide_df.copy(), 'batting_hr_per_g', [5])
    hr_per_g_file = output_dir / 'batting_hr_per_g_rolling.csv'
    hr_per_g_df.to_csv(hr_per_g_file, index=False)
    print(f"✓ batting_hr_per_g_rolling.csv")
    print(f"    Rows: {len(hr_per_g_df):,}, Columns: {len(hr_per_g_df.columns)}")
    
    # batting_k_pct (rolling_10)
    k_pct_df = create_alternating_columns(wide_df.copy(), 'batting_k_pct', [10])
    k_pct_file = output_dir / 'batting_k_pct_rolling.csv'
    k_pct_df.to_csv(k_pct_file, index=False)
    print(f"✓ batting_k_pct_rolling.csv")
    print(f"    Rows: {len(k_pct_df):,}, Columns: {len(k_pct_df.columns)}")
    
    # batting_bb_per_g (rolling_10)
    bb_per_g_df = create_alternating_columns(wide_df.copy(), 'batting_bb_per_g', [10])
    bb_per_g_file = output_dir / 'batting_bb_per_g_rolling.csv'
    bb_per_g_df.to_csv(bb_per_g_file, index=False)
    print(f"✓ batting_bb_per_g_rolling.csv")
    print(f"    Rows: {len(bb_per_g_df):,}, Columns: {len(bb_per_g_df.columns)}")
    
    # ========== SAVE PITCHING STATS ==========
    
    # pitching_era (rolling_5, rolling_10)
    era_df = create_alternating_columns(wide_df.copy(), 'pitching_era', [5, 10])
    era_file = output_dir / 'pitching_era_rolling.csv'
    era_df.to_csv(era_file, index=False)
    print(f"✓ pitching_era_rolling.csv")
    print(f"    Rows: {len(era_df):,}, Columns: {len(era_df.columns)}")
    
    # pitching_whip (rolling_5, rolling_10)
    whip_df = create_alternating_columns(wide_df.copy(), 'pitching_whip', [5, 10])
    whip_file = output_dir / 'pitching_whip_rolling.csv'
    whip_df.to_csv(whip_file, index=False)
    print(f"✓ pitching_whip_rolling.csv")
    print(f"    Rows: {len(whip_df):,}, Columns: {len(whip_df.columns)}")
    
    # pitching_k_bb_ratio (rolling_10)
    k_bb_df = create_alternating_columns(wide_df.copy(), 'pitching_k_bb_ratio', [10])
    k_bb_file = output_dir / 'pitching_k_bb_ratio_rolling.csv'
    k_bb_df.to_csv(k_bb_file, index=False)
    print(f"✓ pitching_k_bb_ratio_rolling.csv")
    print(f"    Rows: {len(k_bb_df):,}, Columns: {len(k_bb_df.columns)}")
    
    # pitching_hr_per_9 (rolling_10)
    hr9_df = create_alternating_columns(wide_df.copy(), 'pitching_hr_per_9', [10])
    hr9_file = output_dir / 'pitching_hr_per_9_rolling.csv'
    hr9_df.to_csv(hr9_file, index=False)
    print(f"✓ pitching_hr_per_9_rolling.csv")
    print(f"    Rows: {len(hr9_df):,}, Columns: {len(hr9_df.columns)}")
    
    # pitching_qs_rate (rolling_10)
    qs_df = create_alternating_columns(wide_df.copy(), 'pitching_qs_rate', [10])
    qs_file = output_dir / 'pitching_qs_rate_rolling.csv'
    qs_df.to_csv(qs_file, index=False)
    print(f"✓ pitching_qs_rate_rolling.csv")
    print(f"    Rows: {len(qs_df):,}, Columns: {len(qs_df.columns)}")
    
    # ========== SAVE FIELDING STATS ==========
    
    # fielding_e_per_g (rolling_10)
    e_per_g_df = create_alternating_columns(wide_df.copy(), 'fielding_e_per_g', [10])
    e_per_g_file = output_dir / 'fielding_e_per_g_rolling.csv'
    e_per_g_df.to_csv(e_per_g_file, index=False)
    print(f"✓ fielding_e_per_g_rolling.csv")
    print(f"    Rows: {len(e_per_g_df):,}, Columns: {len(e_per_g_df.columns)}")
    
    print()
    print("="*80)
    print(f"✓ {year} ROLLING STATS COMPLETED")
    print("="*80)
    print(f"Files created: 14")
    print(f"Output location: {output_dir}")
    
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python compute_historical_team_rolling_stats.py YEAR [YEAR2 YEAR3 ...]")
        print("Example: python compute_historical_team_rolling_stats.py 2024")
        print("Example: python compute_historical_team_rolling_stats.py 2009 2010 2011")
        sys.exit(1)
    
    years = sys.argv[1:]
    
    print("="*80)
    print("TEAM ROLLING STATS - HISTORICAL YEARS")
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
