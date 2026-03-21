import pandas as pd
from pathlib import Path

def consolidate_boxscores(input_dir, output_file, file_pattern, sort_columns=None):
    """
    Consolidate all CSV files from a directory into one large CSV.
    
    Args:
        input_dir: Path to directory containing CSV files
        output_file: Path to output consolidated CSV
        file_pattern: Glob pattern to match files (e.g., "team_boxscores_*.csv")
        sort_columns: List of columns to sort by (default: ['date'])
    """
    if sort_columns is None:
        sort_columns = ['date']
    
    input_path = Path(input_dir)
    files = sorted(input_path.glob(file_pattern))
    
    if not files:
        print(f"❌ No files found matching pattern: {file_pattern}")
        return
    
    print(f"Found {len(files)} files to consolidate")
    print(f"Reading and concatenating...")
    
    # Read all files and concatenate
    dfs = []
    for file in files:
        df = pd.read_csv(file)
        dfs.append(df)
    
    # Concatenate all dataframes
    consolidated = pd.concat(dfs, ignore_index=True)
    
    # Sort by specified columns for consistency
    consolidated = consolidated.sort_values(sort_columns).reset_index(drop=True)
    
    # Save consolidated file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    consolidated.to_csv(output_path, index=False)
    
    print(f"✓ Saved: {output_path}")
    print(f"  Total rows: {len(consolidated):,}")
    print(f"  Total columns: {len(consolidated.columns)}")
    print(f"  Date range: {consolidated['date'].min()} to {consolidated['date'].max()}")
    print()

def main():
    print("="*80)
    print("CONSOLIDATING BOXSCORE FILES")
    print("="*80)
    print()
    
    # 1. Consolidate team boxscores
    print("1. Team Boxscores")
    print("-" * 40)
    consolidate_boxscores(
        input_dir="data/mlb_data/team_boxscores",
        output_file="data/mlb_data/team_boxscores_all.csv",
        file_pattern="team_boxscores_*.csv",
        sort_columns=['date', 'id']
    )
    
    # 2. Consolidate starting pitcher boxscores
    print("2. Starting Pitcher Boxscores")
    print("-" * 40)
    consolidate_boxscores(
        input_dir="data/mlb_data/starting_pitcher_boxscores",
        output_file="data/mlb_data/starting_pitcher_boxscores_all.csv",
        file_pattern="starting_pitcher_boxscores_*.csv",
        sort_columns=['date', 'game_pk']
    )
    
    # 3. Consolidate team bullpen boxscores
    print("3. Team Bullpen Boxscores")
    print("-" * 40)
    consolidate_boxscores(
        input_dir="data/mlb_data/team_bullpen_boxscores",
        output_file="data/mlb_data/team_bullpen_boxscores_all.csv",
        file_pattern="team_bullpen_boxscores_*.csv",
        sort_columns=['date', 'game_pk']
    )
    
    print("="*80)
    print("✓ ALL CONSOLIDATIONS COMPLETE")
    print("="*80)
    print("\nOutput files:")
    print("  - data/mlb_data/team_boxscores_all.csv")
    print("  - data/mlb_data/starting_pitcher_boxscores_all.csv")
    print("  - data/mlb_data/team_bullpen_boxscores_all.csv")

if __name__ == "__main__":
    main()
