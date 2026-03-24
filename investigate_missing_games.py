import requests
import json

game_pks = [449187, 449246, 531548, 567304, 631471, 631472]

for game_pk in game_pks:
    print(f"\n{'='*80}")
    print(f"Investigating game_pk: {game_pk}")
    print('='*80)
    
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        game_data = data.get('gameData', {})
        live_data = data.get('liveData', {})
        
        # Game info
        status = game_data.get('status', {})
        detailed_state = status.get('detailedState', '')
        
        game_date = game_data.get('datetime', {}).get('officialDate', '')
        teams = game_data.get('teams', {})
        away_team = teams.get('away', {}).get('abbreviation', '')
        home_team = teams.get('home', {}).get('abbreviation', '')
        
        print(f"Date: {game_date}")
        print(f"Teams: {away_team} @ {home_team}")
        print(f"Status: {detailed_state}")
        
        # Check if boxscore exists
        boxscore = live_data.get('boxscore', {})
        if not boxscore:
            print("❌ No boxscore data available")
            continue
        
        # Check pitchers list
        away_pitchers = boxscore.get('teams', {}).get('away', {}).get('pitchers', [])
        home_pitchers = boxscore.get('teams', {}).get('home', {}).get('pitchers', [])
        
        print(f"Away pitchers count: {len(away_pitchers)}")
        print(f"Home pitchers count: {len(home_pitchers)}")
        
        if away_pitchers:
            print(f"Away starting pitcher ID: {away_pitchers[0]}")
        if home_pitchers:
            print(f"Home starting pitcher ID: {home_pitchers[0]}")
        
        # Check if game was postponed/suspended
        if 'Postponed' in detailed_state or 'Suspended' in detailed_state:
            print(f"⚠️ Game was {detailed_state}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
