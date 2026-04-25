"""
Consolidate date-specific CSV files into single large datasets.
Creates 5 combined CSV files for easier data access.
"""

import pandas as pd
import glob
import os

def consolidate_dataset(input_pattern, output_file, dataset_name):
    """
    Consolidate multiple CSV files into a single file.
    
    Args:
        input_pattern: Glob pattern to find input files
        output_file: Path to output consolidated file
        dataset_name: Name of dataset for logging
    """
    print(f"\n{'='*80}")
    print(f"Consolidating {dataset_name}")
    print(f"{'='*80}")
    
    # Find all files matching pattern
    files = sorted(glob.glob(input_pattern))
    print(f"Found {len(files)} files to consolidate")
    
    if not files:
        print(f"WARNING: No files found for pattern: {input_pattern}")
        return
    
    # Read and concatenate all files
    dfs = []
    total_rows = 0
    
    for i, file in enumerate(files, 1):
        df = pd.read_csv(file)
        dfs.append(df)
        total_rows += len(df)
        
        if i % 20 == 0:
            print(f"  Processed {i}/{len(files)} files... ({total_rows} rows so far)")
    
    # Concatenate all dataframes
    print(f"\nCombining {len(dfs)} dataframes...")
    combined_df = pd.concat(dfs, ignore_index=True)
    
    print(f"Total rows: {len(combined_df)}")
    print(f"Total columns: {len(combined_df.columns)}")
    
    # Save to CSV
    print(f"Saving to {output_file}...")
    combined_df.to_csv(output_file, index=False)
    
    # Get file size
    file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"Saved! File size: {file_size_mb:.2f} MB")
    
    # Show sample
    print(f"\nSample data (first row):")
    print(combined_df.head(1).to_dict('records')[0])
    
    return combined_df

def main():
    """Consolidate all datasets."""
    
    print("="*80)
    print("MLB MODEL DATA CONSOLIDATION")
    print("="*80)
    print("\nConsolidating 5 datasets into single CSV files...")
    
    datasets = [
        {
            'name': 'Game Outlook',
            'pattern': 'data/bdl_data/game_outlook/game_outlook_*.csv',
            'output': 'data/bdl_data/game_outlook.csv'
        },
        {
            'name': 'Team Season Standings',
            'pattern': 'data/bdl_data/team_season_standings/team_season_standings_*.csv',
            'output': 'data/bdl_data/team_season_standings.csv'
        },
        {
            'name': 'Starting Pitcher Stats',
            'pattern': 'data/bdl_data/starting_pitcher_stats/starting_pitcher_stats_*.csv',
            'output': 'data/bdl_data/starting_pitcher_stats.csv'
        },
        {
            'name': 'Team Season Stats',
            'pattern': 'data/bdl_data/team_season_stats/team_season_stats_*.csv',
            'output': 'data/bdl_data/team_season_stats.csv'
        },
        {
            'name': 'Box Scores',
            'pattern': 'data/bdl_data/boxscores/boxscores_*.csv',
            'output': 'data/bdl_data/boxscores.csv'
        },
    ]
    
    results = {}
    
    for dataset in datasets:
        try:
            df = consolidate_dataset(
                dataset['pattern'],
                dataset['output'],
                dataset['name']
            )
            results[dataset['name']] = {
                'success': True,
                'output': dataset['output'],
                'rows': len(df) if df is not None else 0
            }
        except Exception as e:
            print(f"\nERROR consolidating {dataset['name']}: {e}")
            results[dataset['name']] = {
                'success': False,
                'error': str(e)
            }
    
    # Final summary
    print("\n" + "="*80)
    print("CONSOLIDATION SUMMARY")
    print("="*80)
    
    for dataset_name, result in results.items():
        if result['success']:
            print(f"\n✓ {dataset_name}")
            print(f"  Output: {result['output']}")
            print(f"  Rows: {result['rows']:,}")
        else:
            print(f"\n✗ {dataset_name}")
            print(f"  Error: {result['error']}")
    
    print("\n" + "="*80)
    print("All consolidated files saved to: data/bdl_data/")
    print("="*80)

if __name__ == '__main__':
    main()
