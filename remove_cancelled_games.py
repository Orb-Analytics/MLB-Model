import pandas as pd
import glob
import os

def remove_cancelled_games(year, cancelled_game_pks):
    """Remove cancelled games from boxscore files."""
    
    print(f"\n{'='*80}")
    print(f"Processing {year}")
    print('='*80)
    
    # Load all boxscores
    boxscore_files = glob.glob(f'data/{year}_data/mlb_data/raw/boxscores/*.csv')
    boxscore_dfs = [pd.read_csv(f) for f in boxscore_files]
    boxscores = pd.concat(boxscore_dfs, ignore_index=True)
    
    initial_count = len(boxscores)
    print(f"Initial boxscore count: {initial_count}")
    
    # Find cancelled games
    cancelled_games = boxscores[boxscores['game_pk'].isin(cancelled_game_pks)]
    print(f"\nCancelled games found: {len(cancelled_games)}")
    for _, game in cancelled_games.iterrows():
        print(f"  game_pk {game['game_pk']}: {game['date']} - {game['away_team_abbreviation']} @ {game['home_team_abbreviation']}")
    
    # Remove cancelled games
    boxscores_cleaned = boxscores[~boxscores['game_pk'].isin(cancelled_game_pks)].copy()
    
    final_count = len(boxscores_cleaned)
    removed = initial_count - final_count
    
    print(f"\nAfter removal: {final_count} games")
    print(f"Removed: {removed} cancelled game(s)")
    
    if removed == 0:
        print("✅ No games to remove")
        return 0
    
    # Rewrite files by date
    print(f"\nRewriting boxscore files...")
    for date, group in boxscores_cleaned.groupby('date'):
        output_file = f'data/{year}_data/mlb_data/raw/boxscores/boxscores_{date}.csv'
        group.to_csv(output_file, index=False)
    
    # Check if any date files are now empty and should be removed
    for date in cancelled_games['date'].unique():
        remaining = boxscores_cleaned[boxscores_cleaned['date'] == date]
        if len(remaining) == 0:
            file_to_remove = f'data/{year}_data/mlb_data/raw/boxscores/boxscores_{date}.csv'
            if os.path.exists(file_to_remove):
                os.remove(file_to_remove)
                print(f"  Removed empty file: boxscores_{date}.csv")
    
    print(f"✅ Successfully removed {removed} cancelled game(s) from {year}")
    
    # Verify team counts
    away_counts = boxscores_cleaned['away_team_abbreviation'].value_counts()
    home_counts = boxscores_cleaned['home_team_abbreviation'].value_counts()
    total_counts = (away_counts.add(home_counts, fill_value=0)).astype(int)
    
    expected_games = 162 if year != 2020 else 60
    issues = []
    for team, count in total_counts.items():
        if count != expected_games:
            issues.append(f"{team}: {count} games")
    
    if issues:
        print(f"\n⚠️ Team game count issues after removal:")
        for issue in issues:
            print(f"  {issue}")
    
    return removed

if __name__ == "__main__":
    cancelled_games = {
        2016: [449187, 449246],
        2018: [531548],
        2019: [567304],
        2020: [631471, 631472]
    }
    
    total_removed = 0
    for year, game_pks in cancelled_games.items():
        removed = remove_cancelled_games(year, game_pks)
        total_removed += removed
    
    print(f"\n{'='*80}")
    print(f"SUMMARY: Removed {total_removed} cancelled game(s) total")
    print('='*80)
    
    # Final verification
    print("\n" + "="*80)
    print("FINAL VERIFICATION")
    print("="*80)
    
    for year in [2016, 2018, 2019, 2020]:
        boxscore_files = glob.glob(f'data/{year}_data/mlb_data/raw/boxscores/*.csv')
        boxscore_dfs = [pd.read_csv(f) for f in boxscore_files]
        boxscores = pd.concat(boxscore_dfs, ignore_index=True)
        
        pitcher_files = glob.glob(f'data/{year}_data/mlb_data/raw/starting_pitcher_boxscores/*.csv')
        pitcher_dfs = [pd.read_csv(f) for f in pitcher_files]
        pitchers = pd.concat(pitcher_dfs, ignore_index=True)
        
        expected = 2430 if year != 2020 else 900
        match_status = "✅" if len(boxscores) == len(pitchers) else "⚠️"
        print(f"{year}: Boxscores={len(boxscores)} | Pitchers={len(pitchers)} {match_status}")
