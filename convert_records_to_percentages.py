"""
Convert record columns (W-L format) to win percentages in team_season_standings.csv
"""

import pandas as pd
import numpy as np

# Input file
INPUT_FILE = '/workspaces/MLB-Model/data/bdl_data/team_season_standings.csv'
OUTPUT_FILE = '/workspaces/MLB-Model/data/bdl_data/team_season_standings.csv'


def record_to_percentage(record_str):
    """
    Convert W-L record string (e.g., "55-41") to win percentage.
    Returns 0.0 for "0-0" or invalid records.
    """
    if pd.isna(record_str) or record_str == '-' or record_str == '':
        return 0.0
    
    try:
        parts = str(record_str).split('-')
        if len(parts) != 2:
            return 0.0
        
        wins = int(parts[0])
        losses = int(parts[1])
        total = wins + losses
        
        if total == 0:
            return 0.0
        
        return wins / total
    except (ValueError, AttributeError):
        return 0.0


def convert_record_columns(df):
    """
    Convert all record columns from W-L format to win percentage.
    """
    # List of columns that contain W-L records
    record_columns = [
        'home_total',
        'away_total',
        'home_home',
        'away_home',
        'home_road',
        'away_road',
        'home_intra_division',
        'away_intra_division',
        'home_intra_league',
        'away_intra_league',
        'home_last_ten_games',
        'away_last_ten_games'
    ]
    
    print("\nConverting record columns to percentages:")
    for col in record_columns:
        if col in df.columns:
            print(f"  Converting {col}...")
            # Store a few sample values before conversion
            sample_before = df[col].iloc[1:6].tolist()
            
            # Convert the column
            df[col] = df[col].apply(record_to_percentage)
            
            # Show samples after conversion
            sample_after = df[col].iloc[1:6].tolist()
            print(f"    Samples: {sample_before[:3]} → {sample_after[:3]}")
        else:
            print(f"  WARNING: Column {col} not found in dataframe")
    
    return df


def main():
    print("Loading team_season_standings.csv...")
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    
    print("\nSample records before conversion:")
    record_cols_sample = ['home_total', 'away_total', 'home_home', 'home_road']
    for col in record_cols_sample:
        if col in df.columns:
            non_zero = df[df[col] != '0-0'][col].head(3).tolist()
            if non_zero:
                print(f"  {col}: {non_zero}")
    
    print("\nConverting records to percentages...")
    df = convert_record_columns(df)
    
    print(f"\nSaving to {OUTPUT_FILE}...")
    df.to_csv(OUTPUT_FILE, index=False)
    print("✅ Done!")
    
    # Show sample statistics
    print("\n📊 Sample percentages:")
    for col in ['home_total', 'away_total', 'home_last_ten_games']:
        if col in df.columns:
            non_zero_mask = df[col] > 0
            if non_zero_mask.sum() > 0:
                data = df.loc[non_zero_mask, col]
                print(f"{col}: Mean={data.mean():.3f}, "
                      f"Range=[{data.min():.3f}, {data.max():.3f}]")


if __name__ == '__main__':
    main()
