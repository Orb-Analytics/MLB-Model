#!/usr/bin/env python3
"""
Compute rolling average statistics for team performance metrics
Rolling averages are calculated per team across their game history
"""

import pandas as pd
import numpy as np
from datetime import datetime

print("="*80)
print("COMPUTING ROLLING AVERAGE STATISTICS")
print("="*80)

# Load the dataset
df = pd.read_csv('data/bdl_data/2025_bdl_dataset.csv')
print(f"\nLoaded dataset: {len(df)} rows × {len(df.columns)} columns")

# Convert date to datetime for proper sorting
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

# Define which metrics need rolling averages
rolling_metrics = {
    # BOTH (rolling_5 and rolling_10)
    'batting_ops': ['rolling_5', 'rolling_10'],
    'batting_r_per_g': ['rolling_5', 'rolling_10'],
    'batting_obp': ['rolling_5', 'rolling_10'],
    'pitching_era': ['rolling_5', 'rolling_10'],
    'pitching_whip': ['rolling_5', 'rolling_10'],
    
    # ROLLING_10 only
    'batting_avg': ['rolling_10'],
    'batting_k_pct': ['rolling_10'],
    'batting_bb_per_g': ['rolling_10'],
    'pitching_k_bb_ratio': ['rolling_10'],
    'pitching_hr_per_9': ['rolling_10'],
    'pitching_qs_rate': ['rolling_10'],
    'fielding_e_per_g': ['rolling_10'],
    
    # ROLLING_5 only
    'batting_slg': ['rolling_5'],
    'batting_hr_per_g': ['rolling_5'],
}

print("\n" + "="*80)
print("COMPUTING ROLLING AVERAGES")
print("="*80)

def compute_team_rolling_stats(team_df, windows, metrics_config):
    """
    Compute rolling averages for a single team's games
    Uses expanding window for early games where history < window size
    """
    team_df = team_df.sort_values('date').copy()
    
    for metric, window_list in metrics_config.items():
        if metric not in team_df.columns:
            continue
            
        for window_name in window_list:
            window_size = int(window_name.split('_')[1])  # Extract 5 or 10 from 'rolling_5'
            
            # Calculate rolling average (using min_periods=1 for early games)
            rolling_col = f'{metric}_{window_name}'
            team_df[rolling_col] = team_df[metric].rolling(
                window=window_size, 
                min_periods=1
            ).mean()
    
    return team_df

# Process each team separately for home and away games
all_results = []

# Get unique teams
all_teams = set(df['home_team_id'].unique()) | set(df['away_team_id'].unique())
print(f"\nProcessing {len(all_teams)} teams...")

for team_id in sorted(all_teams):
    # Get all games for this team (both home and away)
    home_games = df[df['home_team_id'] == team_id].copy()
    away_games = df[df['away_team_id'] == team_id].copy()
    
    # Add prefix to identify home vs away
    home_games['is_home'] = True
    away_games['is_home'] = False
    
    # Combine and sort by date
    team_games = pd.concat([home_games, away_games]).sort_values('date')
    
    # Prepare metrics for this team
    team_metrics = {}
    
    # Collect the base metric values for this team from both perspectives
    for game_idx, row in team_games.iterrows():
        game_date = row['date']
        game_id = row['balldontlie_game_id']
        is_home = row['is_home']
        
        # Store metrics with proper prefix
        prefix = 'home' if is_home else 'away'
        
        for base_metric in rolling_metrics.keys():
            col_name = f'{prefix}_{base_metric}'
            if col_name in row.index:
                # Track this value
                if base_metric not in team_metrics:
                    team_metrics[base_metric] = []
                team_metrics[base_metric].append({
                    'date': game_date,
                    'game_id': game_id,
                    'is_home': is_home,
                    'value': row[col_name]
                })
    
    # Compute rolling averages for each metric
    for metric, values_list in team_metrics.items():
        if not values_list:
            continue
            
        metric_df = pd.DataFrame(values_list)
        metric_df = metric_df.sort_values('date')
        
        # Compute rolling averages
        for window_name in rolling_metrics[metric]:
            window_size = int(window_name.split('_')[1])
            
            # Calculate rolling average
            metric_df[f'{metric}_{window_name}'] = metric_df['value'].rolling(
                window=window_size,
                min_periods=1
            ).mean()
        
        # Store results back
        all_results.append({
            'team_id': team_id,
            'metric': metric,
            'data': metric_df
        })

print("  ✓ Computed rolling averages for all teams")

print("\n" + "="*80)
print("MERGING ROLLING AVERAGES BACK TO DATASET")
print("="*80)

# Initialize new columns with NaN
columns_added = 0

for metric, window_list in rolling_metrics.items():
    for window_name in window_list:
        for prefix in ['home', 'away']:
            col_name = f'{prefix}_{metric}_{window_name}'
            df[col_name] = np.nan
            columns_added += 1

print(f"\nInitialized {columns_added} new rolling average columns")

# Map rolling averages back to main dataset
print("\nMapping rolling averages to games...")

for result in all_results:
    team_id = result['team_id']
    metric = result['metric']
    metric_data = result['data']
    
    for idx, row in metric_data.iterrows():
        game_id = row['game_id']
        is_home = row['is_home']
        prefix = 'home' if is_home else 'away'
        
        # Find this game in the main dataset
        game_mask = (df['balldontlie_game_id'] == game_id) & (df[f'{prefix}_team_id'] == team_id)
        
        if game_mask.sum() > 0:
            # Copy rolling values
            for window_name in rolling_metrics[metric]:
                rolling_col = f'{metric}_{window_name}'
                if rolling_col in row.index:
                    df.loc[game_mask, f'{prefix}_{rolling_col}'] = row[rolling_col]

print("  ✓ All rolling averages mapped to dataset")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

# Count successfully created columns
rolling_cols = [col for col in df.columns if 'rolling_' in col]
print(f"\nTotal rolling average columns created: {len(rolling_cols)}")

# Break down by window
rolling_5_cols = [col for col in rolling_cols if 'rolling_5' in col]
rolling_10_cols = [col for col in rolling_cols if 'rolling_10' in col]

print(f"  Rolling 5-game window: {len(rolling_5_cols)} columns")
print(f"  Rolling 10-game window: {len(rolling_10_cols)} columns")

print(f"\nNew dataset size: {len(df)} rows × {len(df.columns)} columns")

# Show sample statistics
print("\n" + "="*80)
print("SAMPLE STATISTICS")
print("="*80)

sample_metrics = ['batting_ops_rolling_10', 'pitching_era_rolling_10', 'batting_r_per_g_rolling_5']

for metric in sample_metrics:
    home_col = f'home_{metric}'
    away_col = f'away_{metric}'
    
    if home_col in df.columns:
        non_null_home = df[home_col].notna().sum()
        non_null_away = df[away_col].notna().sum()
        print(f"\n{metric.upper()}:")
        print(f"  Home - Non-null: {non_null_home}/{len(df)}, Mean: {df[home_col].mean():.3f}")
        print(f"  Away - Non-null: {non_null_away}/{len(df)}, Mean: {df[away_col].mean():.3f}")

# Save the updated dataset
print("\n" + "="*80)
print("SAVING UPDATED DATASET")
print("="*80)

df.to_csv('data/bdl_data/2025_bdl_dataset.csv', index=False)
print(f"\n✓ Saved: data/bdl_data/2025_bdl_dataset.csv")
print(f"  Rows: {len(df)}")
print(f"  Columns: {len(df.columns)}")

print("\n✓✓✓ ROLLING AVERAGES COMPUTED SUCCESSFULLY! ✓✓✓")
print("="*80)
