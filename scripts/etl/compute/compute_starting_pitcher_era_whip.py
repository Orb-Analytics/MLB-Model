"""
Compute ERA and WHIP for starting pitcher boxscores across all years.

ERA = (Earned Runs × 9) / Innings Pitched
WHIP = (Walks + Hits) / Innings Pitched
"""

import pandas as pd
import glob
import os
import numpy as np

def compute_era_whip(df):
    """
    Compute ERA and WHIP for both home and away starters,
    and for individual pitcher rows.
    
    ERA = (ER × 9) / IP
    WHIP = (BB + H) / IP
    
    Returns modified DataFrame with computed stats.
    """
    df_copy = df.copy()
    
    # Compute for home starter
    if 'home_starter_ip' in df_copy.columns:
        # ERA
        df_copy['home_starter_era'] = np.where(
            df_copy['home_starter_ip'] > 0,
            (df_copy['home_starter_earned_runs'] * 9.0) / df_copy['home_starter_ip'],
            0.0
        )
        
        # WHIP
        df_copy['home_starter_whip'] = np.where(
            df_copy['home_starter_ip'] > 0,
            (df_copy['home_starter_walks'] + df_copy['home_starter_hits']) / df_copy['home_starter_ip'],
            0.0
        )
    
    # Compute for away starter
    if 'away_starter_ip' in df_copy.columns:
        # ERA
        df_copy['away_starter_era'] = np.where(
            df_copy['away_starter_ip'] > 0,
            (df_copy['away_starter_earned_runs'] * 9.0) / df_copy['away_starter_ip'],
            0.0
        )
        
        # WHIP
        df_copy['away_starter_whip'] = np.where(
            df_copy['away_starter_ip'] > 0,
            (df_copy['away_starter_walks'] + df_copy['away_starter_hits']) / df_copy['away_starter_ip'],
            0.0
        )
    
    # Compute for individual pitcher rows (if columns exist)
    if 'ip' in df_copy.columns and 'er' in df_copy.columns:
        df_copy['era'] = np.where(
            df_copy['ip'] > 0,
            (df_copy['er'] * 9.0) / df_copy['ip'],
            0.0
        )
    
    # WHIP for individual pitcher rows
    if 'ip' in df_copy.columns and 'h' in df_copy.columns and 'bb' in df_copy.columns:
        # Create whip column if it doesn't exist
        df_copy['whip'] = np.where(
            df_copy['ip'] > 0,
            (df_copy['bb'] + df_copy['h']) / df_copy['ip'],
            0.0
        )
    
    return df_copy


def process_year(year):
    """Process all starting pitcher boxscore files for a given year."""
    pitcher_dir = f'data/{year}_data/mlb_data/raw/starting_pitcher_boxscores/'
    
    if not os.path.exists(pitcher_dir):
        print(f'{year}: Directory not found, skipping...')
        return 0
    
    pitcher_files = sorted(glob.glob(f'{pitcher_dir}/*.csv'))
    
    if not pitcher_files:
        print(f'{year}: No files found, skipping...')
        return 0
    
    files_processed = 0
    
    for file_path in pitcher_files:
        try:
            # Read the file
            df = pd.read_csv(file_path)
            
            # Compute ERA and WHIP
            df_computed = compute_era_whip(df)
            
            # Save back to the same file
            df_computed.to_csv(file_path, index=False)
            
            files_processed += 1
            
        except Exception as e:
            print(f'  Error processing {file_path}: {e}')
    
    return files_processed


def main():
    print('='*70)
    print('COMPUTING ERA AND WHIP FOR STARTING PITCHER BOXSCORES')
    print('='*70)
    
    total_files = 0
    
    for year in range(2009, 2025):  # Process 2009-2024
        print(f'\nProcessing {year}...', end=' ')
        
        files_processed = process_year(year)
        total_files += files_processed
        
        if files_processed > 0:
            print(f'✓ {files_processed} files processed')
        else:
            print('(skipped)')
    
    print('\n' + '='*70)
    print(f'COMPLETE: {total_files} total files processed')
    print('='*70)


if __name__ == '__main__':
    main()
