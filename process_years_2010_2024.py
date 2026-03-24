import pandas as pd
import glob
import os
from collections import defaultdict
from datetime import datetime, timedelta

# Team abbreviation mapping (historical)
ABBR_MAPPING = {
    'ARI': 'AZ',
    'CHW': 'CWS',
    'MIA': 'FLA'  # Florida Marlins until 2011, Miami Marlins from 2012+
}

def apply_abbr_mapping(team_abbr, year):
    """Apply historical team abbreviation mapping based on year"""
    if pd.isna(team_abbr):
        return team_abbr
    
    team_str = str(team_abbr).strip()
    
    # Special case: MIA/FLA transition in 2012
    if year < 2012 and team_str == 'MIA':
        return 'FLA'
    
    return ABBR_MAPPING.get(team_str, team_str)

def process_year(year):
    """Process a single year using the same approach as 2009"""
    
    print("="*80)
    print(f"PROCESSING YEAR {year}")
    print("="*80)
    
    base_path = f'data/{year}_data/mlb_data/raw'
    outlook_path = f'{base_path}/bdl_data/game_outlook'
    boxscore_path = f'{base_path}/boxscores'
    pitcher_path = f'{base_path}/starting_pitcher_boxscores'
    
    # Check if files exist
    outlook_files = glob.glob(f'{outlook_path}/game_outlook_*.csv')
    boxscore_files = glob.glob(f'{boxscore_path}/boxscores_*.csv')
    pitcher_files = glob.glob(f'{pitcher_path}/starting_pitcher_boxscores_*.csv')
    
    if not outlook_files:
        print(f"  ⚠️  No game outlook files found for {year}")
        return False
    
    if not boxscore_files:
        print(f"  ⚠️  No boxscore files found for {year}")
        return False
    
    print(f"\n  Found:")
    print(f"    Outlook files: {len(outlook_files)}")
    print(f"    Boxscore files: {len(boxscore_files)}")
    print(f"    Pitcher files: {len(pitcher_files)}")
    
    # Create backup
    print(f"\n  Creating backup...")
    backup_path = f'{outlook_path}/backup_original_{year}'
    os.makedirs(backup_path, exist_ok=True)
    os.system(f'cp {outlook_path}/game_outlook_*.csv {backup_path}/ 2>/dev/null')
    print(f"    ✓ Backed up to {backup_path}")
    
    # Step 1: Load boxscore structure (the source of truth)
    print(f"\n  Step 1: Loading boxscore structure...")
    correct_structure = defaultdict(list)
    all_boxscore_games = 0
    
    for file in sorted(boxscore_files):
        date = file.split('_')[-1].replace('.csv', '')
        df = pd.read_csv(file)
        all_boxscore_games += len(df)
        
        for position, row in df.iterrows():
            correct_structure[date].append({
                'position': position,
                'game_pk': int(row['game_pk']),
                'away_team': row['away_team_abbreviation'],
                'home_team': row['home_team_abbreviation']
            })
    
    print(f"    {len(correct_structure)} dates, {all_boxscore_games} games")
    
    # Step 2: Load all outlook games and index by matchup
    print(f"\n  Step 2: Loading outlook games...")
    all_outlook_games = {}  # (away, home) -> list of game_row dicts
    outlook_count = 0
    
    for file in sorted(outlook_files):
        df = pd.read_csv(file)
        
        # Apply team abbreviation mapping
        df['away_team_abbreviation'] = df['away_team_abbreviation'].apply(
            lambda x: apply_abbr_mapping(x, year)
        )
        df['home_team_abbreviation'] = df['home_team_abbreviation'].apply(
            lambda x: apply_abbr_mapping(x, year)
        )
        
        for _, row in df.iterrows():
            away = row['away_team_abbreviation']
            home = row['home_team_abbreviation']
            matchup = (away, home)
            
            if matchup not in all_outlook_games:
                all_outlook_games[matchup] = []
            
            all_outlook_games[matchup].append(row.to_dict())
            outlook_count += 1
    
    print(f"    {outlook_count} total games, {len(all_outlook_games)} unique matchups")
    
    # Step 3: Rebuild outlook files to match boxscore structure
    print(f"\n  Step 3: Rebuilding outlook files to match boxscore...")
    new_outlook_data = {}
    matched_games = 0
    missing_games = []
    
    # Track which outlook games we've used (to handle duplicates)
    used_outlook_games = defaultdict(int)
    
    for date, games_list in sorted(correct_structure.items()):
        date_games = []
        
        for game_info in games_list:
            matchup = (game_info['away_team'], game_info['home_team'])
            
            if matchup in all_outlook_games:
                # Get the next available instance of this matchup
                instance_idx = used_outlook_games[matchup]
                
                if instance_idx < len(all_outlook_games[matchup]):
                    game_row = all_outlook_games[matchup][instance_idx].copy()
                    game_row['game_pk'] = game_info['game_pk']
                    date_games.append(game_row)
                    matched_games += 1
                    used_outlook_games[matchup] += 1
                else:
                    missing_games.append(f"{date}: {matchup[0]}@{matchup[1]} (game_pk {game_info['game_pk']})")
            else:
                missing_games.append(f"{date}: {matchup[0]}@{matchup[1]} (game_pk {game_info['game_pk']})")
        
        if date_games:
            new_outlook_data[date] = pd.DataFrame(date_games)
    
    print(f"    Matched: {matched_games}/{all_boxscore_games} games")
    if missing_games:
        print(f"    Missing: {len(missing_games)} games")
        if len(missing_games) <= 5:
            for msg in missing_games:
                print(f"      - {msg}")
    
    # Step 4: Save new outlook files
    print(f"\n  Step 4: Saving aligned outlook files...")
    for date, df in new_outlook_data.items():
        file_path = f'{outlook_path}/game_outlook_{date}.csv'
        df.to_csv(file_path, index=False)
    print(f"    Saved {len(new_outlook_data)} files")
    
    # Step 5: Verify alignment
    print(f"\n  Step 5: Verifying alignment...")
    perfect_dates = 0
    position_matches = 0
    total_checked = 0
    
    for date, correct_games in sorted(correct_structure.items()):
        if date in new_outlook_data:
            outlook_df = new_outlook_data[date]
            
            if len(correct_games) != len(outlook_df):
                continue
            
            date_perfect = True
            for i, game_info in enumerate(correct_games):
                total_checked += 1
                out_pk = outlook_df.iloc[i]['game_pk']
                
                if pd.notna(out_pk) and int(out_pk) == game_info['game_pk']:
                    position_matches += 1
                else:
                    date_perfect = False
            
            if date_perfect:
                perfect_dates += 1
    
    alignment_pct = 100 * position_matches / total_checked if total_checked > 0 else 0
    print(f"    Perfect dates: {perfect_dates}/{len(correct_structure)} ({100*perfect_dates/len(correct_structure):.1f}%)")
    print(f"    Position matches: {position_matches}/{total_checked} ({alignment_pct:.1f}%)")
    
    if perfect_dates == len(correct_structure):
        print(f"  ✅ {year} - PERFECT ALIGNMENT!")
        return True
    else:
        print(f"  ⚠️  {year} - Partial alignment ({alignment_pct:.1f}%)")
        return False

# Main execution
print("\n" + "="*80)
print("PROCESSING YEARS 2010-2024")
print("="*80)

years_to_process = range(2010, 2025)
results = {}

for year in years_to_process:
    success = process_year(year)
    results[year] = success
    print()

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

successful = [y for y, s in results.items() if s]
partial = [y for y, s in results.items() if not s]

print(f"\nSuccessful (100% alignment): {len(successful)} years")
for year in successful:
    print(f"  ✓ {year}")

if partial:
    print(f"\nPartial alignment: {len(partial)} years")
    for year in partial:
        print(f"  ⚠ {year}")

print("="*80)
