import pandas as pd
import glob

def find_mismatched_games(year):
    """Find specific games that are on different dates between boxscores and outlook."""
    
    print(f"\n{'='*80}")
    print(f"Finding Date Mismatches for {year}")
    print('='*80)
    
    # Load MLB boxscores
    boxscore_files = glob.glob(f'data/{year}_data/mlb_data/raw/boxscores/*.csv')
    boxscore_dfs = [pd.read_csv(f) for f in boxscore_files]
    boxscores = pd.concat(boxscore_dfs, ignore_index=True)
    
    # Load BDL game outlook
    outlook_files = glob.glob(f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook/*.csv')
    outlook_dfs = [pd.read_csv(f) for f in outlook_files]
    outlook = pd.concat(outlook_dfs, ignore_index=True)
    
    # Parse dates
    boxscores['date'] = pd.to_datetime(boxscores['date']).dt.date.astype(str)
    outlook['date'] = pd.to_datetime(outlook['date']).dt.date.astype(str)
    
    # Mismatched dates
    mismatch_dates = [
        ('2010-04-16', '2010-04-17'),
        ('2010-05-25', '2010-05-26')
    ]
    
    for date_less, date_more in mismatch_dates:
        print(f"\n{'='*80}")
        print(f"Comparing {date_less} and {date_more}")
        print('='*80)
        
        # Get games for both dates
        box_less = boxscores[boxscores['date'] == date_less][['game_pk', 'home_team_abbreviation', 'away_team_abbreviation', 'date']]
        box_more = boxscores[boxscores['date'] == date_more][['game_pk', 'home_team_abbreviation', 'away_team_abbreviation', 'date']]
        
        out_less = outlook[outlook['date'] == date_less][['id', 'home_team_abbreviation', 'away_team_abbreviation', 'date']]
        out_more = outlook[outlook['date'] == date_more][['id', 'home_team_abbreviation', 'away_team_abbreviation', 'date']]
        
        print(f"\n{date_less}:")
        print(f"  Boxscores: {len(box_less)} games")
        print(f"  Outlook:   {len(out_less)} games")
        
        print(f"\n{date_more}:")
        print(f"  Boxscores: {len(box_more)} games")
        print(f"  Outlook:   {len(out_more)} games")
        
        # Create matchup strings for comparison
        box_less['matchup'] = box_less['home_team_abbreviation'] + ' vs ' + box_less['away_team_abbreviation']
        box_more['matchup'] = box_more['home_team_abbreviation'] + ' vs ' + box_more['away_team_abbreviation']
        out_less['matchup'] = out_less['home_team_abbreviation'] + ' vs ' + out_less['away_team_abbreviation']
        out_more['matchup'] = out_more['home_team_abbreviation'] + ' vs ' + out_more['away_team_abbreviation']
        
        # Find games that are in outlook but not in boxscores for each date
        print(f"\nGames in Outlook on {date_less} but not in Boxscores on {date_less}:")
        misplaced_less = out_less[~out_less['matchup'].isin(box_less['matchup'])]
        if len(misplaced_less) > 0:
            for _, row in misplaced_less.iterrows():
                print(f"  ID {row['id']}: {row['matchup']}")
                # Check if this game is in boxscores on the other date
                if row['matchup'] in box_more['matchup'].values:
                    print(f"    ⚠️  This game IS in Boxscores on {date_more}")
        else:
            print("  None")
        
        print(f"\nGames in Outlook on {date_more} but not in Boxscores on {date_more}:")
        misplaced_more = out_more[~out_more['matchup'].isin(box_more['matchup'])]
        if len(misplaced_more) > 0:
            for _, row in misplaced_more.iterrows():
                print(f"  ID {row['id']}: {row['matchup']}")
                # Check if this game is in boxscores on the other date
                if row['matchup'] in box_less['matchup'].values:
                    print(f"    ⚠️  This game IS in Boxscores on {date_less}")
        else:
            print("  None")

if __name__ == "__main__":
    find_mismatched_games(2010)
