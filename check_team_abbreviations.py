import pandas as pd
import glob

def check_team_abbreviations(year):
    """Check if there are team abbreviation mismatches between boxscores and outlook."""
    
    print(f"\n{'='*80}")
    print(f"Checking Team Abbreviations for {year}")
    print('='*80)
    
    # Load boxscores
    boxscore_files = glob.glob(f'data/{year}_data/mlb_data/raw/boxscores/*.csv')
    boxscore_dfs = [pd.read_csv(f) for f in boxscore_files]
    boxscores = pd.concat(boxscore_dfs, ignore_index=True)
    
    # Load outlook
    outlook_files = glob.glob(f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook/*.csv')
    outlook_dfs = [pd.read_csv(f) for f in outlook_files]
    outlook = pd.concat(outlook_dfs, ignore_index=True)
    
    # Get unique team abbreviations
    box_home = set(boxscores['home_team_abbreviation'].unique())
    box_away = set(boxscores['away_team_abbreviation'].unique())
    box_teams = sorted(box_home | box_away)
    
    out_home = set(outlook['home_team_abbreviation'].unique())
    out_away = set(outlook['away_team_abbreviation'].unique())
    out_teams = sorted(out_home | out_away)
    
    print(f"\nBoxscore team abbreviations ({len(box_teams)}):")
    print(box_teams)
    
    print(f"\nOutlook team abbreviations ({len(out_teams)}):")
    print(out_teams)
    
    # Find differences
    only_in_box = sorted(set(box_teams) - set(out_teams))
    only_in_outlook = sorted(set(out_teams) - set(box_teams))
    
    if only_in_box:
        print(f"\n⚠️  Only in Boxscores: {only_in_box}")
    
    if only_in_outlook:
        print(f"⚠️  Only in Outlook: {only_in_outlook}")
    
    # Try to find potential mappings by looking at unmatched games
    print(f"\n{'='*80}")
    print("Analyzing Unmatched Games")
    print('='*80)
    
    outlook['date_parsed'] = pd.to_datetime(outlook['date']).dt.date.astype(str)
    boxscores['date'] = pd.to_datetime(boxscores['date']).dt.date.astype(str)
    
    # Find games in outlook with no game_pk
    unmatched = outlook[outlook['game_pk'].isna()].copy()
    
    print(f"\nTotal unmatched: {len(unmatched)}")
    print(f"\nSample unmatched games:")
    
    for _, game in unmatched.head(5).iterrows():
        date = game['date_parsed']
        home = game['home_team_abbreviation']
        away = game['away_team_abbreviation']
        
        print(f"\n  {home} vs {away} on {date}")
        
        # Check if there are any boxscore games on this date with similar teams
        date_games = boxscores[boxscores['date'] == date]
        print(f"    Boxscores on {date}:")
        for _, bg in date_games.iterrows():
            print(f"      {bg['home_team_abbreviation']} vs {bg['away_team_abbreviation']}")

if __name__ == "__main__":
    check_team_abbreviations(2010)
