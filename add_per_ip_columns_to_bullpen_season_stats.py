"""
Add per-IP standardized columns to team bullpen season-to-date stats.
Each stat gets a corresponding _per_ip column placed immediately after it.
"""

import pandas as pd
import glob
import os

def add_per_ip_columns():
    """
    Add per-IP standardized columns to all team bullpen season-to-date CSV files.
    """
    
    # Get all CSV files in the directory
    stats_files = glob.glob('data/mlb_data/derived_stats/team_bullpen_season_to_date_stats/*.csv')
    
    print(f"Found {len(stats_files)} files to process")
    
    # Stats that should be standardized per IP (excluding IP itself)
    stats_to_standardize = [
        'total_hits',
        'total_earned_runs',
        'total_walks',
        'total_strikeouts',
        'total_homeruns'
    ]
    
    for stats_file in stats_files:
        print(f"\nProcessing {os.path.basename(stats_file)}...")
        
        # Load the CSV
        df = pd.read_csv(stats_file)
        
        # Create a new dataframe with columns in the desired order
        new_columns = []
        
        # Start with game_pk and date
        new_columns.extend(['game_pk', 'date'])
        
        # Add team IDs and names
        new_columns.extend(['home_team_id', 'away_team_id', 'home_team_name', 'away_team_name'])
        
        # Add games
        new_columns.extend(['home_games', 'away_games'])
        
        # Add IP (no per-IP calculation for IP itself)
        new_columns.extend(['home_total_ip', 'away_total_ip'])
        
        # For each stat, add raw values then per-IP values
        for stat in stats_to_standardize:
            home_col = f'home_{stat}'
            away_col = f'away_{stat}'
            home_per_ip_col = f'home_{stat}_per_ip'
            away_per_ip_col = f'away_{stat}_per_ip'
            
            # Add raw columns
            new_columns.extend([home_col, away_col])
            
            # Calculate per-IP columns
            # Avoid division by zero
            df[home_per_ip_col] = df.apply(
                lambda row: round(row[home_col] / row['home_total_ip'], 3) if row['home_total_ip'] > 0 else 0.0,
                axis=1
            )
            df[away_per_ip_col] = df.apply(
                lambda row: round(row[away_col] / row['away_total_ip'], 3) if row['away_total_ip'] > 0 else 0.0,
                axis=1
            )
            
            # Add per-IP columns
            new_columns.extend([home_per_ip_col, away_per_ip_col])
        
        # Add the existing rate stats (ERA, WHIP, K/9, etc.)
        rate_stats = ['era', 'whip', 'k_per_9', 'k_bb_ratio', 'hr_per_9', 'bb_per_9']
        for stat in rate_stats:
            new_columns.extend([f'home_{stat}', f'away_{stat}'])
        
        # Reorder dataframe columns
        df_reordered = df[new_columns]
        
        # Save back to file
        df_reordered.to_csv(stats_file, index=False)
        print(f"  Added {len(stats_to_standardize) * 2} per-IP columns")
        print(f"  Total columns: {len(df_reordered.columns)}")
    
    print("\n" + "="*60)
    print("Processing complete!")
    print(f"Processed {len(stats_files)} files")
    print("\nNew column structure:")
    print("  game_pk, date")
    print("  home_team_id, away_team_id, home_team_name, away_team_name")
    print("  home_games, away_games")
    print("  home_total_ip, away_total_ip")
    print("  For each stat:")
    print("    home_[stat], away_[stat], home_[stat]_per_ip, away_[stat]_per_ip")
    print("  Plus existing rate stats (ERA, WHIP, K/9, etc.)")

if __name__ == "__main__":
    add_per_ip_columns()
