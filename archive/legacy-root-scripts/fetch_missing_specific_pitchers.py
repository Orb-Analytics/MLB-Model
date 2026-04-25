import requests
import pandas as pd
import os
from datetime import datetime
import time

def fetch_starting_pitcher_for_game(game_pk):
    """Fetch starting pitcher data for a specific game from MLB Stats API."""
    
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        game_data = data.get('gameData', {})
        live_data = data.get('liveData', {})
        
        # Get game info
        game_date = game_data.get('datetime', {}).get('officialDate', '')
        teams = game_data.get('teams', {})
        away_team = teams.get('away', {}).get('abbreviation', '')
        home_team = teams.get('home', {}).get('abbreviation', '')
        
        # Get starting pitchers
        boxscore = live_data.get('boxscore', {})
        away_pitcher_id = boxscore.get('teams', {}).get('away', {}).get('pitchers', [None])[0]
        home_pitcher_id = boxscore.get('teams', {}).get('home', {}).get('pitchers', [None])[0]
        
        if not away_pitcher_id or not home_pitcher_id:
            print(f"  ❌ game_pk {game_pk}: Could not find starting pitchers")
            return None
        
        # Get pitcher details from players
        players = boxscore.get('teams', {}).get('away', {}).get('players', {})
        away_pitcher_key = f'ID{away_pitcher_id}'
        away_pitcher = players.get(away_pitcher_key, {})
        away_pitcher_name = away_pitcher.get('person', {}).get('fullName', '')
        away_stats = away_pitcher.get('stats', {}).get('pitching', {})
        
        players = boxscore.get('teams', {}).get('home', {}).get('players', {})
        home_pitcher_key = f'ID{home_pitcher_id}'
        home_pitcher = players.get(home_pitcher_key, {})
        home_pitcher_name = home_pitcher.get('person', {}).get('fullName', '')
        home_stats = home_pitcher.get('stats', {}).get('pitching', {})
        
        # Create record
        record = {
            'game_pk': game_pk,
            'date': game_date,
            'away_team': away_team,
            'home_team': home_team,
            'pitcher_team': away_team,
            'opponent_team': home_team,
            'pitcher_id': away_pitcher_id,
            'pitcher_name': away_pitcher_name,
            'innings_pitched': away_stats.get('inningsPitched', 0),
            'hits': away_stats.get('hits', 0),
            'runs': away_stats.get('runs', 0),
            'earned_runs': away_stats.get('earnedRuns', 0),
            'walks': away_stats.get('baseOnBalls', 0),
            'strikeouts': away_stats.get('strikeOuts', 0),
            'home_runs': away_stats.get('homeRuns', 0),
            'pitches': away_stats.get('numberOfPitches', 0),
            'strikes': away_stats.get('strikes', 0),
        }
        
        print(f"  ✅ game_pk {game_pk}: {game_date} - {away_pitcher_name} ({away_team})")
        return record
        
    except Exception as e:
        print(f"  ❌ game_pk {game_pk}: Error - {str(e)}")
        return None

def fetch_and_save_missing_pitchers():
    """Fetch missing pitcher records and save them."""
    
    missing_games = {
        2016: [449187, 449246],
        2018: [531548],
        2019: [567304],
        2020: [631471, 631472]
    }
    
    total_fetched = 0
    
    for year, game_pks in missing_games.items():
        print(f"\n{'='*80}")
        print(f"Fetching {len(game_pks)} missing pitcher record(s) for {year}")
        print('='*80)
        
        records = []
        for game_pk in game_pks:
            record = fetch_starting_pitcher_for_game(game_pk)
            if record:
                records.append(record)
                total_fetched += 1
            time.sleep(0.5)  # Rate limiting
        
        if records:
            df = pd.DataFrame(records)
            # Group by date and save
            for date, group in df.groupby('date'):
                output_file = f'data/{year}_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_{date}.csv'
                
                if os.path.exists(output_file):
                    # Append to existing file
                    existing = pd.read_csv(output_file)
                    combined = pd.concat([existing, group], ignore_index=True)
                    combined = combined.drop_duplicates(subset=['game_pk'], keep='last')
                    combined.to_csv(output_file, index=False)
                    print(f"\n✅ Added {len(group)} record(s) to {os.path.basename(output_file)}")
                else:
                    # Create new file
                    group.to_csv(output_file, index=False)
                    print(f"\n✅ Created {os.path.basename(output_file)} with {len(group)} record(s)")
    
    print(f"\n{'='*80}")
    print(f"SUMMARY: Fetched and saved {total_fetched} pitcher record(s)")
    print('='*80)

if __name__ == "__main__":
    fetch_and_save_missing_pitchers()
