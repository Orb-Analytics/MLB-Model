import requests
import pandas as pd
import glob
import time
from collections import defaultdict

def verify_year_game_pks(year):
    """
    Verify a year's boxscore data by comparing game_pk and date against MLB API.
    Returns detailed report of matches, mismatches, and missing games.
    """
    
    print("="*80)
    print(f"VERIFYING YEAR {year}: game_pk and date validation")
    print("="*80)
    
    # Step 1: Load local boxscore game_pks and dates
    print(f"\n  Step 1: Loading local boxscore data...")
    boxscore_path = f'data/{year}_data/mlb_data/raw/boxscores'
    boxscore_files = sorted(glob.glob(f'{boxscore_path}/boxscores_*.csv'))
    
    local_games = {}  # {game_pk: date}
    local_by_date = defaultdict(list)  # {date: [game_pks]}
    
    for file in boxscore_files:
        date = file.split('_')[-1].replace('.csv', '')
        df = pd.read_csv(file)
        
        for _, row in df.iterrows():
            game_pk = int(row['game_pk'])
            local_games[game_pk] = date
            local_by_date[date].append(game_pk)
    
    print(f"    Local data: {len(local_games)} games across {len(local_by_date)} dates")
    
    # Step 2: Query MLB API for season schedule
    print(f"\n  Step 2: Querying MLB API for season schedule...")
    
    try:
        # Set season date range
        if year == 2020:
            start_date = f"{year}-07-23"
            end_date = f"{year}-09-27"
        else:
            start_date = f"{year}-03-20"
            end_date = f"{year}-11-10"
        
        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={start_date}&endDate={end_date}"
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            print(f"    ❌ Failed to query MLB API (status {response.status_code})")
            return None
        
        data = response.json()
        
        # Extract all regular season games
        api_games = {}  # {game_pk: date}
        api_by_date = defaultdict(list)  # {date: [game_pks]}
        
        for date_entry in data.get('dates', []):
            date = date_entry.get('date')
            games = date_entry.get('games', [])
            
            for game in games:
                if game.get('gameType') == 'R':  # Regular season only
                    game_pk = game.get('gamePk')
                    if game_pk:
                        api_games[game_pk] = date
                        api_by_date[date].append(game_pk)
        
        print(f"    MLB API: {len(api_games)} regular season games across {len(api_by_date)} dates")
        
        # Step 3: Compare game_pk and date pairs
        print(f"\n  Step 3: Comparing game_pk and date pairs...")
        
        # Find matches
        matching_games = set(local_games.keys()) & set(api_games.keys())
        
        # Check if dates match for matching game_pks
        date_matches = 0
        date_mismatches = []
        
        for game_pk in matching_games:
            if local_games[game_pk] == api_games[game_pk]:
                date_matches += 1
            else:
                date_mismatches.append({
                    'game_pk': game_pk,
                    'local_date': local_games[game_pk],
                    'api_date': api_games[game_pk]
                })
        
        # Find games only in local
        local_only = set(local_games.keys()) - set(api_games.keys())
        
        # Find games only in API (missing from local)
        api_only = set(api_games.keys()) - set(local_games.keys())
        
        # Step 4: Report results
        print(f"\n  Step 4: Results:")
        print(f"    ✅ Matching game_pks: {len(matching_games)}")
        print(f"       - Date matches: {date_matches}")
        print(f"       - Date mismatches: {len(date_mismatches)}")
        
        if date_mismatches and len(date_mismatches) <= 10:
            print(f"\n    Date mismatches details:")
            for mismatch in date_mismatches:
                print(f"      game_pk {mismatch['game_pk']}: local={mismatch['local_date']}, api={mismatch['api_date']}")
        
        if local_only:
            print(f"\n    ⚠️  Games in local but not in API: {len(local_only)}")
            if len(local_only) <= 10:
                for game_pk in sorted(local_only):
                    print(f"      game_pk {game_pk} on {local_games[game_pk]}")
        
        if api_only:
            print(f"\n    ⚠️  Games in API but missing from local: {len(api_only)}")
            if len(api_only) <= 10:
                for game_pk in sorted(api_only):
                    print(f"      game_pk {game_pk} on {api_games[game_pk]}")
        
        # Calculate accuracy
        total_expected = len(api_games)
        perfect_matches = date_matches
        accuracy = (perfect_matches / total_expected * 100) if total_expected > 0 else 0
        
        print(f"\n  📊 Summary:")
        print(f"    Accuracy: {accuracy:.2f}% ({perfect_matches}/{total_expected} perfect matches)")
        print(f"    Status: {'✅ PASS' if accuracy >= 99.0 else '⚠️  NEEDS REVIEW'}")
        
        return {
            'year': year,
            'total_local': len(local_games),
            'total_api': len(api_games),
            'matching_pks': len(matching_games),
            'date_matches': date_matches,
            'date_mismatches': len(date_mismatches),
            'local_only': len(local_only),
            'api_only': len(api_only),
            'accuracy': accuracy,
            'status': 'PASS' if accuracy >= 99.0 else 'REVIEW'
        }
        
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return None

# Main execution
print("\n" + "="*80)
print("VALIDATING BOXSCORE DATA: game_pk and date verification")
print("="*80 + "\n")

results = []

for year in range(2010, 2025):
    result = verify_year_game_pks(year)
    if result:
        results.append(result)
    print()
    time.sleep(1)  # Be nice to MLB API

# Final Summary
print("\n" + "="*80)
print("FINAL SUMMARY")
print("="*80 + "\n")

if results:
    passed = [r for r in results if r['status'] == 'PASS']
    review = [r for r in results if r['status'] == 'REVIEW']
    
    print(f"✅ PASSED: {len(passed)} years")
    for r in passed:
        print(f"   {r['year']}: {r['accuracy']:.2f}% accuracy ({r['date_matches']}/{r['total_api']} games)")
    
    if review:
        print(f"\n⚠️  NEEDS REVIEW: {len(review)} years")
        for r in review:
            print(f"   {r['year']}: {r['accuracy']:.2f}% accuracy ({r['date_matches']}/{r['total_api']} games)")
            print(f"      Missing: {r['api_only']}, Extra: {r['local_only']}, Date mismatches: {r['date_mismatches']}")

print("\n" + "="*80)
