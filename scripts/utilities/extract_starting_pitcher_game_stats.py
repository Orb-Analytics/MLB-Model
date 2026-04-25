"""
Extract Individual Starting Pitcher Game Performance from MLB Stats API

Purpose:
    Fetch individual starting pitcher stats for each game (IP, H, R, ER, BB, K, HR, etc.)
    This gives us the actual per-game performance to compare against cumulative stats.
"""

import requests
import pandas as pd
import json
import os
from datetime import datetime

MLB_STATS_API = "https://statsapi.mlb.com/api/v1"


def get_game_boxscore_json(game_pk):
    """
    Fetch the full boxscore JSON from MLB API.
    
    Args:
        game_pk: MLB game ID
    
    Returns:
        dict: Full boxscore JSON data
    """
    url = f"{MLB_STATS_API}/game/{game_pk}/boxscore"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching game {game_pk}: {e}")
        return None


def extract_starting_pitcher_stats(boxscore_data, game_pk, game_date):
    """
    Extract starting pitcher individual game stats from boxscore.
    
    Args:
        boxscore_data: Full boxscore JSON
        game_pk: Game ID
        game_date: Game date
    
    Returns:
        dict: Starting pitcher stats for both teams
    """
    if not boxscore_data or 'teams' not in boxscore_data:
        return None
    
    teams = boxscore_data['teams']
    
    # Structure to hold both starters
    starter_stats = {
        'game_pk': game_pk,
        'date': game_date,
        'home_starter': None,
        'away_starter': None
    }
    
    # Extract for both home and away
    for side in ['home', 'away']:
        team_data = teams[side]
        
        # Get pitcher IDs and player data
        pitcher_ids = team_data.get('pitchers', [])
        players = team_data.get('players', {})
        
        if not pitcher_ids:
            continue
        
        # Starting pitcher is typically the first in the list
        # We can also check the 'note' field or battingOrder
        starter_id = pitcher_ids[0]  # First pitcher listed
        starter_key = f"ID{starter_id}"
        
        if starter_key not in players:
            continue
        
        starter_data = players[starter_key]
        person = starter_data.get('person', {})
        pitching_stats = starter_data.get('stats', {}).get('pitching', {})
        
        # Extract comprehensive game stats
        game_stats = {
            'player_id': person.get('id'),
            'player_name': person.get('fullName'),
            'team_id': team_data.get('team', {}).get('id'),
            'team_name': team_data.get('team', {}).get('name'),
            
            # Pitching stats
            'ip': pitching_stats.get('inningsPitched', 0),
            'hits': pitching_stats.get('hits', 0),
            'runs': pitching_stats.get('runs', 0),
            'earned_runs': pitching_stats.get('earnedRuns', 0),
            'walks': pitching_stats.get('baseOnBalls', 0),
            'strikeouts': pitching_stats.get('strikeOuts', 0),
            'homeruns': pitching_stats.get('homeRuns', 0),
            
            'era': pitching_stats.get('era', 0),
            'whip': pitching_stats.get('whip', 0),
            
            'pitches': pitching_stats.get('numberOfPitches', 0),
            'strikes': pitching_stats.get('strikes', 0),
            
            'hit_batters': pitching_stats.get('hitBatsmen', 0),
            'wild_pitches': pitching_stats.get('wildPitches', 0),
            'balks': pitching_stats.get('balks', 0),
            
            'batters_faced': pitching_stats.get('battersFaced', 0),
            'ground_outs': pitching_stats.get('groundOuts', 0),
            'air_outs': pitching_stats.get('airOuts', 0),
            
            # Game context
            'win': pitching_stats.get('wins', 0),
            'loss': pitching_stats.get('losses', 0),
            'save': pitching_stats.get('saves', 0),
            'blown_save': pitching_stats.get('blownSaves', 0),
            'hold': pitching_stats.get('holds', 0),
        }
        
        starter_stats[f'{side}_starter'] = game_stats
    
    return starter_stats


def test_single_game(game_pk, game_date=None):
    """
    Test extraction on a single game.
    
    Args:
        game_pk: MLB game ID
        game_date: Optional game date (for display)
    """
    print(f"\n{'='*80}")
    print(f"Testing Starting Pitcher Stats Extraction")
    print(f"Game PK: {game_pk}")
    if game_date:
        print(f"Date: {game_date}")
    print(f"{'='*80}\n")
    
    # Fetch boxscore
    print("Fetching boxscore from MLB API...")
    boxscore = get_game_boxscore_json(game_pk)
    
    if not boxscore:
        print("❌ Failed to fetch boxscore")
        return None
    
    print("✓ Boxscore fetched successfully\n")
    
    # Save raw JSON for inspection
    json_file = f"test_boxscore_{game_pk}.json"
    with open(json_file, 'w') as f:
        json.dump(boxscore, f, indent=2)
    print(f"✓ Saved raw boxscore: {json_file}\n")
    
    # Extract starting pitcher stats
    print("Extracting starting pitcher stats...")
    starters = extract_starting_pitcher_stats(boxscore, game_pk, game_date)
    
    if not starters:
        print("❌ Failed to extract starter stats")
        return None
    
    print("✓ Extraction successful\n")
    
    # Display results
    print("="*80)
    print("AWAY STARTING PITCHER")
    print("="*80)
    if starters['away_starter']:
        away = starters['away_starter']
        print(f"Name: {away['player_name']}")
        print(f"Player ID: {away['player_id']}")
        print(f"Team: {away['team_name']}\n")
        print("Game Stats:")
        print(f"  IP: {away['ip']}")
        print(f"  H: {away['hits']}")
        print(f"  R: {away['runs']}")
        print(f"  ER: {away['earned_runs']}")
        print(f"  BB: {away['walks']}")
        print(f"  K: {away['strikeouts']}")
        print(f"  HR: {away['homeruns']}")
        print(f"  Pitches: {away['pitches']} ({away['strikes']} strikes)")
        print(f"  ERA: {away['era']}")
        print(f"  WHIP: {away['whip']}")
    else:
        print("No away starter found")
    
    print("\n" + "="*80)
    print("HOME STARTING PITCHER")
    print("="*80)
    if starters['home_starter']:
        home = starters['home_starter']
        print(f"Name: {home['player_name']}")
        print(f"Player ID: {home['player_id']}")
        print(f"Team: {home['team_name']}\n")
        print("Game Stats:")
        print(f"  IP: {home['ip']}")
        print(f"  H: {home['hits']}")
        print(f"  R: {home['runs']}")
        print(f"  ER: {home['earned_runs']}")
        print(f"  BB: {home['walks']}")
        print(f"  K: {home['strikeouts']}")
        print(f"  HR: {home['homeruns']}")
        print(f"  Pitches: {home['pitches']} ({home['strikes']} strikes)")
        print(f"  ERA: {home['era']}")
        print(f"  WHIP: {home['whip']}")
    else:
        print("No home starter found")
    
    print("\n" + "="*80)
    print("SUCCESS! ✓")
    print("="*80)
    print("\nAvailable Stats per Starting Pitcher:")
    print("- Basic: IP, H, R, ER, BB, K, HR")
    print("- Advanced: ERA, WHIP, Pitches, Strikes")
    print("- Outcomes: W, L, Save, Blown Save, Hold")
    print("- Additional: HBP, Wild Pitches, Balks, Batters Faced, GO, AO")
    
    return starters


if __name__ == "__main__":
    # Test on first game of 2025 season
    # Cubs vs Dodgers, March 18, 2025, Tokyo Dome
    # From our dataset: game_pk = 778563 (this is balldontlie ID, need to find MLB game_pk)
    
    # Let me try the Cubs-Dodgers game
    # We'll need to search for the actual MLB game_pk
    print("Testing Starting Pitcher Game Stats Extraction")
    print("\nNote: Need to provide actual MLB game_pk.")
    print("The game IDs in our dataset (like 778563) are balldontlie IDs.")
    print("\nTo test, we need to:")
    print("1. Search for games on March 18, 2025")
    print("2. Find the Cubs vs Dodgers game")
    print("3. Get its MLB game_pk")
    print("4. Then fetch the boxscore")
    
    # For now, let's try a known game_pk if available
    # (Can be found by searching the schedule API)
