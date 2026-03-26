"""
Remove extra duplicate/empty columns from starting pitcher boxscores.

Years 2015, 2021, and 2024 have 22 extra columns that are mostly empty.
This script removes them to standardize all years to 52 columns.
"""

import pandas as pd
import glob
import os

def clean_pitcher_files(year):
    """Remove columns 53-74 from all files for a given year."""
    pitcher_dir = f'data/{year}_data/mlb_data/raw/starting_pitcher_boxscores/'
    
    if not os.path.exists(pitcher_dir):
        print(f'{year}: Directory not found, skipping...')
        return 0
    
    pitcher_files = sorted(glob.glob(f'{pitcher_dir}/*.csv'))
    
    if not pitcher_files:
        print(f'{year}: No files found, skipping...')
        return 0
    
    # Check if files need cleaning
    sample_df = pd.read_csv(pitcher_files[0])
    if len(sample_df.columns) <= 52:
        print(f'{year}: Already clean (52 columns), skipping...')
        return 0
    
    files_processed = 0
    
    for file_path in pitcher_files:
        try:
            # Read the file
            df = pd.read_csv(file_path)
            
            # Keep only first 52 columns
            df_clean = df.iloc[:, :52]
            
            # Save back to the same file
            df_clean.to_csv(file_path, index=False)
            
            files_processed += 1
            
        except Exception as e:
            print(f'  Error processing {file_path}: {e}')
    
    return files_processed


def main():
    print('='*70)
    print('REMOVING EXTRA COLUMNS FROM STARTING PITCHER BOXSCORES')
    print('='*70)
    
    years_to_clean = [2015, 2021, 2024]
    total_files = 0
    
    for year in years_to_clean:
        print(f'\nCleaning {year}...', end=' ')
        
        files_processed = clean_pitcher_files(year)
        total_files += files_processed
        
        if files_processed > 0:
            print(f'✓ {files_processed} files cleaned')
        else:
            print('(no cleaning needed)')
    
    print('\n' + '='*70)
    print(f'COMPLETE: {total_files} total files cleaned')
    print('All years now have consistent 52-column structure')
    print('='*70)


if __name__ == '__main__':
    main()
