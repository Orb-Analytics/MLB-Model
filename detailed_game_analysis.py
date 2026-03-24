import pandas as pd
import glob
from collections import Counter

print("="*80)
print("DETAILED ANALYSIS: ORIGINAL BDL vs BOXSCORE GAMES")
print("="*80)

# Team abbreviation mapping
ABBR_MAPPING = {'ARI': 'AZ', 'CHW': 'CWS', 'MIA': 'FLA'}

def apply_abbr_mapping(team_abbr):
    if pd.isna(team_abbr):
        return team_abbr
    return ABBR_MAPPING.get(str(team_abbr).strip(), str(team_abbr).strip())

# Step 1: Load ALL games from original BDL (not unique, but all instances)
print("\nStep 1: Loading ALL games from original BDL backup...")
original_bdl_files = sorted(glob.glob('data/2009_data/mlb_data/raw/bdl_data/game_outlook/backup_before_game_pk/game_outlook_*.csv'))

original_games_by_date = {}  # date -> list of (away, home)
all_original_matchups = []  # All matchups including duplicates

for file in original_bdl_files:
    date = file.split('_')[-1].replace('.csv', '')
    df = pd.read_csv(file)
    df['away_team_abbreviation'] = df['away_team_abbreviation'].apply(apply_abbr_mapping)
    df['home_team_abbreviation'] = df['home_team_abbreviation'].apply(apply_abbr_mapping)
    
    date_games = []
    for _, row in df.iterrows():
        away = row['away_team_abbreviation']
        home = row['home_team_abbreviation']
        matchup = (away, home)
        all_original_matchups.append(matchup)
        date_games.append(matchup)
    
    original_games_by_date[date] = date_games

print(f"  Total original BDL games: {len(all_original_matchups)}")
print(f"  Unique matchups: {len(set(all_original_matchups))}")

# Count matchup frequencies in original BDL
original_matchup_counts = Counter(all_original_matchups)
print(f"\n  Top 10 most frequent matchups in original BDL:")
for matchup, count in original_matchup_counts.most_common(10):
    print(f"    {matchup[0]}@{matchup[1]}: {count} games")

# Step 2: Load ALL games from boxscore
print("\nStep 2: Loading ALL games from boxscore...")
boxscore_files = sorted(glob.glob('data/2009_data/mlb_data/raw/boxscores/boxscores_*.csv'))

boxscore_games_by_date = {}  # date -> list of (game_pk, away, home)
all_boxscore_matchups = []

for file in boxscore_files:
    date = file.split('_')[-1].replace('.csv', '')
    df = pd.read_csv(file)
    
    date_games = []
    for _, row in df.iterrows():
        away = row['away_team_abbreviation']
        home = row['home_team_abbreviation']
        matchup = (away, home)
        all_boxscore_matchups.append(matchup)
        date_games.append((int(row['game_pk']), matchup))
    
    boxscore_games_by_date[date] = date_games

print(f"  Total boxscore games: {len(all_boxscore_matchups)}")
print(f"  Unique matchups: {len(set(all_boxscore_matchups))}")

# Count matchup frequencies in boxscore
boxscore_matchup_counts = Counter(all_boxscore_matchups)
print(f"\n  Top 10 most frequent matchups in boxscore:")
for matchup, count in boxscore_matchup_counts.most_common(10):
    print(f"    {matchup[0]}@{matchup[1]}: {count} games")

# Step 3: Compare counts for same matchups
print("\n" + "="*80)
print("MATCHUP FREQUENCY COMPARISON")
print("="*80)

discrepancies = []
for matchup in set(all_original_matchups) | set(all_boxscore_matchups):
    bdl_count = original_matchup_counts.get(matchup, 0)
    box_count = boxscore_matchup_counts.get(matchup, 0)
    
    if bdl_count != box_count:
        discrepancies.append({
            'matchup': f"{matchup[0]}@{matchup[1]}",
            'bdl': bdl_count,
            'box': box_count,
            'diff': box_count - bdl_count
        })

print(f"\nMatchups with different frequencies: {len(discrepancies)}")
if discrepancies:
    # Sort by absolute difference
    discrepancies.sort(key=lambda x: abs(x['diff']), reverse=True)
    print(f"\nTop 20 discrepancies (BDL vs Boxscore):")
    for disc in discrepancies[:20]:
        print(f"  {disc['matchup']}: BDL={disc['bdl']}, Boxscore={disc['box']}, Diff={disc['diff']:+d}")
    
    total_missing = sum(d['diff'] for d in discrepancies if d['diff'] > 0)
    total_extra = sum(d['diff'] for d in discrepancies if d['diff'] < 0)
    print(f"\nTotal games in Boxscore but not in BDL: {total_missing}")
    print(f"Total games in BDL but not in Boxscore: {abs(total_extra)}")

print("="*80)
