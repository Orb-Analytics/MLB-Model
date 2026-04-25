import requests
import pandas as pd
import glob
import time
import os

# The game_pks we just added
MISSING_GAMES = {
    2015: [415766],
    2016: [449187, 449246],
    2018: [531548],
    2019: [567304],
    2020: [631472, 631471],
    2021: [632457],
    2024: [746577]
}

def fetch_game_data(game_pk):
    """Fetch full game data from MLB API."""
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"      ❌ Error fetching game {game_pk}: {e}")
        return None


def extract_starting_pitcher_data(game_data, game_pk):
    """Extract starting pitcher boxscore data."""
    
    try:
        game_info = game_data.get('gameData', {})
        live_data = game_data.get('liveData', {})
        
        game_date = game_info.get('datetime', {}).get('officialDate', '')
        teams = game_info.get('teams', {})
        
        away_team = teams.get('away', {})
        home_team = teams.get('home', {})
        
        # Get starting pitchers
        players = game_info.get('players', {})
        probables = game_info.get('probablePitchers', {})
        
        away_pitcher_id = probables.get('away', {}).get('id')
        home_pitcher_id = probables.get('home', {}).get('id')
        
        # Get pitcher stats from boxscore
        box_score = live_data.get('boxscore', {})
        away_pitchers = box_score.get('teams', {}).get('away', {}).get('players', {})
        home_pitchers = box_score.get('teams', {}).get('home', {}).get('players', {})
        
        rows = []
        
        # Process away starting pitcher
        if away_pitcher_id:
            pitcher_key = f'ID{away_pitcher_id}'
            if pitcher_key in away_pitchers:
                pitcher_data = away_pitchers[pitcher_key]
                pitcher_stats = pitcher_data.get('stats', {}).get('pitching', {})
                pitcher_info = players.get(pitcher_key, {})
                
                row = {
                    'game_pk': game_pk,
                    'date': game_date,
                    'pitcher_id': away_pitcher_id,
                    'pitcher_name': pitcher_info.get('fullName', ''),
                    'team_id': away_team.get('id'),
                    'team_abbreviation': away_team.get('abbreviation', ''),
                    'opponent_id': home_team.get('id'),
                    'opponent_abbreviation': home_team.get('abbreviation', ''),
                    'home_away': 'away',
                    'win': pitcher_stats.get('wins', 0),
                    'loss': pitcher_stats.get('losses', 0),
                    'save': pitcher_stats.get('saves', 0),
                    'ip': pitcher_stats.get('inningsPitched', '0.0'),
                    'h': pitcher_stats.get('hits', 0),
                    'r': pitcher_stats.get('runs', 0),
                    'er': pitcher_stats.get('earnedRuns', 0),
                    'bb': pitcher_stats.get('baseOnBalls', 0),
                    'so': pitcher_stats.get('strikeOuts', 0),
                    'hr': pitcher_stats.get('homeRuns', 0),
                    'era': pitcher_stats.get('era', '0.00'),
                    'pitches': pitcher_stats.get('numberOfPitches', 0),
                    'strikes': pitcher_stats.get('strikes', 0),
                    'date_dt': game_date
                }
                rows.append(row)
        
        # Process home starting pitcher
        if home_pitcher_id:
            pitcher_key = f'ID{home_pitcher_id}'
            if pitcher_key in home_pitchers:
                pitcher_data = home_pitchers[pitcher_key]
                pitcher_stats = pitcher_data.get('stats', {}).get('pitching', {})
                pitcher_info = players.get(pitcher_key, {})
                
                row = {
                    'game_pk': game_pk,
                    'date': game_date,
                    'pitcher_id': home_pitcher_id,
                    'pitcher_name': pitcher_info.get('fullName', ''),
                    'team_id': home_team.get('id'),
                    'team_abbreviation': home_team.get('abbreviation', ''),
                    'opponent_id': away_team.get('id'),
                    'opponent_abbreviation': away_team.get('abbreviation', ''),
                    'home_away': 'home',
                    'win': pitcher_stats.get('wins', 0),
                    'loss': pitcher_stats.get('losses', 0),
                    'save': pitcher_stats.get('saves', 0),
                    'ip': pitcher_stats.get('inningsPitched', '0.0'),
                    'h': pitcher_stats.get('hits', 0),
                    'r': pitcher_stats.get('runs', 0),
                    'er': pitcher_stats.get('earnedRuns', 0),
                    'bb': pitcher_stats.get('baseOnBalls', 0),
                    'so': pitcher_stats.get('strikeOuts', 0),
                    'hr': pitcher_stats.get('homeRuns', 0),
                    'era': pitcher_stats.get('era', '0.00'),
                    'pitches': pitcher_stats.get('numberOfPitches', 0),
                    'strikes': pitcher_stats.get('strikes', 0),
                    'date_dt': game_date
                }
                rows.append(row)
        
        return rows
        
    except Exception as e:
        print(f"      ❌ Error extracting pitcher data for game {game_pk}: {e}")
        return []


# Main execution
print("="*80)
print("FETCHING STARTING PITCHER BOXSCORES FOR MISSING GAMES")
print("="*80)

total_added = 0

for year, game_pks in MISSING_GAMES.items():
    print(f"\n{'='*80}")
    print(f"YEAR {year}")
    print('='*80)
    
    pitcher_path = f'data/{year}_data/mlb_data/raw/starting_pitcher_boxscores'
    
    for game_pk in game_pks:
        print(f"\n  Fetching starting pitcher data for game {game_pk}...")
        
        # Fetch game data
        game_data = fetch_game_data(game_pk)
        if not game_data:
            print(f"    ❌ Failed to fetch game data")
            continue
        
        # Extract pitcher data
        pitcher_rows = extract_starting_pitcher_data(game_data, game_pk)
        
        if not pitcher_rows:
            print(f"    ⚠️  No starting pitcher data found")
            continue
        
        # Get the date from first row
        date = pitcher_rows[0]['date']
        file_path = f'{pitcher_path}/starting_pitcher_boxscores_{date}.csv'
        
        # Add to file
        if os.path.exists(file_path):
            df_existing = pd.read_csv(file_path)
            df_new = pd.DataFrame(pitcher_rows)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.to_csv(file_path, index=False)
            print(f"    ✅ Added {len(pitcher_rows)} pitcher(s) to existing file")
        else:
            df_new = pd.DataFrame(pitcher_rows)
            df_new.to_csv(file_path, index=False)
            print(f"    ✅ Created new file with {len(pitcher_rows)} pitcher(s)")
        
        total_added += len(pitcher_rows)
        time.sleep(0.5)

print(f"\n{'='*80}")
print(f"COMPLETE: Added {total_added} starting pitcher records")
print('='*80)
