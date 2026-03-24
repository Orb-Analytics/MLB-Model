import pandas as pd
import glob
from collections import defaultdict

print("="*80)
print("IDENTIFYING WHICH 37 GAMES TO REMOVE")
print("="*80)

# Team abbreviation mapping
ABBR_MAPPING = {'ARI': 'AZ', 'CHW': 'CWS', 'MIA': 'FLA'}

def apply_abbr_mapping(team_abbr):
    if pd.isna(team_abbr):
        return team_abbr
    return ABBR_MAPPING.get(str(team_abbr).strip(), str(team_abbr).strip())

# Step 1: Load original BDL games with their dates
print("\nStep 1: Loading original BDL games...")
original_bdl_files = sorted(glob.glob('data/2009_data/mlb_data/raw/bdl_data/game_outlook/backup_before_game_pk/game_outlook_*.csv'))

# Index: date -> list of matchups in order
bdl_games_by_date = {}

for file in original_bdl_files:
    date = file.split('_')[-1].replace('.csv', '')
    df = pd.read_csv(file)
    df['away_team_abbreviation'] = df['away_team_abbreviation'].apply(apply_abbr_mapping)
    df['home_team_abbreviation'] = df['home_team_abbreviation'].apply(apply_abbr_mapping)
    
    date_matchups = []
    for _, row in df.iterrows():
        away = row['away_team_abbreviation']
        home = row['home_team_abbreviation']
        date_matchups.append((away, home))
    
    bdl_games_by_date[date] = date_matchups

total_bdl = sum(len(v) for v in bdl_games_by_date.values())
print(f"  Original BDL: {total_bdl} games across {len(bdl_games_by_date)} dates")

# Step 2: Load boxscore games and match them to BDL games
print("\nStep 2: Matching boxscore games to original BDL games...")
boxscore_files = sorted(glob.glob('data/2009_data/mlb_data/raw/boxscores/boxscores_*.csv'))

games_to_keep = []  # game_pks to keep
games_to_remove = []  # game_pks to remove

for file in boxscore_files:
    date = file.split('_')[-1].replace('.csv', '')
    df = pd.read_csv(file)
    
    # Get BDL matchups for this date (if any)
    bdl_matchups = bdl_games_by_date.get(date, [])
    
    # Build a list to track which BDL matchups we've matched
    bdl_matched = [False] * len(bdl_matchups)
    
    for _, row in df.iterrows():
        game_pk = int(row['game_pk'])
        away = row['away_team_abbreviation']
        home = row['home_team_abbreviation']
        matchup = (away, home)
        
        # Try to find this matchup in BDL games for this date
        matched = False
        for i, bdl_matchup in enumerate(bdl_matchups):
            if bdl_matchup == matchup and not bdl_matched[i]:
                # Match found - mark as matched
                bdl_matched[i] = True
                matched = True
                games_to_keep.append({
                    'date': date,
                    'game_pk': game_pk,
                    'matchup': f"{away}@{home}"
                })
                break
        
        if not matched:
            # This game is in boxscore but not in BDL
            games_to_remove.append({
                'date': date,
                'game_pk': game_pk,
                'matchup': f"{away}@{home}"
            })

print(f"  Games to keep: {len(games_to_keep)}")
print(f"  Games to remove: {len(games_to_remove)}")

# Show games to remove
print(f"\n  Games TO REMOVE (37 extras from MLB that weren't in BDL):")
for game in sorted(games_to_remove, key=lambda x: x['date']):
    print(f"    {game['date']}: {game['matchup']} (game_pk {game['game_pk']})")

# Save the list of game_pks to keep
print("\nStep 3: Saving list of game_pks to keep...")
keep_df = pd.DataFrame(games_to_keep)
keep_df.to_csv('games_to_keep_2430.csv', index=False)
print(f"  Saved {len(keep_df)} game_pks to games_to_keep_2430.csv")

remove_df = pd.DataFrame(games_to_remove)
remove_df.to_csv('games_to_remove_37.csv', index=False)
print(f"  Saved {len(remove_df)} game_pks to games_to_remove_37.csv")

print("="*80)
