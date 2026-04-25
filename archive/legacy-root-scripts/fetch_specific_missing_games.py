import requests
import pandas as pd
import glob
import time
import os
from collections import defaultdict

def get_missing_games(year):
    """
    Compare local data with MLB API to find missing game_pks.
    Returns list of missing games with their details.
    """
    
    # Load local boxscore game_pks
    boxscore_path = f'data/{year}_data/mlb_data/raw/boxscores'
    boxscore_files = sorted(glob.glob(f'{boxscore_path}/boxscores_*.csv'))
    
    local_games = set()
    for file in boxscore_files:
        df = pd.read_csv(file)
        local_games.update(df['game_pk'].astype(int).tolist())
    
    # Query MLB API
    if year == 2020:
        start_date = f"{year}-07-23"
        end_date = f"{year}-09-27"
    else:
        start_date = f"{year}-03-20"
        end_date = f"{year}-11-10"
    
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={start_date}&endDate={end_date}"
    response = requests.get(url, timeout=30)
    
    if response.status_code != 200:
        return []
    
    data = response.json()
    
    # Find all regular season games from API
    api_games = {}  # {game_pk: {date, teams, etc}}
    
    for date_entry in data.get('dates', []):
        date = date_entry.get('date')
        games = date_entry.get('games', [])
        
        for game in games:
            if game.get('gameType') == 'R':  # Regular season only
                game_pk = game.get('gamePk')
                if game_pk:
                    teams = game.get('teams', {})
                    api_games[game_pk] = {
                        'game_pk': game_pk,
                        'date': date,
                        'away_team': teams.get('away', {}).get('team', {}).get('name', 'Unknown'),
                        'home_team': teams.get('home', {}).get('team', {}).get('name', 'Unknown'),
                        'status': game.get('status', {}).get('detailedState', 'Unknown')
                    }
    
    # Find missing games
    missing = []
    for game_pk, details in api_games.items():
        if game_pk not in local_games:
            missing.append(details)
    
    return missing


def fetch_game_boxscore(game_pk):
    """Fetch detailed boxscore for a specific game from MLB API."""
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"      ❌ Failed to fetch game {game_pk} (status {response.status_code})")
            return None
    except Exception as e:
        print(f"      ❌ Error fetching game {game_pk}: {e}")
        return None


def extract_boxscore_data(game_data, game_pk):
    """Extract boxscore data from MLB API response."""
    
    try:
        game_info = game_data.get('gameData', {})
        live_data = game_data.get('liveData', {})
        
        # Basic game info
        game_date = game_info.get('datetime', {}).get('officialDate', '')
        teams = game_info.get('teams', {})
        
        away_team = teams.get('away', {})
        home_team = teams.get('home', {})
        
        # Box score stats
        box_score = live_data.get('boxscore', {})
        away_stats = box_score.get('teams', {}).get('away', {}).get('teamStats', {})
        home_stats = box_score.get('teams', {}).get('home', {}).get('teamStats', {})
        
        # Build boxscore row
        boxscore_row = {
            'game_pk': game_pk,
            'date': game_date,
            'home_team_id': home_team.get('id'),
            'away_team_id': away_team.get('id'),
            'home_team_abbreviation': home_team.get('abbreviation', ''),
            'away_team_abbreviation': away_team.get('abbreviation', ''),
            'home_team_display_name': home_team.get('name', ''),
            'away_team_display_name': away_team.get('name', ''),
            'home_team_name': home_team.get('teamName', ''),
            'away_team_name': away_team.get('teamName', ''),
            'home_postseason': 0,
            'away_postseason': 0,
            'home_season_type': 'regular',
            'away_season_type': 'regular',
            'home_season': game_date.split('-')[0],
            'away_season': game_date.split('-')[0],
            'home_gp': 1,
            'away_gp': 1,
        }
        
        # Add batting stats
        batting_keys = ['ab', 'r', 'h', '2b', '3b', 'hr', 'rbi', 'tb', 'bb', 'so', 'sb', 'avg', 'obp', 'slg', 'ops']
        for key in batting_keys:
            boxscore_row[f'home_batting_{key}'] = home_stats.get('batting', {}).get(key, 0)
            boxscore_row[f'away_batting_{key}'] = away_stats.get('batting', {}).get(key, 0)
        
        # Add pitching stats
        pitching_keys = ['w', 'l', 'era', 'ip', 'h', 'er', 'hr', 'bb', 'k', 'oba', 'whip']
        for key in pitching_keys:
            boxscore_row[f'home_pitching_{key}'] = home_stats.get('pitching', {}).get(key, 0)
            boxscore_row[f'away_pitching_{key}'] = away_stats.get('pitching', {}).get(key, 0)
        
        # Add fielding stats
        boxscore_row['home_fielding_e'] = home_stats.get('fielding', {}).get('errors', 0)
        boxscore_row['away_fielding_e'] = away_stats.get('fielding', {}).get('errors', 0)
        
        boxscore_row['date_dt'] = game_date
        
        return boxscore_row
        
    except Exception as e:
        print(f"      ❌ Error extracting data for game {game_pk}: {e}")
        return None


def add_games_to_files(year, games_to_add):
    """Add missing games to the appropriate date files."""
    
    boxscore_path = f'data/{year}_data/mlb_data/raw/boxscores'
    added_count = 0
    
    for game_info in games_to_add:
        game_pk = game_info['game_pk']
        date = game_info['date']
        
        print(f"  Fetching game {game_pk} ({game_info['away_team']} @ {game_info['home_team']}) on {date}...")
        
        # Fetch game data
        game_data = fetch_game_boxscore(game_pk)
        if not game_data:
            continue
        
        # Extract boxscore
        boxscore_row = extract_boxscore_data(game_data, game_pk)
        if not boxscore_row:
            continue
        
        # Add to appropriate file
        file_path = f'{boxscore_path}/boxscores_{date}.csv'
        
        if os.path.exists(file_path):
            # Append to existing file
            df_existing = pd.read_csv(file_path)
            df_new = pd.DataFrame([boxscore_row])
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.to_csv(file_path, index=False)
            print(f"    ✅ Added to existing file")
        else:
            # Create new file
            df_new = pd.DataFrame([boxscore_row])
            df_new.to_csv(file_path, index=False)
            print(f"    ✅ Created new file")
        
        added_count += 1
        time.sleep(0.5)  # Be nice to API
    
    return added_count


# Main execution
print("="*80)
print("FETCHING MISSING GAMES")
print("="*80)

years_to_check = [2015, 2016, 2018, 2019, 2020, 2021, 2024]
total_added = 0

for year in years_to_check:
    print(f"\n{'='*80}")
    print(f"YEAR {year}")
    print('='*80)
    
    print(f"\n  Step 1: Identifying missing games...")
    missing = get_missing_games(year)
    
    if not missing:
        print(f"    ✓ No missing games found!")
        continue
    
    print(f"    Found {len(missing)} missing game(s):")
    for game in missing:
        print(f"      - game_pk {game['game_pk']}: {game['away_team']} @ {game['home_team']} on {game['date']}")
    
    print(f"\n  Step 2: Fetching and adding missing games...")
    added = add_games_to_files(year, missing)
    total_added += added
    
    print(f"\n  ✅ Added {added} game(s) to {year}")

print(f"\n{'='*80}")
print(f"COMPLETE: Added {total_added} total games")
print('='*80)
