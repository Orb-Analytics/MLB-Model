import pandas as pd
import numpy as np
from pathlib import Path

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

def create_alternating_columns(df, stat_suffixes):
    """
    Create alternating home/away columns for multiple stat suffixes.
    """
    result = df[['game_pk', 'date']].copy()
    
    for suffix in stat_suffixes:
        result[f'home_{suffix}'] = df[f'home_{suffix}']
        result[f'away_{suffix}'] = df[f'away_{suffix}']
    
    return result

def main():
    print("="*80)
    print("COMPUTING STARTING PITCHER ROLLING AVERAGE STATS")
    print("="*80)
    print()
    
    # Load starting pitcher boxscores
    print("Loading starting pitcher boxscores...")
    df = pd.read_csv("data/mlb_data/starting_pitcher_boxscores_all.csv")
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
    output_dir = Path("data/mlb_data/derived_stats/starting_pitcher_derived_stats")
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
        print(f"    Stats: {', '.join(stat_columns)}")
        print()
    
    print("="*80)
    print("✓ ALL ROLLING STATS COMPUTED AND SAVED")
    print("="*80)
    print(f"\nOutput location: {output_dir}")
    print(f"Files created: {len(stat_groups)}")
    
    # Sample output
    print("\n" + "="*80)
    print("SAMPLE OUTPUT (ERA Rolling - First 3 games)")
    print("="*80)
    sample = pd.read_csv(output_dir / "era_rolling.csv")
    print(sample[['game_pk', 'date', 'home_era_rolling_5', 'away_era_rolling_5', 
                  'home_era_rolling_10', 'away_era_rolling_10']].head(3).to_string(index=False))

if __name__ == "__main__":
    main()
