import pandas as pd
import numpy as np

def round_decimals_in_dataset():
    """
    Round all numeric decimal columns to 2 decimal places in the dataset.
    """
    print("Rounding all decimal values to 2 places...")
    
    # Load the dataset
    df = pd.read_csv('/workspaces/MLB-Model/data/2025_dataset/2025_dataset.csv')
    print(f"Loaded {len(df)} rows × {len(df.columns)} columns")
    
    # Identify numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    print(f"Found {len(numeric_cols)} numeric columns")
    
    # Columns that should remain as integers
    integer_cols = [
        'balldontlie_game_id', 'id', 'home_team_id', 'away_team_id',
        'home_starter_id', 'away_starter_id', 'home_season', 'away_season',
        'home_postseason', 'away_postseason', 'home_playoff_seed', 'away_playoff_seed',
        'is_divisional_game'
    ]
    
    # Add count columns (stats that are whole numbers)
    count_suffixes = [
        '_games_played', '_gp', '_gs', '_wins', '_losses',
        '_ab', '_r', '_h', '_2b', '_3b', '_hr', '_rbi', '_tb', '_bb', '_so', '_sb',
        '_w', '_l', '_sv', '_cg', '_sho', '_qs', '_k', '_e', '_tc', '_po', '_a',
        'points_for', 'points_against'
    ]
    
    for col in numeric_cols:
        for suffix in count_suffixes:
            if col.endswith(suffix):
                integer_cols.append(col)
                break
    
    print(f"Identified {len(integer_cols)} integer columns")
    
    # Debug: check specific columns
    debug_cols = ['home_batting_avg', 'home_batting_ab', 'home_pitching_era', 'home_win_percent']
    print("\nDebug - checking specific columns:")
    for col in debug_cols:
        if col in df.columns:
            is_int = col in integer_cols
            print(f"  {col}: {'INTEGER' if is_int else 'FLOAT (will round)'}")
    
    rounded_count = 0
    integer_count = 0
    
    # Process each numeric column
    for col in numeric_cols:
        if col in integer_cols:
            # Keep as integer, but handle NaN values
            df[col] = df[col].fillna(0).astype(int)
            integer_count += 1
        else:
            # Round to 2 decimal places
            df[col] = df[col].round(2)
            rounded_count += 1
    
    print(f"Rounded {rounded_count} columns to 2 decimal places")
    print(f"Kept {integer_count} columns as integers")
    
    # Save the rounded dataset
    output_path = '/workspaces/MLB-Model/data/2025_dataset/2025_dataset.csv'
    df.to_csv(output_path, index=False)
    print(f"\n✓ Saved rounded dataset to {output_path}")
    
    # Show some examples from row with actual data (row index 1)
    print("\n" + "="*60)
    print("Sample values (row 2, selected columns):")
    print("="*60)
    sample_cols = [
        'home_win_percent', 'away_win_percent',
        'home_starter_pitching_era', 'away_starter_pitching_era',
        'home_bp_era', 'away_bp_era',
        'home_batting_avg', 'away_batting_avg',
        'home_pitching_whip', 'away_pitching_whip'
    ]
    
    for col in sample_cols:
        if col in df.columns:
            val = df[col].iloc[1] if len(df) > 1 else df[col].iloc[0]
            print(f"  {col}: {val}")
    
    # Check data types
    print("\n" + "="*60)
    print("Data types for sample columns:")
    print("="*60)
    for col in sample_cols[:4]:
        if col in df.columns:
            print(f"  {col}: {df[col].dtype}")
    
    return df

if __name__ == '__main__':
    df = round_decimals_in_dataset()
    print("\n✓ Rounding complete!")
