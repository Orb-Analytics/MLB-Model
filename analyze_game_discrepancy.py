import pandas as pd
import glob

print("="*80)
print("ANALYZING GAME COUNT DISCREPANCY")
print("="*80)

# Step 1: Load original BDL games (from backup before game_pk was added)
print("\nStep 1: Loading original BDL games from backup...")
original_bdl_files = sorted(glob.glob('data/2009_data/mlb_data/raw/bdl_data/game_outlook/backup_before_game_pk/game_outlook_*.csv'))

# Team abbreviation mapping
ABBR_MAPPING = {'ARI': 'AZ', 'CHW': 'CWS', 'MIA': 'FLA'}

def apply_abbr_mapping(team_abbr):
    if pd.isna(team_abbr):
        return team_abbr
    return ABBR_MAPPING.get(str(team_abbr).strip(), str(team_abbr).strip())

original_matchups = set()
for file in original_bdl_files:
    df = pd.read_csv(file)
    df['away_team_abbreviation'] = df['away_team_abbreviation'].apply(apply_abbr_mapping)
    df['home_team_abbreviation'] = df['home_team_abbreviation'].apply(apply_abbr_mapping)
    
    for _, row in df.iterrows():
        away = row['away_team_abbreviation']
        home = row['home_team_abbreviation']
        original_matchups.add((away, home))

print(f"  Original BDL games: {len(original_matchups)}")

# Step 2: Load boxscore games
print("\nStep 2: Loading boxscore games...")
boxscore_files = sorted(glob.glob('data/2009_data/mlb_data/raw/boxscores/boxscores_*.csv'))

boxscore_games = []
for file in boxscore_files:
    date = file.split('_')[-1].replace('.csv', '')
    df = pd.read_csv(file)
    
    for idx, row in df.iterrows():
        boxscore_games.append({
            'date': date,
            'game_pk': int(row['game_pk']),
            'away': row['away_team_abbreviation'],
            'home': row['home_team_abbreviation'],
            'matchup': (row['away_team_abbreviation'], row['home_team_abbreviation'])
        })

print(f"  Boxscore games: {len(boxscore_games)}")

# Step 3: Find games in boxscore but NOT in original BDL
print("\nStep 3: Finding games in boxscore but NOT in original BDL...")
missing_from_bdl = []
matchup_counts = {}

for game in boxscore_games:
    matchup = game['matchup']
    
    # Count matchup occurrences
    if matchup not in matchup_counts:
        matchup_counts[matchup] = 0
    matchup_counts[matchup] += 1
    
    # Check if this matchup exists in BDL
    if matchup not in original_matchups:
        missing_from_bdl.append(game)

print(f"\n  Found {len(missing_from_bdl)} games in boxscore but NOT in original BDL:")
for game in missing_from_bdl[:20]:
    print(f"    {game['date']}: {game['away']}@{game['home']} (game_pk {game['game_pk']})")
if len(missing_from_bdl) > 20:
    print(f"    ... and {len(missing_from_bdl) - 20} more")

# Step 4: Find duplicate matchups (teams played each other multiple times)
print("\nStep 4: Checking for duplicate matchups in boxscore...")
duplicates = {k: v for k, v in matchup_counts.items() if v > 1}
print(f"  Matchups that appear more than once: {len(duplicates)}")

if duplicates:
    # Show top duplicates
    sorted_dups = sorted(duplicates.items(), key=lambda x: x[1], reverse=True)
    print(f"\n  Top 10 most frequent matchups:")
    for matchup, count in sorted_dups[:10]:
        print(f"    {matchup[0]}@{matchup[1]}: {count} games")
        # Check if this matchup was in original BDL
        in_bdl = matchup in original_matchups
        print(f"      In original BDL: {in_bdl}")

# Step 5: Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Original BDL games: 2430")
print(f"Current boxscore games: {len(boxscore_games)}")
print(f"Difference: {len(boxscore_games) - 2430} extra games in boxscore")
print(f"\nGames in boxscore but NOT in original BDL: {len(missing_from_bdl)}")
print(f"Unique matchups in BDL: {len(original_matchups)}")
print(f"Unique matchups in boxscore: {len(set(g['matchup'] for g in boxscore_games))}")

# Check if extra games are due to duplicate matchups
unique_matchups_in_boxscore = set(g['matchup'] for g in boxscore_games)
print(f"\nMatchups in boxscore but not in BDL: {len(unique_matchups_in_boxscore - original_matchups)}")
print("="*80)
