"""
Filter team bullpen season-to-date stats to match only games in the main dataset.
"""

import pandas as pd

def filter_bullpen_stats_to_match_dataset():
    """
    Filter bullpen stats to only include games that are in the main dataset.
    """
    
    print("Loading main dataset...")
    main_df = pd.read_csv('data/2025_dataset/2025_dataset.csv')
    print(f"Main dataset has {len(main_df)} games")
    
    # Get the set of game_pks in the main dataset
    # The main dataset uses 'id' column which corresponds to MLB game_pk
    main_game_pks = set(main_df['id'].values)
    print(f"Unique game PKs in main dataset: {len(main_game_pks)}")
    
    print("Loading bullpen season-to-date stats from individual date files...")
    # Load all individual date files and concatenate
    import glob
    date_files = sorted(glob.glob('data/mlb_data/derived_stats/team_bullpen_season_to_date_stats/team_bullpen_season_to_date_2025-*.csv'))
    print(f"Found {len(date_files)} date files")
    
    dfs = []
    for file in date_files:
        df = pd.read_csv(file)
        dfs.append(df)
    
    bullpen_df = pd.concat(dfs, ignore_index=True)
    print(f"Bullpen stats has {len(bullpen_df)} games total")
    
    # Filter bullpen stats to only include games in the main dataset
    print("\nFiltering bullpen stats...")
    filtered_df = bullpen_df[bullpen_df['game_pk'].isin(main_game_pks)].copy()
    print(f"Filtered bullpen stats has {len(filtered_df)} games total")
    
    # Check for duplicates
    n_duplicates = filtered_df['game_pk'].duplicated().sum()
    if n_duplicates > 0:
        print(f"Found {n_duplicates} duplicate games (likely doubleheaders appearing at different points)")
        print("Keeping the entry with lowest team game counts (stats BEFORE the game)")
        
        # For each duplicate game_pk, keep the one with the lowest sum of home_games + away_games
        # This ensures we get the stats from earliest in the season (before the game)
        filtered_df['total_games'] = filtered_df['home_games'] + filtered_df['away_games']
        filtered_df = filtered_df.sort_values(['game_pk', 'total_games']).groupby('game_pk', as_index=False).first()
        filtered_df = filtered_df.drop('total_games', axis=1)
        print(f"After deduplication: {len(filtered_df)} games")
    
    # Sort by date and game_pk
    filtered_df = filtered_df.sort_values(['date', 'game_pk']).reset_index(drop=True)
    
    # Save the filtered dataset
    output_file = 'data/mlb_data/derived_stats/team_bullpen_season_to_date_stats/team_bullpen_season_to_date_filtered_all.csv'
    filtered_df.to_csv(output_file, index=False)
    print(f"\nSaved filtered bullpen stats to {output_file}")
    
    # Also update individual date files
    print("\nUpdating individual date files...")
    for date in filtered_df['date'].unique():
        date_df = filtered_df[filtered_df['date'] == date].copy()
        date_file = f'data/mlb_data/derived_stats/team_bullpen_season_to_date_stats/team_bullpen_season_to_date_{date}.csv'
        date_df.to_csv(date_file, index=False)
        print(f"  Updated {date_file}: {len(date_df)} games")
    
    # Show which games were excluded
    excluded_pks = set(bullpen_df['game_pk'].values) - main_game_pks
    if excluded_pks:
        print(f"\nExcluded {len(excluded_pks)} games not in main dataset:")
        for pk in sorted(excluded_pks)[:10]:  # Show first 10
            print(f"  Game PK: {pk}")
        if len(excluded_pks) > 10:
            print(f"  ... and {len(excluded_pks) - 10} more")
    
    print("\nDone!")

if __name__ == "__main__":
    filter_bullpen_stats_to_match_dataset()
