import requests
import pandas as pd
import glob
import os
from datetime import datetime

def verify_and_fetch_year(year):
    """
    Verify boxscore data for a year. 
    Check if we have all games by comparing against MLB schedule API.
    Only re-fetch if data is missing or incomplete.
    """
    
    print("="*80)
    print(f"YEAR {year}")
    print("="*80)
    
    # Paths
    base_path = f'data/{year}_data/mlb_data/raw'
    boxscore_path = f'{base_path}/boxscores'
    pitcher_path = f'{base_path}/starting_pitcher_boxscores'
    
    # Step 1: Check what we have locally
    print(f"\n  Step 1: Checking local files...")
    
    boxscore_files = glob.glob(f'{boxscore_path}/boxscores_*.csv')
    pitcher_files = glob.glob(f'{pitcher_path}/starting_pitcher_boxscores_*.csv')
    
    if boxscore_files:
        local_box_games = sum(len(pd.read_csv(f)) for f in boxscore_files)
        local_box_dates = len(boxscore_files)
        print(f"    Boxscores: {local_box_games} games across {local_box_dates} dates")
    else:
        local_box_games = 0
        local_box_dates = 0
        print(f"    Boxscores: No files found")
    
    if pitcher_files:
        local_pitch_games = sum(len(pd.read_csv(f)) for f in pitcher_files)
        local_pitch_dates = len(pitcher_files)
        print(f"    Starting Pitcher: {local_pitch_games} games across {local_pitch_dates} dates")
    else:
        local_pitch_games = 0
        local_pitch_dates = 0
        print(f"    Starting Pitcher: No files found")
    
    # Step 2: Query MLB API for actual season schedule
    print(f"\n  Step 2: Querying MLB API for season schedule...")
    
    try:
        # Get season dates
        if year == 2020:
            start_date = f"{year}-07-23"  # COVID shortened season
            end_date = f"{year}-09-27"
        else:
            start_date = f"{year}-03-20"
            end_date = f"{year}-11-10"
        
        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={start_date}&endDate={end_date}"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Count ONLY regular season games (exclude postseason)
            api_game_count = 0
            api_date_count = 0
            
            for date_entry in data.get('dates', []):
                games = date_entry.get('games', [])
                regular_season_games = [g for g in games if g.get('gameType') == 'R']
                if regular_season_games:
                    api_date_count += 1
                    api_game_count += len(regular_season_games)
            
            print(f"    MLB API reports: {api_game_count} games across {api_date_count} dates")
            
            # Step 3: Compare
            print(f"\n  Step 3: Comparison...")
            
            # Check boxscores
            if local_box_games >= api_game_count:
                print(f"    ✅ Boxscores COMPLETE ({local_box_games} >= {api_game_count})")
                box_status = "COMPLETE"
            else:
                diff = api_game_count - local_box_games
                print(f"    ⚠️  Boxscores INCOMPLETE ({local_box_games} < {api_game_count}, missing {diff})")
                box_status = "INCOMPLETE"
            
            # Check starting pitcher boxscores
            if local_pitch_games >= api_game_count:
                print(f"    ✅ Starting Pitcher COMPLETE ({local_pitch_games} >= {api_game_count})")
                pitch_status = "COMPLETE"
            else:
                diff = api_game_count - local_pitch_games
                print(f"    ⚠️  Starting Pitcher INCOMPLETE ({local_pitch_games} < {api_game_count}, missing {diff})")
                pitch_status = "INCOMPLETE"
            
            # Check if counts match each other
            if local_box_games == local_pitch_games:
                print(f"    ✅ Boxscore and Pitcher counts MATCH")
            else:
                print(f"    ⚠️  Boxscore ({local_box_games}) and Pitcher ({local_pitch_games}) counts DON'T MATCH")
            
            return {
                'year': year,
                'boxscore_status': box_status,
                'pitcher_status': pitch_status,
                'local_box_games': local_box_games,
                'local_pitch_games': local_pitch_games,
                'api_game_count': api_game_count,
                'needs_refetch': box_status == "INCOMPLETE" or pitch_status == "INCOMPLETE"
            }
            
        else:
            print(f"    ❌ Failed to query MLB API (status {response.status_code})")
            return {
                'year': year,
                'boxscore_status': 'UNKNOWN',
                'pitcher_status': 'UNKNOWN',
                'local_box_games': local_box_games,
                'local_pitch_games': local_pitch_games,
                'api_game_count': None,
                'needs_refetch': False
            }
            
    except Exception as e:
        print(f"    ❌ Error querying MLB API: {e}")
        return {
            'year': year,
            'boxscore_status': 'ERROR',
            'pitcher_status': 'ERROR',
            'local_box_games': local_box_games,
            'local_pitch_games': local_pitch_games,
            'api_game_count': None,
            'needs_refetch': False
        }

# Main execution
print("\n" + "="*80)
print("VERIFYING BOXSCORE DATA FOR YEARS 2011-2024")
print("="*80 + "\n")

results = []

for year in range(2011, 2025):
    result = verify_and_fetch_year(year)
    results.append(result)
    print()

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80 + "\n")

complete_years = [r for r in results if r['boxscore_status'] == 'COMPLETE' and r['pitcher_status'] == 'COMPLETE']
incomplete_years = [r for r in results if r.get('needs_refetch', False)]

print(f"✅ Complete Years: {len(complete_years)}")
for r in complete_years:
    print(f"   {r['year']}: {r['local_box_games']} games (API: {r['api_game_count']})")

if incomplete_years:
    print(f"\n⚠️  Incomplete Years: {len(incomplete_years)}")
    for r in incomplete_years:
        print(f"   {r['year']}: Local {r['local_box_games']}, API {r['api_game_count']}")
    print(f"\n   These years would need to be re-fetched.")
else:
    print(f"\n🎉 All years have complete data!")

print("\n" + "="*80)
