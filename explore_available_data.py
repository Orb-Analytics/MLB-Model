"""
Explore all available data from balldontlie API for building a training set
Test using one game to see what data we can actually retrieve
"""
import requests
import time
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
API_KEY = os.getenv("BALLDONTLIE_API_KEY")
BASE_URL = "https://api.balldontlie.io/mlb/v1"

def fetch_with_retry(url, params=None, max_retries=3):
    """Fetch data with retry logic"""
    headers = {"Authorization": API_KEY}
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limit
                wait_time = 2 ** attempt
                print(f"  Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"  Error {response.status_code}: {response.text[:200]}")
                return None
        except Exception as e:
            print(f"  Exception: {e}")
            time.sleep(1)
    
    return None

def explore_game_data(game_date, away_team, home_team):
    """Explore all available data for a specific game"""
    
    print(f"\n{'='*80}")
    print(f"EXPLORING DATA FOR: {game_date} - {away_team} @ {home_team}")
    print(f"{'='*80}\n")
    
    # 1. Get game info
    print("1. GAME INFORMATION")
    print("-" * 80)
    game_data = fetch_with_retry(f"{BASE_URL}/games", {"dates[]": game_date})
    
    if not game_data or not game_data.get('data'):
        print("  ✗ Could not fetch game data")
        return
    
    # Find our specific game
    game = None
    for g in game_data['data']:
        if g['visitor_team']['abbreviation'] == away_team and g['home_team']['abbreviation'] == home_team:
            game = g
            break
    
    if not game:
        print(f"  ✗ Game not found")
        return
    
    game_id = game['id']
    print(f"  ✓ Game ID: {game_id}")
    print(f"  ✓ Status: {game.get('status', 'N/A')}")
    print(f"  ✓ Final Score: {away_team} {game['visitor_team_score']} @ {home_team} {game['home_team_score']}")
    
    # Extract interesting fields from game object
    print(f"\n  Available game-level fields:")
    for key in sorted(game.keys()):
        if key not in ['id', 'visitor_team', 'home_team', 'visitor_team_score', 'home_team_score']:
            value = game[key]
            if value and value != {}:
                print(f"    - {key}: {value}")
    
    time.sleep(0.5)
    
    # 2. Get plate appearances (for starting pitchers)
    print("\n2. STARTING PITCHERS (from plate appearances)")
    print("-" * 80)
    pa_data = fetch_with_retry(f"{BASE_URL}/plate_appearances", {"game_id": game_id, "per_page": 100})
    
    if pa_data and pa_data.get('data'):
        plate_appearances = pa_data['data']
        print(f"  ✓ Retrieved {len(plate_appearances)} plate appearances")
        
        # Find starters
        away_starter_id = None
        home_starter_id = None
        
        for pa in plate_appearances:
            if pa['inning'] == 1:
                if pa['half_inning'] == 'bottom' and not away_starter_id:
                    away_starter_id = pa['pitcher_id']
                elif pa['half_inning'] == 'top' and not home_starter_id:
                    home_starter_id = pa['pitcher_id']
        
        # Get pitcher details
        starters = {}
        for label, pitcher_id in [("Away", away_starter_id), ("Home", home_starter_id)]:
            if pitcher_id:
                player_data = fetch_with_retry(f"{BASE_URL}/players/{pitcher_id}")
                if player_data and player_data.get('data'):
                    player = player_data['data']
                    starters[label] = player
                    print(f"  ✓ {label} Starter: {player['full_name']} (ID: {pitcher_id})")
                    print(f"    Position: {player.get('position', 'N/A')}")
                    print(f"    Team: {player.get('team', {}).get('full_name', 'N/A')}")
                time.sleep(0.3)
        
        # Show interesting PA fields
        if plate_appearances:
            pa = plate_appearances[0]
            print(f"\n  Available plate appearance fields:")
            for key in sorted(pa.keys()):
                if key not in ['id', 'game_id', 'batter_id', 'pitcher_id']:
                    print(f"    - {key}")
    else:
        print("  ✗ Could not fetch plate appearances")
    
    time.sleep(0.5)
    
    # 3. Get player season stats (for starters)
    print("\n3. PITCHER SEASON STATS")
    print("-" * 80)
    
    if away_starter_id and home_starter_id:
        stats_data = fetch_with_retry(
            f"{BASE_URL}/season_stats",
            {"player_ids[]": [away_starter_id, home_starter_id], "season": 2025}
        )
        
        if stats_data and stats_data.get('data'):
            print(f"  ✓ Retrieved stats for {len(stats_data['data'])} records")
            
            for stat_record in stats_data['data']:
                player_id = stat_record.get('player_id')
                stat_type = stat_record.get('stat_type')
                
                if stat_type == 'pitching':
                    pitcher_name = starters.get("Away" if player_id == away_starter_id else "Home", {}).get('full_name', f'ID {player_id}')
                    print(f"\n  {pitcher_name} (Pitching Stats):")
                    
                    # List all available pitching stats
                    for key in sorted(stat_record.keys()):
                        if key not in ['id', 'player_id', 'season', 'stat_type', 'season_type']:
                            value = stat_record.get(key)
                            if value is not None and value != '':
                                print(f"    - {key}: {value}")
        else:
            print("  ✗ Could not fetch player stats")
    
    time.sleep(0.5)
    
    # 4. Get team season stats
    print("\n4. TEAM SEASON STATS")
    print("-" * 80)
    
    away_team_id = game['visitor_team']['id']
    home_team_id = game['home_team']['id']
    
    team_stats_data = fetch_with_retry(
        f"{BASE_URL}/teams/season_stats",
        {"team_ids[]": [away_team_id, home_team_id], "season": 2025}
    )
    
    if team_stats_data and team_stats_data.get('data'):
        print(f"  ✓ Retrieved stats for {len(team_stats_data['data'])} team records")
        
        for team_record in team_stats_data['data']:
            team_id = team_record.get('team_id')
            season_type = team_record.get('season_type', 'N/A')
            
            if season_type == 'regular':
                team_name = away_team if team_id == away_team_id else home_team
                print(f"\n  {team_name} Team Stats (Regular Season):")
                
                # Organize by category
                pitching_stats = []
                batting_stats = []
                fielding_stats = []
                
                for key in sorted(team_record.keys()):
                    if key not in ['id', 'team_id', 'season', 'season_type']:
                        value = team_record.get(key)
                        if value is not None and value != '':
                            if key.startswith('pitching_'):
                                pitching_stats.append(f"    - {key}: {value}")
                            elif key.startswith('batting_'):
                                batting_stats.append(f"    - {key}: {value}")
                            elif key.startswith('fielding_'):
                                fielding_stats.append(f"    - {key}: {value}")
                            else:
                                print(f"    - {key}: {value}")
                
                if pitching_stats:
                    print("\n  Pitching Stats:")
                    for stat in pitching_stats[:15]:  # Show first 15
                        print(stat)
                    if len(pitching_stats) > 15:
                        print(f"    ... and {len(pitching_stats) - 15} more pitching stats")
                
                if batting_stats:
                    print("\n  Batting Stats:")
                    for stat in batting_stats[:15]:  # Show first 15
                        print(stat)
                    if len(batting_stats) > 15:
                        print(f"    ... and {len(batting_stats) - 15} more batting stats")
                
                if fielding_stats:
                    print("\n  Fielding Stats:")
                    for stat in fielding_stats[:10]:
                        print(stat)
                    if len(fielding_stats) > 10:
                        print(f"    ... and {len(fielding_stats) - 10} more fielding stats")
    else:
        print("  ✗ Could not fetch team stats")
    
    time.sleep(0.5)
    
    # 5. Check for game stats endpoint
    print("\n5. GAME-LEVEL STATS (if available)")
    print("-" * 80)
    
    game_stats_data = fetch_with_retry(f"{BASE_URL}/stats", {"game_id": game_id, "per_page": 100})
    
    if game_stats_data and game_stats_data.get('data'):
        print(f"  ✓ Retrieved {len(game_stats_data['data'])} player game stats")
        
        # Group by stat type
        pitching_count = sum(1 for s in game_stats_data['data'] if s.get('stat_type') == 'pitching')
        batting_count = sum(1 for s in game_stats_data['data'] if s.get('stat_type') == 'batting')
        
        print(f"    - Pitching records: {pitching_count}")
        print(f"    - Batting records: {batting_count}")
        
        # Show sample fields from a pitching stat
        pitching_stats = [s for s in game_stats_data['data'] if s.get('stat_type') == 'pitching']
        if pitching_stats:
            sample = pitching_stats[0]
            print(f"\n  Sample pitching game stat fields:")
            for key in sorted(sample.keys()):
                if key not in ['id', 'player_id', 'game_id']:
                    print(f"    - {key}")
    else:
        print("  ℹ Game-level stats endpoint not available or no data")
    
    # 6. Summary
    print(f"\n{'='*80}")
    print("SUMMARY OF AVAILABLE DATA")
    print(f"{'='*80}")
    print("""
✓ GAME INFO: Date, teams, scores, status
✓ STARTING PITCHERS: Names, positions, team affiliations
✓ PITCHER SEASON STATS: ERA, WHIP, IP, K, BB, wins, losses, etc (FULL SEASON)
✓ TEAM SEASON STATS: Pitching + Batting metrics (FULL SEASON)
✓ GAME-LEVEL STATS: Individual player stats for specific game (if endpoint exists)
✓ PLATE APPEARANCE DATA: Detailed play-by-play for each at-bat

⚠ LIMITATION: Season stats appear to be FULL SEASON totals, not filtered by date
⚠ No historical odds data available from this API
    """)

if __name__ == "__main__":
    # Test with the same game we've been using
    explore_game_data("2025-08-16", "SEA", "NYM")
