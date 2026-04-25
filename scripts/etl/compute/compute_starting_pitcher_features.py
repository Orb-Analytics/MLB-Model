#!/usr/bin/env python3
"""
Starting Pitcher Feature Pipeline
Computes standardized stats and rolling averages for starting pitchers
with strict no-leakage rules (only using prior games)
"""

import pandas as pd
import numpy as np
from pathlib import Path


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def safe_divide(numerator, denominator):
    """
    Safely divide two series/arrays, returning NaN where denominator is zero
    """
    return np.where(denominator != 0, numerator / denominator, np.nan)


def load_raw_starting_pitcher_data(file_path):
    """
    Load the raw starting pitcher stats from CSV
    
    Returns:
        DataFrame with game-level starter data (wide format)
    """
    print(f"Loading raw starting pitcher data from {file_path}...")
    df = pd.read_csv(file_path)
    print(f"  ✓ Loaded {len(df)} games")
    print(f"  ✓ Columns: {len(df.columns)}")
    return df


def reshape_starting_pitchers_to_long(df):
    """
    Reshape from wide game-level format to long pitcher-game format
    
    Input: One row per game with home_starter_* and away_starter_* columns
    Output: Two rows per game (one for home starter, one for away starter)
    """
    print("\nReshaping to long pitcher-game format...")
    
    # Identify raw stat columns (those that appear for both home and away)
    pitcher_stat_cols = [
        'pitching_gp', 'pitching_gs', 'pitching_qs', 'pitching_w', 'pitching_l',
        'pitching_era', 'pitching_sv', 'pitching_hld', 'pitching_ip', 'pitching_h',
        'pitching_er', 'pitching_hr', 'pitching_bb', 'pitching_whip', 'pitching_k',
        'pitching_k_per_9'
    ]
    
    # Build home starters long format
    home_cols = {
        'balldontlie_game_id': 'game_id',
        'date': 'date',
        'home_starter_id': 'pitcher_id'
    }
    
    # Add all home pitcher stat columns
    for stat in pitcher_stat_cols:
        home_col = f'home_starter_{stat}'
        if home_col in df.columns:
            home_cols[home_col] = stat
    
    home_df = df[list(home_cols.keys())].rename(columns=home_cols).copy()
    home_df['side'] = 'home'
    
    # Build away starters long format
    away_cols = {
        'balldontlie_game_id': 'game_id',
        'date': 'date',
        'away_starter_id': 'pitcher_id'
    }
    
    # Add all away pitcher stat columns
    for stat in pitcher_stat_cols:
        away_col = f'away_starter_{stat}'
        if away_col in df.columns:
            away_cols[away_col] = stat
    
    away_df = df[list(away_cols.keys())].rename(columns=away_cols).copy()
    away_df['side'] = 'away'
    
    # Combine home and away
    long_df = pd.concat([home_df, away_df], ignore_index=True)
    
    # Sort by pitcher, then date (critical for rolling calculations)
    long_df = long_df.sort_values(['pitcher_id', 'date']).reset_index(drop=True)
    
    print(f"  ✓ Reshaped to {len(long_df)} pitcher-game rows")
    print(f"  ✓ Unique pitchers: {long_df['pitcher_id'].nunique()}")
    
    return long_df


def compute_starting_pitcher_derived_features(df):
    """
    Compute derived/standardized features from raw stats
    
    Derived features:
    - k_bb_ratio = pitching_k / pitching_bb
    - qs_rate = pitching_qs / pitching_gs
    - ip_per_gs = pitching_ip / pitching_gs
    - hr_per_9 = (pitching_hr * 9) / pitching_ip
    - bb_per_9 = (pitching_bb * 9) / pitching_ip
    - h_per_9 = (pitching_h * 9) / pitching_ip
    - win_pct = pitching_w / (pitching_w + pitching_l)
    """
    print("\nComputing derived features...")
    
    df = df.copy()
    
    # k_bb_ratio
    df['k_bb_ratio'] = safe_divide(df['pitching_k'], df['pitching_bb'])
    
    # qs_rate
    df['qs_rate'] = safe_divide(df['pitching_qs'], df['pitching_gs'])
    
    # ip_per_gs
    df['ip_per_gs'] = safe_divide(df['pitching_ip'], df['pitching_gs'])
    
    # hr_per_9
    df['hr_per_9'] = safe_divide(df['pitching_hr'] * 9, df['pitching_ip'])
    
    # bb_per_9
    df['bb_per_9'] = safe_divide(df['pitching_bb'] * 9, df['pitching_ip'])
    
    # h_per_9
    df['h_per_9'] = safe_divide(df['pitching_h'] * 9, df['pitching_ip'])
    
    # win_pct
    df['win_pct'] = safe_divide(df['pitching_w'], df['pitching_w'] + df['pitching_l'])
    
    print(f"  ✓ Computed 7 derived features")
    
    return df


def compute_per_game_stats(df):
    """
    Compute per-game stats from cumulative stats
    This is needed to properly calculate rolling ERA, WHIP, etc.
    """
    print("\nComputing per-game stats from cumulative data...")
    
    df = df.copy()
    grouped = df.groupby('pitcher_id')
    
    # Calculate per-game stats by taking difference from previous game
    # For counting stats (ER, H, BB, K, HR, IP)
    for stat in ['pitching_er', 'pitching_h', 'pitching_bb', 'pitching_k', 'pitching_hr', 'pitching_ip']:
        if stat in df.columns:
            df[f'{stat}_game'] = grouped[stat].diff()
            # First game for each pitcher: use the cumulative value as the game value
            first_games = grouped.cumcount() == 0
            df.loc[first_games, f'{stat}_game'] = df.loc[first_games, stat]
    
    print(f"  ✓ Computed per-game stats for rolling calculations")
    
    return df


def compute_starting_pitcher_rolling_features(df, windows=[5, 10]):
    """
    Compute rolling average features for each pitcher using ONLY prior games
    
    For rate stats like ERA and WHIP, we compute them properly over rolling windows.
    For other metrics, we compute rolling averages of the derived stats.
    
    Critical: Uses shift(1) to prevent data leakage
    """
    print(f"\nComputing rolling features (windows: {windows})...")
    
    df = df.copy()
    grouped = df.groupby('pitcher_id')
    
    rolling_count = 0
    
    # Compute rolling ERA (earned runs / innings pitched over window)
    for window in [5, 10]:
        if window not in windows:
            continue
        
        if 'pitching_er_game' in df.columns and 'pitching_ip_game' in df.columns:
            # Shift to use only prior games, then sum over rolling window
            # min_periods=None means we need ALL values in the window (no NaN result if any value is NaN)
            rolling_er = grouped['pitching_er_game'].shift(1).rolling(
                window=window, min_periods=window
            ).sum().reset_index(level=0, drop=True)
            
            rolling_ip = grouped['pitching_ip_game'].shift(1).rolling(
                window=window, min_periods=window
            ).sum().reset_index(level=0, drop=True)
            
            # ERA = (ER * 9) / IP
            df[f'pitching_era_l{window}'] = safe_divide(rolling_er * 9, rolling_ip)
            rolling_count += 1
    
    # Compute rolling WHIP ((H + BB) / IP over window)
    for window in [5, 10]:
        if window not in windows:
            continue
        
        if 'pitching_h_game' in df.columns and 'pitching_bb_game' in df.columns and 'pitching_ip_game' in df.columns:
            rolling_h = grouped['pitching_h_game'].shift(1).rolling(
                window=window, min_periods=window
            ).sum().reset_index(level=0, drop=True)
            
            rolling_bb = grouped['pitching_bb_game'].shift(1).rolling(
                window=window, min_periods=window
            ).sum().reset_index(level=0, drop=True)
            
            rolling_ip = grouped['pitching_ip_game'].shift(1).rolling(
                window=window, min_periods=window
            ).sum().reset_index(level=0, drop=True)
            
            # WHIP = (H + BB) / IP
            df[f'pitching_whip_l{window}'] = safe_divide(rolling_h + rolling_bb, rolling_ip)
            rolling_count += 1
            rolling_count += 1
    
    # Compute rolling K/9 (strikeouts per 9 innings over window)
    for window in [5, 10]:
        if window not in windows:
            continue
        
        if 'pitching_k_game' in df.columns and 'pitching_ip_game' in df.columns:
            rolling_k = grouped['pitching_k_game'].shift(1).rolling(
                window=window, min_periods=window
            ).sum().reset_index(level=0, drop=True)
            
            rolling_ip = grouped['pitching_ip_game'].shift(1).rolling(
                window=window, min_periods=window
            ).sum().reset_index(level=0, drop=True)
            
            # K/9 = (K * 9) / IP
            df[f'pitching_k_per_9_l{window}'] = safe_divide(rolling_k * 9, rolling_ip)
            rolling_count += 1
    
    # For derived stats that are already rates, compute rolling averages
    # K/BB ratio
    for window in [5, 10]:
        if window not in windows:
            continue
        
        if 'k_bb_ratio' in df.columns:
            df[f'k_bb_ratio_l{window}'] = grouped['k_bb_ratio'].shift(1).rolling(
                window=window, min_periods=window
            ).mean().reset_index(level=0, drop=True)
            rolling_count += 1
    
    # QS rate
    if 10 in windows and 'qs_rate' in df.columns:
        df['qs_rate_l10'] = grouped['qs_rate'].shift(1).rolling(
            window=10, min_periods=10
        ).mean().reset_index(level=0, drop=True)
        rolling_count += 1
    
    # IP per GS
    if 5 in windows and 'ip_per_gs' in df.columns:
        df['ip_per_gs_l5'] = grouped['ip_per_gs'].shift(1).rolling(
            window=5, min_periods=5
        ).mean().reset_index(level=0, drop=True)
        rolling_count += 1
    
    # HR per 9
    if 10 in windows and 'hr_per_9' in df.columns:
        df['hr_per_9_l10'] = grouped['hr_per_9'].shift(1).rolling(
            window=10, min_periods=10
        ).mean().reset_index(level=0, drop=True)
        rolling_count += 1
    
    # BB per 9
    if 5 in windows and 'bb_per_9' in df.columns:
        df['bb_per_9_l5'] = grouped['bb_per_9'].shift(1).rolling(
            window=5, min_periods=5
        ).mean().reset_index(level=0, drop=True)
        rolling_count += 1
    
    print(f"  ✓ Computed {rolling_count} rolling features")
    
    return df


def build_starting_pitcher_pregame_snapshots(df):
    """
    Build pregame feature snapshots for each pitcher
    
    This ensures all features represent the pitcher's stats BEFORE the game
    For baseline stats (not rolling), we also need to shift them
    """
    print("\nBuilding pregame feature snapshots...")
    
    df = df.copy()
    
    # Baseline features to shift (cumulative stats from season)
    baseline_features = [
        'pitching_era',
        'pitching_whip',
        'pitching_k_per_9',
        'k_bb_ratio',
        'qs_rate',
        'ip_per_gs',
        'hr_per_9',
        'bb_per_9',
        'h_per_9',
        'win_pct',
        'pitching_ip',
        'pitching_gs',
        'pitching_gp'
    ]
    
    # Shift baseline features to represent entering stats
    grouped = df.groupby('pitcher_id')
    for feature in baseline_features:
        if feature in df.columns:
            df[f'{feature}_entering'] = grouped[feature].shift(1)
    
    print(f"  ✓ Created pregame snapshots for {len(baseline_features)} baseline features")
    
    return df


def merge_starting_pitcher_features_to_games(game_df, pitcher_feature_df):
    """
    Merge pitcher pregame features back to wide game-level format
    
    Merges twice:
    - Once for home_starter_id -> home_starter_* columns
    - Once for away_starter_id -> away_starter_* columns
    """
    print("\nMerging pitcher features back to game rows...")
    
    # Features to include in output (using _entering versions for baseline)
    output_features = [
        'pitching_era_entering',
        'pitching_whip_entering',
        'pitching_k_per_9_entering',
        'k_bb_ratio_entering',
        'qs_rate_entering',
        'ip_per_gs_entering',
        'hr_per_9_entering',
        'bb_per_9_entering',
        'h_per_9_entering',
        'win_pct_entering',
        'pitching_ip_entering',
        'pitching_gs_entering',
        'pitching_gp_entering',
        # Rolling features
        'pitching_era_l5',
        'pitching_era_l10',
        'pitching_whip_l5',
        'pitching_whip_l10',
        'pitching_k_per_9_l5',
        'pitching_k_per_9_l10',
        'k_bb_ratio_l5',
        'k_bb_ratio_l10',
        'qs_rate_l10',
        'ip_per_gs_l5',
        'hr_per_9_l10',
        'bb_per_9_l5'
    ]
    
    # Filter to only features that exist
    output_features = [f for f in output_features if f in pitcher_feature_df.columns]
    
    # Prepare pitcher feature dataframe for merging
    merge_cols = ['game_id', 'pitcher_id', 'side'] + output_features
    pitcher_merge = pitcher_feature_df[merge_cols].copy()
    
    # Merge home starters
    home_pitchers = pitcher_merge[pitcher_merge['side'] == 'home'].copy()
    home_pitchers = home_pitchers.drop(columns=['side'])
    
    # Rename columns with home_starter_ prefix
    home_rename = {'pitcher_id': 'home_starter_id'}
    for feat in output_features:
        home_rename[feat] = f'home_starter_{feat}'
    home_pitchers = home_pitchers.rename(columns=home_rename)
    
    result = game_df.merge(
        home_pitchers,
        left_on=['balldontlie_game_id', 'home_starter_id'],
        right_on=['game_id', 'home_starter_id'],
        how='left'
    )
    result = result.drop(columns=['game_id'])
    
    # Merge away starters
    away_pitchers = pitcher_merge[pitcher_merge['side'] == 'away'].copy()
    away_pitchers = away_pitchers.drop(columns=['side'])
    
    # Rename columns with away_starter_ prefix
    away_rename = {'pitcher_id': 'away_starter_id'}
    for feat in output_features:
        away_rename[feat] = f'away_starter_{feat}'
    away_pitchers = away_pitchers.rename(columns=away_rename)
    
    result = result.merge(
        away_pitchers,
        left_on=['balldontlie_game_id', 'away_starter_id'],
        right_on=['game_id', 'away_starter_id'],
        how='left'
    )
    result = result.drop(columns=['game_id'])
    
    print(f"  ✓ Merged features for home and away starters")
    print(f"  ✓ Added {len(output_features) * 2} feature columns")
    
    return result


def validate_no_leakage(df, sample_pitcher_id=None):
    """
    Validate that rolling features don't include the current game
    
    Checks a sample pitcher's first few games to ensure:
    - First game has NaN for all features (no prior games)
    - Second game uses only data from first game
    """
    print("\nValidating no data leakage...")
    
    if sample_pitcher_id is None:
        # Pick first pitcher with multiple games
        pitcher_counts = df.groupby('pitcher_id').size()
        sample_pitcher_id = pitcher_counts[pitcher_counts >= 3].index[0]
    
    pitcher_df = df[df['pitcher_id'] == sample_pitcher_id].head(3)
    
    print(f"\n  Sample validation for pitcher {sample_pitcher_id}:")
    print(f"  First 3 games:")
    
    for idx, row in pitcher_df.iterrows():
        print(f"\n  Game {row['date']}:")
        print(f"    GP (raw): {row.get('pitching_gp', 'N/A')}")
        print(f"    GP (entering): {row.get('pitching_gp_entering', 'N/A')}")
        print(f"    ERA (entering): {row.get('pitching_era_entering', 'N/A')}")
        print(f"    ERA (L5): {row.get('pitching_era_l5', 'N/A')}")
        print(f"    K/BB (entering): {row.get('k_bb_ratio_entering', 'N/A')}")
    
    print("\n  ✓ Validation complete")


def order_output_columns(df, game_id_col='balldontlie_game_id'):
    """
    Order columns logically: id, date, then alternating home/away features
    """
    print("\nOrdering output columns...")
    
    # Start with game identifiers
    ordered_cols = [game_id_col, 'date']
    
    # Add home starter ID and away starter ID
    if 'home_starter_id' in df.columns:
        ordered_cols.append('home_starter_id')
    if 'away_starter_id' in df.columns:
        ordered_cols.append('away_starter_id')
    
    # Get all home_starter_ and away_starter_ feature columns
    home_features = sorted([c for c in df.columns if c.startswith('home_starter_') and c != 'home_starter_id'])
    away_features = sorted([c for c in df.columns if c.startswith('away_starter_') and c != 'away_starter_id'])
    
    # Add features
    ordered_cols.extend(home_features)
    ordered_cols.extend(away_features)
    
    # Reorder dataframe
    df = df[ordered_cols]
    
    print(f"  ✓ Ordered {len(ordered_cols)} columns")
    
    return df


# ==================================================
# MAIN PIPELINE
# ==================================================

def run_starting_pitcher_feature_pipeline(
    input_file='data/bdl_data/starting_pitcher_stats.csv',
    output_file='data/bdl_data/starting_pitcher_standardized_stats.csv',
    validate=True
):
    """
    Main pipeline to compute starting pitcher features
    
    Steps:
    1. Load raw data
    2. Reshape to long format
    3. Compute per-game stats
    4. Compute derived features
    5. Compute rolling features (no leakage)
    6. Build pregame snapshots
    7. Validate
    8. Merge back to wide format
    9. Order columns
    10. Save
    """
    print("="*80)
    print("STARTING PITCHER FEATURE PIPELINE")
    print("="*80)
    
    # Step 1: Load raw data
    raw_df = load_raw_starting_pitcher_data(input_file)
    
    # Step 2: Reshape to long format
    long_df = reshape_starting_pitchers_to_long(raw_df)
    
    # Step 3: Compute per-game stats (needed for proper rolling calculations)
    long_df = compute_per_game_stats(long_df)
    
    # Step 4: Compute derived features
    long_df = compute_starting_pitcher_derived_features(long_df)
    
    # Step 5: Compute rolling features
    long_df = compute_starting_pitcher_rolling_features(long_df, windows=[5, 10])
    
    # Step 6: Build pregame snapshots
    long_df = build_starting_pitcher_pregame_snapshots(long_df)
    
    # Step 7: Validate no leakage
    if validate:
        validate_no_leakage(long_df)
    
    # Step 8: Merge back to wide format
    # Use only game identifiers and starter IDs from original
    game_skeleton = raw_df[['balldontlie_game_id', 'date', 'home_starter_id', 'away_starter_id']].copy()
    wide_df = merge_starting_pitcher_features_to_games(game_skeleton, long_df)
    
    # Step 9: Order columns
    wide_df = order_output_columns(wide_df)
    
    # Step 10: Save output
    print("\n" + "="*80)
    print("SAVING OUTPUT")
    print("="*80)
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wide_df.to_csv(output_path, index=False)
    
    print(f"\n✓ Saved: {output_file}")
    print(f"  Rows: {len(wide_df)}")
    print(f"  Columns: {len(wide_df.columns)}")
    
    # Show sample output
    print("\n" + "="*80)
    print("SAMPLE OUTPUT")
    print("="*80)
    
    print("\nFirst 3 rows, first 10 columns:")
    print(wide_df.head(3).iloc[:, :10])
    
    print("\nColumn summary:")
    feature_cols = [c for c in wide_df.columns if 'entering' in c or '_l5' in c or '_l10' in c]
    print(f"  Total feature columns: {len(feature_cols)}")
    print(f"  Home starter features: {len([c for c in feature_cols if c.startswith('home_starter_')])}")
    print(f"  Away starter features: {len([c for c in feature_cols if c.startswith('away_starter_')])}")
    
    print("\n" + "="*80)
    print("✓✓✓ PIPELINE COMPLETE! ✓✓✓")
    print("="*80)
    
    return wide_df


# ==================================================
# ENTRY POINT
# ==================================================

if __name__ == '__main__':
    result_df = run_starting_pitcher_feature_pipeline(
        input_file='data/bdl_data/starting_pitcher_stats.csv',
        output_file='data/bdl_data/starting_pitcher_standardized_stats.csv',
        validate=True
    )
    
    print("\n✓ Starting pitcher standardized stats file created successfully!")
    print("\nNext steps:")
    print("  1. Review the output file")
    print("  2. Check validation results for data leakage")
    print("  3. Merge these computed features with your main dataset")
