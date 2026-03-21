import pandas as pd

def filter_boxscores():
    """
    Filter the three consolidated boxscore files to match only the games 
    in the main dataset (2,430 rows instead of 2,464).
    """
    print("="*80)
    print("FILTERING BOXSCORE FILES TO MATCH MAIN DATASET")
    print("="*80)
    print()
    
    # Load main dataset
    print("Loading main dataset...")
    main_df = pd.read_csv("data/bdl_data/2025_bdl_dataset_with_duplicates.csv")
    print(f"Main dataset rows: {len(main_df):,}")
    
    # Get the MLB game_pk values from the main dataset (column 'id.1')
    main_game_pks = set(main_df['id.1'].dropna().astype(int))
    print(f"Unique game PKs in main dataset: {len(main_game_pks):,}")
    print()
    
    # 1. Filter team boxscores
    print("1. Filtering Team Boxscores")
    print("-" * 40)
    team_df = pd.read_csv("data/mlb_data/team_boxscores_all.csv")
    print(f"Before filtering: {len(team_df):,} rows")
    
    team_filtered = team_df[team_df['id'].isin(main_game_pks)].copy()
    print(f"After filtering: {len(team_filtered):,} rows")
    print(f"Removed: {len(team_df) - len(team_filtered)} rows")
    
    team_filtered.to_csv("data/mlb_data/team_boxscores_all.csv", index=False)
    print(f"✓ Saved: data/mlb_data/team_boxscores_all.csv")
    print()
    
    # 2. Filter starting pitcher boxscores
    print("2. Filtering Starting Pitcher Boxscores")
    print("-" * 40)
    starter_df = pd.read_csv("data/mlb_data/starting_pitcher_boxscores_all.csv")
    print(f"Before filtering: {len(starter_df):,} rows")
    
    starter_filtered = starter_df[starter_df['game_pk'].isin(main_game_pks)].copy()
    print(f"After filtering: {len(starter_filtered):,} rows")
    print(f"Removed: {len(starter_df) - len(starter_filtered)} rows")
    
    starter_filtered.to_csv("data/mlb_data/starting_pitcher_boxscores_all.csv", index=False)
    print(f"✓ Saved: data/mlb_data/starting_pitcher_boxscores_all.csv")
    print()
    
    # 3. Filter team bullpen boxscores
    print("3. Filtering Team Bullpen Boxscores")
    print("-" * 40)
    bullpen_df = pd.read_csv("data/mlb_data/team_bullpen_boxscores_all.csv")
    print(f"Before filtering: {len(bullpen_df):,} rows")
    
    bullpen_filtered = bullpen_df[bullpen_df['game_pk'].isin(main_game_pks)].copy()
    print(f"After filtering: {len(bullpen_filtered):,} rows")
    print(f"Removed: {len(bullpen_df) - len(bullpen_filtered)} rows")
    
    bullpen_filtered.to_csv("data/mlb_data/team_bullpen_boxscores_all.csv", index=False)
    print(f"✓ Saved: data/mlb_data/team_bullpen_boxscores_all.csv")
    print()
    
    # Summary
    print("="*80)
    print("✓ FILTERING COMPLETE")
    print("="*80)
    print("\nAll three files now match the main dataset:")
    print(f"  - Team boxscores: {len(team_filtered):,} rows")
    print(f"  - Starting pitcher boxscores: {len(starter_filtered):,} rows")
    print(f"  - Team bullpen boxscores: {len(bullpen_filtered):,} rows")
    print(f"  - Main dataset: {len(main_df):,} rows")
    print()
    
    # Verify no games are missing from boxscores
    team_game_pks = set(team_filtered['id'])
    starter_game_pks = set(starter_filtered['game_pk'])
    bullpen_game_pks = set(bullpen_filtered['game_pk'])
    
    missing_team = main_game_pks - team_game_pks
    missing_starter = main_game_pks - starter_game_pks
    missing_bullpen = main_game_pks - bullpen_game_pks
    
    if missing_team or missing_starter or missing_bullpen:
        print("⚠ WARNING: Some games in main dataset are missing from boxscores:")
        if missing_team:
            print(f"  - Team boxscores missing: {len(missing_team)} games")
        if missing_starter:
            print(f"  - Starting pitcher missing: {len(missing_starter)} games")
        if missing_bullpen:
            print(f"  - Bullpen missing: {len(missing_bullpen)} games")
    else:
        print("✓ All games in main dataset have corresponding boxscore data")

if __name__ == "__main__":
    filter_boxscores()
