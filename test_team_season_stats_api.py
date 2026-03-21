"""
Test script to explore the balldontlie /mlb/v1/teams/season_stats endpoint
and see if we can fetch cumulative stats up to a specific number of games played.
"""
import os
import requests
import json
from dotenv import load_dotenv
from time import sleep

# Load API key
load_dotenv()
api_key = os.getenv('BALLDONTLIE_API_KEY')

BASE_URL = "https://api.balldontlie.io/mlb/v1"
HEADERS = {"Authorization": api_key}

def test_basic_endpoint():
    """Test basic endpoint without parameters"""
    print("=" * 80)
    print("TEST 1: Basic endpoint (season 2024, no filters)")
    print("=" * 80)
    
    url = f"{BASE_URL}/teams/season_stats"
    params = {
        "season": 2024,
        "per_page": 5  # Just get a few teams for testing
    }
    
    response = requests.get(url, headers=HEADERS, params=params)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nReceived {len(data.get('data', []))} teams")
        
        if data.get('data'):
            # Show first team's data
            team = data['data'][0]
            print(f"\nSample team: {team['team']['display_name']}")
            print(f"Games played (gp): {team['gp']}")
            print(f"Batting stats - AB: {team['batting_ab']}, H: {team['batting_h']}, HR: {team['batting_hr']}")
            print(f"Pitching stats - W: {team['pitching_w']}, L: {team['pitching_l']}, ERA: {team['pitching_era']}")
    else:
        print(f"Error: {response.text}")
    
    return response

def test_with_gp_parameter():
    """Test if gp (games played) can be used as a filter parameter"""
    print("\n" + "=" * 80)
    print("TEST 2: Try filtering by gp parameter")
    print("=" * 80)
    
    url = f"{BASE_URL}/teams/season_stats"
    params = {
        "season": 2024,
        "gp": 50,  # Try to get stats for first 50 games only
        "per_page": 5
    }
    
    response = requests.get(url, headers=HEADERS, params=params)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nReceived {len(data.get('data', []))} teams")
        
        if data.get('data'):
            team = data['data'][0]
            print(f"\nSample team: {team['team']['display_name']}")
            print(f"Games played (gp): {team['gp']}")
            print(f"Batting stats - AB: {team['batting_ab']}, H: {team['batting_h']}, HR: {team['batting_hr']}")
            
            # Compare to see if stats are different from full season
            print("\nNote: If gp parameter works, these stats should be lower than full season")
    else:
        print(f"Error: {response.text}")
    
    return response

def test_team_specific():
    """Test getting stats for a specific team"""
    print("\n" + "=" * 80)
    print("TEST 3: Get stats for specific team (Padres, team_id=23)")
    print("=" * 80)
    
    url = f"{BASE_URL}/teams/season_stats"
    params = {
        "season": 2024,
        "team_ids[]": 23,  # San Diego Padres
    }
    
    response = requests.get(url, headers=HEADERS, params=params)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('data'):
            team = data['data'][0]
            print(f"\nTeam: {team['team']['display_name']}")
            print(f"Games played: {team['gp']}")
            print(f"Record: {team['pitching_w']}-{team['pitching_l']}")
            print(f"Batting AVG: {team['batting_avg']:.3f}")
            print(f"ERA: {team['pitching_era']:.3f}")
            
            print("\n" + json.dumps(team, indent=2)[:1000] + "...")  # Show first 1000 chars
    else:
        print(f"Error: {response.text}")
    
    return response

def test_date_parameter():
    """Test if there's a date parameter to get stats up to a specific date"""
    print("\n" + "=" * 80)
    print("TEST 4: Try date parameter")
    print("=" * 80)
    
    url = f"{BASE_URL}/teams/season_stats"
    params = {
        "season": 2024,
        "date": "2024-06-01",  # Try getting stats up to June 1
        "per_page": 5
    }
    
    response = requests.get(url, headers=HEADERS, params=params)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nReceived {len(data.get('data', []))} teams")
        
        if data.get('data'):
            team = data['data'][0]
            print(f"\nSample team: {team['team']['display_name']}")
            print(f"Games played: {team['gp']}")
            print("Note: If date parameter works, gp should be ~60-70 games (not 162)")
    else:
        print(f"Error: {response.text}")
    
    return response

def test_available_parameters():
    """Test various parameter combinations to discover what's available"""
    print("\n" + "=" * 80)
    print("TEST 5: Testing various parameter combinations")
    print("=" * 80)
    
    test_params = [
        {"season": 2024, "start_date": "2024-03-20"},
        {"season": 2024, "end_date": "2024-06-01"},
        {"season": 2024, "start_date": "2024-03-20", "end_date": "2024-06-01"},
        {"season": 2024, "games_played": 50},
        {"season": 2024, "max_gp": 50},
    ]
    
    for i, params in enumerate(test_params, 1):
        print(f"\n  Test 5.{i}: {params}")
        params["per_page"] = 3
        
        response = requests.get(
            f"{BASE_URL}/teams/season_stats",
            headers=HEADERS,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data'):
                team = data['data'][0]
                print(f"    ✓ Success - {team['team']['abbreviation']}: gp={team['gp']}, "
                      f"H={team['batting_h']}, W={team['pitching_w']}")
        else:
            print(f"    ✗ Failed: {response.status_code}")
        
        sleep(0.6)  # Rate limiting
    
    return None

if __name__ == "__main__":
    print("Testing balldontlie /mlb/v1/teams/season_stats endpoint\n")
    
    # Run tests with delays for rate limiting
    test_basic_endpoint()
    sleep(0.6)
    
    test_with_gp_parameter()
    sleep(0.6)
    
    test_team_specific()
    sleep(0.6)
    
    test_date_parameter()
    sleep(0.6)
    
    test_available_parameters()
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)
    print("\nKey questions to answer:")
    print("1. Does gp parameter filter stats to first N games?")
    print("2. Does date parameter give cumulative stats up to that date?")
    print("3. Are there start_date/end_date parameters for date ranges?")
    print("4. Or does the endpoint only return full season stats?")
