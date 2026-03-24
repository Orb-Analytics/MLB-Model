import pandas as pd
import glob

def find_missing_pitcher_records(year):
    """Find games that have boxscores but no starting pitcher data."""
    
    # Load all boxscores for the year
    boxscore_files = glob.glob(f'data/{year}_data/mlb_data/raw/boxscores/*.csv')
    if not boxscore_files:
        print(f"No boxscore files found for {year}")
        return []
    
    boxscore_dfs = [pd.read_csv(f) for f in boxscore_files]
    boxscores = pd.concat(boxscore_dfs, ignore_index=True)
    
    # Load all starting pitcher boxscores for the year
    pitcher_files = glob.glob(f'data/{year}_data/mlb_data/raw/starting_pitcher_boxscores/*.csv')
    if not pitcher_files:
        print(f"No pitcher files found for {year}")
        pitcher_game_pks = set()
    else:
        pitcher_dfs = [pd.read_csv(f) for f in pitcher_files]
        pitchers = pd.concat(pitcher_dfs, ignore_index=True)
        pitcher_game_pks = set(pitchers['game_pk'].unique())
    
    # Find game_pks in boxscores but not in pitchers
    boxscore_game_pks = set(boxscores['game_pk'].unique())
    missing_game_pks = boxscore_game_pks - pitcher_game_pks
    
    if not missing_game_pks:
        print(f"{year}: No missing pitcher records")
        return []
    
    # Get details of missing games
    missing_games = boxscores[boxscores['game_pk'].isin(missing_game_pks)].copy()
    missing_games = missing_games.sort_values('date')
    
    print(f"\n{year}: Found {len(missing_game_pks)} missing pitcher record(s)")
    print("=" * 80)
    
    for _, game in missing_games.iterrows():
        print(f"game_pk: {game['game_pk']}")
        print(f"  Date: {game['date']}")
        print(f"  Teams: {game['away_team']} @ {game['home_team']}")
        print()
    
    return list(missing_game_pks)

if __name__ == "__main__":
    years_to_check = [2016, 2018, 2019, 2020]
    
    all_missing = {}
    for year in years_to_check:
        missing = find_missing_pitcher_records(year)
        if missing:
            all_missing[year] = missing
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total_missing = sum(len(v) for v in all_missing.values())
    print(f"Total missing pitcher records: {total_missing}")
    for year, game_pks in all_missing.items():
        print(f"  {year}: {len(game_pks)} game(s) - {game_pks}")
