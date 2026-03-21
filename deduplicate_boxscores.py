import pandas as pd

def deduplicate_boxscores():
    """
    Remove duplicate game PKs from the three consolidated boxscore files
    to match the main dataset (2,430 unique games).
    """
    print("="*80)
    print("DEDUPLICATING BOXSCORE FILES")
    print("="*80)
    print()
    
    # 1. Deduplicate team boxscores
    print("1. Team Boxscores")
    print("-" * 40)
    team_df = pd.read_csv("data/mlb_data/team_boxscores_all.csv")
    print(f"Before deduplication: {len(team_df):,} rows")
    print(f"  Unique game PKs: {team_df['id'].nunique():,}")
    print(f"  Duplicate rows: {len(team_df) - team_df['id'].nunique()}")
    
    team_dedup = team_df.drop_duplicates(subset=['id'], keep='first').reset_index(drop=True)
    print(f"After deduplication: {len(team_dedup):,} rows")
    print(f"  Removed: {len(team_df) - len(team_dedup)} duplicates")
    
    team_dedup.to_csv("data/mlb_data/team_boxscores_all.csv", index=False)
    print(f"✓ Saved: data/mlb_data/team_boxscores_all.csv")
    print()
    
    # 2. Deduplicate starting pitcher boxscores
    print("2. Starting Pitcher Boxscores")
    print("-" * 40)
    starter_df = pd.read_csv("data/mlb_data/starting_pitcher_boxscores_all.csv")
    print(f"Before deduplication: {len(starter_df):,} rows")
    print(f"  Unique game PKs: {starter_df['game_pk'].nunique():,}")
    print(f"  Duplicate rows: {len(starter_df) - starter_df['game_pk'].nunique()}")
    
    starter_dedup = starter_df.drop_duplicates(subset=['game_pk'], keep='first').reset_index(drop=True)
    print(f"After deduplication: {len(starter_dedup):,} rows")
    print(f"  Removed: {len(starter_df) - len(starter_dedup)} duplicates")
    
    starter_dedup.to_csv("data/mlb_data/starting_pitcher_boxscores_all.csv", index=False)
    print(f"✓ Saved: data/mlb_data/starting_pitcher_boxscores_all.csv")
    print()
    
    # 3. Deduplicate team bullpen boxscores
    print("3. Team Bullpen Boxscores")
    print("-" * 40)
    bullpen_df = pd.read_csv("data/mlb_data/team_bullpen_boxscores_all.csv")
    print(f"Before deduplication: {len(bullpen_df):,} rows")
    print(f"  Unique game PKs: {bullpen_df['game_pk'].nunique():,}")
    print(f"  Duplicate rows: {len(bullpen_df) - bullpen_df['game_pk'].nunique()}")
    
    bullpen_dedup = bullpen_df.drop_duplicates(subset=['game_pk'], keep='first').reset_index(drop=True)
    print(f"After deduplication: {len(bullpen_dedup):,} rows")
    print(f"  Removed: {len(bullpen_df) - len(bullpen_dedup)} duplicates")
    
    bullpen_dedup.to_csv("data/mlb_data/team_bullpen_boxscores_all.csv", index=False)
    print(f"✓ Saved: data/mlb_data/team_bullpen_boxscores_all.csv")
    print()
    
    # Summary
    print("="*80)
    print("✓ DEDUPLICATION COMPLETE")
    print("="*80)
    print("\nAll three files now have unique games matching the main dataset:")
    print(f"  - Team boxscores: {len(team_dedup):,} rows")
    print(f"  - Starting pitcher boxscores: {len(starter_dedup):,} rows")
    print(f"  - Team bullpen boxscores: {len(bullpen_dedup):,} rows")
    print(f"  - Main dataset: 2,430 rows")
    print()
    
    # Verify all match
    if len(team_dedup) == len(starter_dedup) == len(bullpen_dedup) == 2430:
        print("✓ All files have exactly 2,430 rows ✓")
    else:
        print("⚠ WARNING: Row counts don't match!")

if __name__ == "__main__":
    deduplicate_boxscores()
