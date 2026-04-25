"""
Team Season Feature Pipeline
Computes standardized team features and rolling averages from raw team season stats.
Ensures no data leakage by using only prior games for all entering/rolling features.
"""

import pandas as pd
import numpy as np
from typing import List, Dict


def safe_divide(numerator: pd.Series, denominator: pd.Series, default: float = 0.0) -> pd.Series:
    """
    Safely divide two series, returning default value when denominator is zero or NaN.
    """
    return np.where(
        (denominator == 0) | (denominator.isna()) | (numerator.isna()),
        default,
        numerator / denominator
    )


def load_raw_team_data(filepath: str = 'data/bdl_data/team_season_stats.csv') -> pd.DataFrame:
    """
    Load raw team season stats file.
    
    Returns:
        DataFrame with game rows containing home_* and away_* team columns
    """
    df = pd.read_csv(filepath)
    print(f"Loaded raw team data: {len(df)} games")
    return df


def reshape_teams_to_long(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reshape wide game-level data into long team-history format.
    Each game produces 2 rows: one for home team, one for away team.
    
    Returns:
        DataFrame with one row per team per game, sorted by team_id and date
    """
    
    # Define the raw stat columns to extract (these exist in home_* and away_* format)
    stat_columns = [
        'gp',
        'batting_ab', 'batting_r', 'batting_h', 'batting_2b', 'batting_3b',
        'batting_hr', 'batting_rbi', 'batting_tb', 'batting_bb', 'batting_so',
        'batting_sb', 'batting_avg', 'batting_obp', 'batting_slg', 'batting_ops',
        'pitching_w', 'pitching_l', 'pitching_era', 'pitching_sv', 'pitching_cg',
        'pitching_sho', 'pitching_qs', 'pitching_ip', 'pitching_h', 'pitching_er',
        'pitching_hr', 'pitching_bb', 'pitching_k', 'pitching_oba', 'pitching_whip',
        'fielding_e', 'fielding_fp', 'fielding_tc', 'fielding_po', 'fielding_a'
    ]
    
    # Build home team rows
    home_rows = df[['balldontlie_game_id', 'date', 'home_team_id']].copy()
    home_rows['team_id'] = home_rows['home_team_id']
    home_rows['side'] = 'home'
    
    for col in stat_columns:
        if f'home_{col}' in df.columns:
            home_rows[col] = df[f'home_{col}']
    
    # Build away team rows
    away_rows = df[['balldontlie_game_id', 'date', 'away_team_id']].copy()
    away_rows['team_id'] = away_rows['away_team_id']
    away_rows['side'] = 'away'
    
    for col in stat_columns:
        if f'away_{col}' in df.columns:
            away_rows[col] = df[f'away_{col}']
    
    # Combine and sort
    long_df = pd.concat([home_rows, away_rows], ignore_index=True)
    long_df = long_df.sort_values(['team_id', 'date']).reset_index(drop=True)
    
    print(f"Reshaped to long format: {len(long_df)} team-game rows")
    print(f"Unique teams: {long_df['team_id'].nunique()}")
    
    return long_df


def compute_per_game_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute per-game stats from cumulative season stats.
    Critical for proper rolling calculations.
    
    For each team, compute the difference between consecutive games.
    First game uses cumulative value as the game value.
    """
    df = df.copy()
    
    # Stats that accumulate (need diff)
    cumulative_cols = [
        'batting_r', 'batting_h', 'batting_hr', 'batting_bb', 
        'batting_so', 'batting_sb', 'batting_ab',
        'pitching_h', 'pitching_er', 'pitching_hr', 
        'pitching_bb', 'pitching_k', 'pitching_ip',
        'fielding_e'
    ]
    
    grouped = df.groupby('team_id')
    
    for col in cumulative_cols:
        if col in df.columns:
            # Compute per-game value as diff from previous game
            df[f'{col}_game'] = grouped[col].diff()
            # First game per team: use cumulative as game value
            first_game_mask = grouped.cumcount() == 0
            df.loc[first_game_mask, f'{col}_game'] = df.loc[first_game_mask, col]
    
    print("Computed per-game stats from cumulative season stats")
    return df


def compute_team_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute derived/standardized team features from raw stats.
    
    Features computed:
    - batting_r_per_g = batting_r / gp
    - batting_hr_per_g = batting_hr / gp
    - batting_k_pct = batting_so / batting_ab
    - batting_bb_per_g = batting_bb / gp
    - batting_sb_per_g = batting_sb / gp
    - pitching_k_per_9 = (pitching_k * 9) / pitching_ip
    - pitching_k_bb_ratio = pitching_k / pitching_bb
    - pitching_hr_per_9 = (pitching_hr * 9) / pitching_ip
    - pitching_bb_per_9 = (pitching_bb * 9) / pitching_ip
    - pitching_qs_rate = pitching_qs / gp
    - fielding_e_per_g = fielding_e / gp
    """
    df = df.copy()
    
    # Batting derived features
    df['batting_r_per_g'] = safe_divide(df['batting_r'], df['gp'])
    df['batting_hr_per_g'] = safe_divide(df['batting_hr'], df['gp'])
    df['batting_k_pct'] = safe_divide(df['batting_so'], df['batting_ab'])
    df['batting_bb_per_g'] = safe_divide(df['batting_bb'], df['gp'])
    df['batting_sb_per_g'] = safe_divide(df['batting_sb'], df['gp'])
    
    # Pitching derived features
    df['pitching_k_per_9'] = safe_divide(df['pitching_k'] * 9, df['pitching_ip'])
    df['pitching_k_bb_ratio'] = safe_divide(df['pitching_k'], df['pitching_bb'])
    df['pitching_hr_per_9'] = safe_divide(df['pitching_hr'] * 9, df['pitching_ip'])
    df['pitching_bb_per_9'] = safe_divide(df['pitching_bb'] * 9, df['pitching_ip'])
    df['pitching_qs_rate'] = safe_divide(df['pitching_qs'], df['gp'])
    
    # Fielding derived features
    df['fielding_e_per_g'] = safe_divide(df['fielding_e'], df['gp'])
    
    print("Computed derived team features")
    return df


def compute_team_rolling_features(df: pd.DataFrame, windows: List[int] = [5, 10]) -> pd.DataFrame:
    """
    Compute rolling average features using ONLY prior games (no leakage).
    
    Uses shift(1) before rolling to ensure current game is never included.
    Uses min_periods=window to require full window (no partial windows).
    
    Rolling features:
    - L5: batting_ops, batting_r_per_g, batting_obp, batting_slg, batting_hr_per_g, 
          pitching_era, pitching_whip
    - L10: batting_ops, batting_r_per_g, batting_obp, batting_avg, batting_k_pct, 
           batting_bb_per_g, pitching_era, pitching_whip, pitching_k_bb_ratio, 
           pitching_hr_per_9, pitching_qs_rate, fielding_e_per_g
    """
    df = df.copy()
    
    # Define which features get which rolling windows
    rolling_config = {
        # Both L5 and L10
        'batting_ops': [5, 10],
        'batting_r_per_g': [5, 10],
        'batting_obp': [5, 10],
        'pitching_era': [5, 10],
        'pitching_whip': [5, 10],
        
        # L5 only
        'batting_slg': [5],
        'batting_hr_per_g': [5],
        
        # L10 only
        'batting_avg': [10],
        'batting_k_pct': [10],
        'batting_bb_per_g': [10],
        'pitching_k_bb_ratio': [10],
        'pitching_hr_per_9': [10],
        'pitching_qs_rate': [10],
        'fielding_e_per_g': [10],
    }
    
    grouped = df.groupby('team_id')
    
    for feature, feature_windows in rolling_config.items():
        if feature not in df.columns:
            print(f"Warning: {feature} not found, skipping rolling calculation")
            continue
        
        for window in feature_windows:
            if window not in windows:
                continue
            
            col_name = f'{feature}_l{window}'
            
            # Shift then roll to prevent leakage
            df[col_name] = (
                grouped[feature]
                .shift(1)
                .rolling(window=window, min_periods=window)
                .mean()
            )
    
    print(f"Computed rolling features for windows: {windows}")
    return df


def build_team_pregame_snapshots(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build pregame feature snapshots by renaming baseline stats to *_entering.
    
    NOTE: The raw team season data already contains ENTERING stats 
    (GP represents games played BEFORE this game), so we DON'T shift.
    We simply rename the columns to be explicit about this.
    
    Rolling features are ALREADY shifted in compute_team_rolling_features(),
    so they don't need additional shifting here.
    """
    df = df.copy()
    
    # Baseline features to rename (these are already entering stats from raw data)
    baseline_features = [
        'batting_avg', 'batting_obp', 'batting_slg', 'batting_ops',
        'batting_r_per_g', 'batting_hr_per_g', 'batting_k_pct', 
        'batting_bb_per_g', 'batting_sb_per_g',
        'pitching_era', 'pitching_oba', 'pitching_whip',
        'pitching_k_per_9', 'pitching_k_bb_ratio', 'pitching_hr_per_9',
        'pitching_bb_per_9', 'pitching_qs_rate',
        'fielding_fp', 'fielding_e_per_g',
        'gp', 'pitching_ip'
    ]
    
    # Simply rename to make it explicit these are entering stats
    # NO SHIFTING needed because raw data is already entering stats
    for feature in baseline_features:
        if feature in df.columns:
            df[f'{feature}_entering'] = df[feature]
    
    print("Built team pregame feature snapshots (renamed entering stats)")
    return df


def merge_team_features_to_games(game_df: pd.DataFrame, team_feature_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge computed team features back to the wide game-level format.
    
    Merges twice:
    1. For home team features (prefix: home_)
    2. For away team features (prefix: away_)
    
    Returns:
        DataFrame with original game structure plus computed team features
    """
    
    # Select only the features we want to merge (not intermediate calculations)
    feature_cols = [col for col in team_feature_df.columns if 
                   col.endswith('_entering') or col.endswith('_l5') or col.endswith('_l10')]
    
    merge_cols = ['balldontlie_game_id', 'team_id'] + feature_cols
    
    # Prepare home team features
    home_features = team_feature_df[team_feature_df['side'] == 'home'][merge_cols].copy()
    home_features = home_features.rename(columns={'team_id': 'home_team_id'})
    home_features = home_features.rename(columns={
        col: f'home_{col}' for col in feature_cols
    })
    
    # Remove any duplicates (shouldn't exist but just in case)
    home_features = home_features.drop_duplicates(subset=['balldontlie_game_id'])
    
    # Prepare away team features
    away_features = team_feature_df[team_feature_df['side'] == 'away'][merge_cols].copy()
    away_features = away_features.rename(columns={'team_id': 'away_team_id'})
    away_features = away_features.rename(columns={
        col: f'away_{col}' for col in feature_cols
    })
    
    # Remove any duplicates (shouldn't exist but just in case)
    away_features = away_features.drop_duplicates(subset=['balldontlie_game_id'])
    
    # Merge with original game data
    result = game_df[['balldontlie_game_id', 'date']].copy()
    result = result.merge(home_features, on='balldontlie_game_id', how='left')
    result = result.merge(away_features, on='balldontlie_game_id', how='left')
    
    print(f"Merged team features back to game rows: {len(result)} rows, {len(result.columns)} columns")
    
    return result


def validate_no_leakage(df: pd.DataFrame, sample_team_id: int = None) -> None:
    """
    Validate that first games show NaN/0 (no leakage) and later games have values.
    """
    print("\n" + "="*80)
    print("VALIDATION: Checking for data leakage")
    print("="*80)
    
    # Check a sample team's progression
    if sample_team_id is None:
        sample_team_id = df['home_team_id'].iloc[10]
    
    team_games = df[
        (df['home_team_id'] == sample_team_id) | 
        (df['away_team_id'] == sample_team_id)
    ].sort_values('date').head(10)
    
    print(f"\nSample Team {sample_team_id} - First 10 Games:")
    print("\nDate       | Home ERA (ent) | Home ERA L5 | Away ERA (ent) | Away ERA L5")
    print("-" * 75)
    
    for idx, row in team_games.iterrows():
        if pd.notna(row.get('home_batting_ops_entering')):
            print(f"{row['date']} | {row.get('home_pitching_era_entering', 0):.2f} | "
                  f"{row.get('home_pitching_era_l5', 0):.2f} | "
                  f"{row.get('away_pitching_era_entering', 0):.2f} | "
                  f"{row.get('away_pitching_era_l5', 0):.2f}")
    
    # Check for NaN counts
    entering_cols = [col for col in df.columns if '_entering' in col]
    rolling_cols = [col for col in df.columns if '_l5' in col or '_l10' in col]
    
    if entering_cols:
        null_count_entering = df[entering_cols[0]].isna().sum()
        print(f"\nFirst entering feature ({entering_cols[0]}): {null_count_entering}/{len(df)} null values")
    
    if rolling_cols:
        null_count_rolling = df[rolling_cols[0]].isna().sum()
        print(f"First L5 feature ({rolling_cols[0]}): {null_count_rolling}/{len(df)} null values")
    
    print("\n✓ Validation complete - check that early games have null values")


def order_output_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Order columns for readability: identifiers first, then alternating home/away features.
    """
    # Start with identifiers
    ordered_cols = ['balldontlie_game_id', 'date']
    
    # Get all feature names (without home_/away_ prefix)
    all_cols = [col for col in df.columns if col not in ordered_cols]
    home_cols = [col for col in all_cols if col.startswith('home_')]
    away_cols = [col for col in all_cols if col.startswith('away_')]
    
    # Extract feature names
    feature_names = sorted(set([col.replace('home_', '') for col in home_cols]))
    
    # Alternate home and away for each feature
    for feature in feature_names:
        home_col = f'home_{feature}'
        away_col = f'away_{feature}'
        if home_col in df.columns:
            ordered_cols.append(home_col)
        if away_col in df.columns:
            ordered_cols.append(away_col)
    
    return df[ordered_cols]


def main():
    """
    Main pipeline for computing team season features.
    """
    print("="*80)
    print("TEAM SEASON FEATURE PIPELINE")
    print("="*80)
    
    # Step 1: Load raw data
    print("\nSTEP 1: Loading raw team data...")
    raw_df = load_raw_team_data()
    
    # Step 2: Reshape to long format
    print("\nSTEP 2: Reshaping to long team-history format...")
    long_df = reshape_teams_to_long(raw_df)
    
    # Step 3: Compute per-game stats
    print("\nSTEP 3: Computing per-game stats from cumulative data...")
    long_df = compute_per_game_stats(long_df)
    
    # Step 4: Compute derived features
    print("\nSTEP 4: Computing derived team features...")
    long_df = compute_team_derived_features(long_df)
    
    # Step 5: Compute rolling features
    print("\nSTEP 5: Computing rolling features (L5, L10)...")
    long_df = compute_team_rolling_features(long_df, windows=[5, 10])
    
    # Step 6: Build pregame snapshots
    print("\nSTEP 6: Building team pregame feature snapshots...")
    long_df = build_team_pregame_snapshots(long_df)
    
    # Step 7: Merge back to game rows
    print("\nSTEP 7: Merging features back to wide game format...")
    output_df = merge_team_features_to_games(raw_df, long_df)
    
    # Step 8: Order columns and save
    print("\nSTEP 8: Ordering columns and saving output...")
    output_df = order_output_columns(output_df)
    
    output_path = 'data/bdl_data/team_season_standardized_stats.csv'
    output_df.to_csv(output_path, index=False)
    
    print(f"\n✓ Saved: {output_path}")
    print(f"  Rows: {len(output_df)}")
    print(f"  Columns: {len(output_df.columns)}")
    
    # Validation
    validate_no_leakage(output_df)
    
    # Show sample output
    print("\n" + "="*80)
    print("SAMPLE OUTPUT")
    print("="*80)
    print("\nFirst 5 rows (showing key features):")
    sample_cols = ['balldontlie_game_id', 'date', 
                   'home_batting_ops_entering', 'home_batting_ops_l5',
                   'home_pitching_era_entering', 'home_pitching_era_l5',
                   'away_batting_ops_entering', 'away_pitching_era_l5']
    display_cols = [col for col in sample_cols if col in output_df.columns]
    print(output_df[display_cols].head())
    
    print("\n" + "="*80)
    print("✓ PIPELINE COMPLETE")
    print("="*80)


if __name__ == '__main__':
    main()
