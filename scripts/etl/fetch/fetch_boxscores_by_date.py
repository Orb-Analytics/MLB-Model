"""
Fetch MLB box scores and organize by date with specific schema.
Outputs to /workspaces/MLB-Model/data/bdl_data/boxscores/
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import json
import time
from collections import defaultdict

# Configuration
START_DATE = datetime(2025, 3, 18)  # First game of 2025 season
END_DATE = datetime(2025, 9, 29)    # End of regular season
OUTPUT_BASE_DIR = "/workspaces/MLB-Model/data/bdl_data/boxscores"

# Create output directory
os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)

# Cache for team information
TEAM_INFO_CACHE = {}
TEAM_GAME_COUNTS = defaultdict(int)  # Track games played per team


def fetch_team_info():
    """Fetch all MLB team information including IDs and abbreviations."""
    global TEAM_INFO_CACHE
    
    if TEAM_INFO_CACHE:
        return TEAM_INFO_CACHE
    
    url = "https://statsapi.mlb.com/api/v1/teams"
    params = {"sportId": 1, "season": 2025}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        for team in data.get('teams', []):
            team_name = team['name']
            TEAM_INFO_CACHE[team_name] = {
                'id': team['id'],
                'abbreviation': team.get('abbreviation', ''),
                'display_name': team['name'],
                'name': team.get('teamName', ''),
                'location': team.get('locationName', '')
            }
        
        print(f"✅ Loaded info for {len(TEAM_INFO_CACHE)} teams")
        return TEAM_INFO_CACHE
    
    except Exception as e:
        print(f"❌ Error fetching team info: {e}")
        return {}


def get_games_by_date(date_str):
    """Fetch all MLB games for a specific date."""
    url = "https://statsapi.mlb.com/api/v1/schedule"
    params = {
        "sportId": 1,  # MLB
        "date": date_str
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'dates' not in data or len(data['dates']) == 0:
            return []
        
        games = data['dates'][0]['games']
        # Filter for regular season only
        regular_season_games = [g for g in games if g.get('gameType') == 'R']
        return regular_season_games
    
    except Exception as e:
        print(f"   ❌ Error fetching games for {date_str}: {e}")
        return []


def get_game_boxscore(game_pk):
    """Fetch detailed boxscore for a specific game."""
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    
    except Exception as e:
        print(f"      ❌ Error fetching boxscore for game {game_pk}: {e}")
        return None


def calculate_opponent_batting_avg(pitching_stats):
    """Calculate opponent batting average (OBA) for pitching."""
    hits = pitching_stats.get('hits', 0)
    at_bats = pitching_stats.get('atBats', 0)
    
    if at_bats == 0:
        return '.000'
    
    oba = hits / at_bats
    return f'.{int(oba * 1000):03d}'


def extract_boxscore_row(game_info, boxscore_data, team_info):
    """Extract box score data in the required schema format."""
    
    if not boxscore_data or 'teams' not in boxscore_data:
        return None
    
    teams = boxscore_data['teams']
    away_team = teams['away']
    home_team = teams['home']
    
    # Get team names
    away_team_name = away_team['team']['name']
    home_team_name = home_team['team']['name']
    
    # Get team info from cache
    away_info = team_info.get(away_team_name, {})
    home_info = team_info.get(home_team_name, {})
    
    # Increment game counts for these teams
    TEAM_GAME_COUNTS[away_team_name] += 1
    TEAM_GAME_COUNTS[home_team_name] += 1
    
    # Extract stats
    away_batting = away_team['teamStats']['batting']
    home_batting = home_team['teamStats']['batting']
    away_pitching = away_team['teamStats']['pitching']
    home_pitching = home_team['teamStats']['pitching']
    away_fielding = away_team['teamStats']['fielding']
    home_fielding = home_team['teamStats']['fielding']
    
    # Determine winner for W/L
    away_runs = away_batting.get('runs', 0)
    home_runs = home_batting.get('runs', 0)
    home_won = 1 if home_runs > away_runs else 0
    away_won = 1 if away_runs > home_runs else 0
    home_loss = 1 if away_runs > home_runs else 0
    away_loss = 1 if home_runs > away_runs else 0
    
    # Build the row with exact schema
    row = {
        # Game Identifiers
        'id': game_info.get('gamePk', ''),
        'date': game_info.get('officialDate', ''),
        
        # Home Team Info
        'home_team_id': home_info.get('id', ''),
        'home_team_abbreviation': home_info.get('abbreviation', ''),
        'home_team_display_name': home_info.get('display_name', home_team_name),
        'home_team_name': home_info.get('name', ''),
        
        # Away Team Info
        'away_team_id': away_info.get('id', ''),
        'away_team_abbreviation': away_info.get('abbreviation', ''),
        'away_team_display_name': away_info.get('display_name', away_team_name),
        'away_team_name': away_info.get('name', ''),
        
        # Season Info
        'home_postseason': 0,  # Regular season
        'away_postseason': 0,
        'home_season_type': 'regular',
        'away_season_type': 'regular',
        'home_season': 2025,
        'away_season': 2025,
        'home_gp': TEAM_GAME_COUNTS[home_team_name],
        'away_gp': TEAM_GAME_COUNTS[away_team_name],
        
        # Home Team Batting
        'home_batting_ab': home_batting.get('atBats', 0),
        'home_batting_r': home_batting.get('runs', 0),
        'home_batting_h': home_batting.get('hits', 0),
        'home_batting_2b': home_batting.get('doubles', 0),
        'home_batting_3b': home_batting.get('triples', 0),
        'home_batting_hr': home_batting.get('homeRuns', 0),
        'home_batting_rbi': home_batting.get('rbi', 0),
        'home_batting_tb': home_batting.get('totalBases', 0),
        'home_batting_bb': home_batting.get('baseOnBalls', 0),
        'home_batting_so': home_batting.get('strikeOuts', 0),
        'home_batting_sb': home_batting.get('stolenBases', 0),
        'home_batting_avg': home_batting.get('avg', '.000'),
        'home_batting_obp': home_batting.get('obp', '.000'),
        'home_batting_slg': home_batting.get('slg', '.000'),
        'home_batting_ops': home_batting.get('ops', '.000'),
        
        # Away Team Batting
        'away_batting_ab': away_batting.get('atBats', 0),
        'away_batting_r': away_batting.get('runs', 0),
        'away_batting_h': away_batting.get('hits', 0),
        'away_batting_2b': away_batting.get('doubles', 0),
        'away_batting_3b': away_batting.get('triples', 0),
        'away_batting_hr': away_batting.get('homeRuns', 0),
        'away_batting_rbi': away_batting.get('rbi', 0),
        'away_batting_tb': away_batting.get('totalBases', 0),
        'away_batting_bb': away_batting.get('baseOnBalls', 0),
        'away_batting_so': away_batting.get('strikeOuts', 0),
        'away_batting_sb': away_batting.get('stolenBases', 0),
        'away_batting_avg': away_batting.get('avg', '.000'),
        'away_batting_obp': away_batting.get('obp', '.000'),
        'away_batting_slg': away_batting.get('slg', '.000'),
        'away_batting_ops': away_batting.get('ops', '.000'),
        
        # Home Team Pitching
        'home_pitching_w': home_won,
        'home_pitching_l': home_loss,
        'home_pitching_era': home_pitching.get('era', '0.00'),
        'home_pitching_ip': home_pitching.get('inningsPitched', '0.0'),
        'home_pitching_h': home_pitching.get('hits', 0),
        'home_pitching_er': home_pitching.get('earnedRuns', 0),
        'home_pitching_hr': home_pitching.get('homeRuns', 0),
        'home_pitching_bb': home_pitching.get('baseOnBalls', 0),
        'home_pitching_k': home_pitching.get('strikeOuts', 0),
        'home_pitching_oba': calculate_opponent_batting_avg(home_pitching),
        'home_pitching_whip': home_pitching.get('whip', '0.00'),
        
        # Away Team Pitching
        'away_pitching_w': away_won,
        'away_pitching_l': away_loss,
        'away_pitching_era': away_pitching.get('era', '0.00'),
        'away_pitching_ip': away_pitching.get('inningsPitched', '0.0'),
        'away_pitching_h': away_pitching.get('hits', 0),
        'away_pitching_er': away_pitching.get('earnedRuns', 0),
        'away_pitching_hr': away_pitching.get('homeRuns', 0),
        'away_pitching_bb': away_pitching.get('baseOnBalls', 0),
        'away_pitching_k': away_pitching.get('strikeOuts', 0),
        'away_pitching_oba': calculate_opponent_batting_avg(away_pitching),
        'away_pitching_whip': away_pitching.get('whip', '0.00'),
        
        # Home Team Fielding
        'home_fielding_e': home_fielding.get('errors', 0),
        
        # Away Team Fielding
        'away_fielding_e': away_fielding.get('errors', 0),
    }
    
    return row


def main():
    """Main execution function."""
    print("=" * 80)
    print("MLB Box Score Fetcher - Organized by Date")
    print("=" * 80)
    print(f"Date Range: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    print(f"Output Directory: {OUTPUT_BASE_DIR}")
    print("=" * 80)
    print()
    
    # Fetch team information first
    print("📋 Fetching team information...")
    team_info = fetch_team_info()
    
    if not team_info:
        print("❌ Failed to fetch team information. Exiting.")
        return
    
    print()
    
    # Dictionary to store games by date
    games_by_date = defaultdict(list)
    
    total_games = 0
    successful_games = 0
    failed_games = 0
    
    # Loop through each date
    current_date = START_DATE
    while current_date <= END_DATE:
        date_str = current_date.strftime("%Y-%m-%d")
        print(f"📅 Processing {date_str}...")
        
        # Get games for this date
        games = get_games_by_date(date_str)
        
        if not games:
            print(f"   No regular season games found")
            current_date += timedelta(days=1)
            continue
        
        print(f"   Found {len(games)} regular season game(s)")
        
        # Process each game
        for game in games:
            game_pk = game['gamePk']
            away_team = game['teams']['away']['team']['name']
            home_team = game['teams']['home']['team']['name']
            total_games += 1
            
            print(f"   🏟️  Game {game_pk}: {away_team} @ {home_team}")
            
            # Fetch boxscore
            boxscore_data = get_game_boxscore(game_pk)
            
            if not boxscore_data:
                print(f"      ❌ Failed to fetch boxscore")
                failed_games += 1
                continue
            
            # Extract stats in required format
            row = extract_boxscore_row(game, boxscore_data, team_info)
            
            if not row:
                print(f"      ❌ Failed to extract stats")
                failed_games += 1
                continue
            
            # Add to games for this date
            games_by_date[date_str].append(row)
            successful_games += 1
            
            score = f"{row['away_batting_r']}-{row['home_batting_r']}"
            print(f"      ✅ Score: {score}")
            
            # Small delay to be respectful to API
            time.sleep(0.5)
        
        current_date += timedelta(days=1)
    
    # Save games by date
    print("\n" + "=" * 80)
    print("💾 Saving CSV files organized by date...")
    print("=" * 80)
    
    saved_files = 0
    for date_str, game_rows in sorted(games_by_date.items()):
        if not game_rows:
            continue
        
        # Create DataFrame
        df = pd.DataFrame(game_rows)
        
        # Ensure all required columns are present in correct order
        required_columns = [
            'id', 'date',
            'home_team_id', 'away_team_id',
            'home_team_abbreviation', 'away_team_abbreviation',
            'home_team_display_name', 'away_team_display_name',
            'home_team_name', 'away_team_name',
            'home_postseason', 'away_postseason',
            'home_season_type', 'away_season_type',
            'home_season', 'away_season',
            'home_gp', 'away_gp',
            'home_batting_ab', 'away_batting_ab',
            'home_batting_r', 'away_batting_r',
            'home_batting_h', 'away_batting_h',
            'home_batting_2b', 'away_batting_2b',
            'home_batting_3b', 'away_batting_3b',
            'home_batting_hr', 'away_batting_hr',
            'home_batting_rbi', 'away_batting_rbi',
            'home_batting_tb', 'away_batting_tb',
            'home_batting_bb', 'away_batting_bb',
            'home_batting_so', 'away_batting_so',
            'home_batting_sb', 'away_batting_sb',
            'home_batting_avg', 'away_batting_avg',
            'home_batting_obp', 'away_batting_obp',
            'home_batting_slg', 'away_batting_slg',
            'home_batting_ops', 'away_batting_ops',
            'home_pitching_w', 'away_pitching_w',
            'home_pitching_l', 'away_pitching_l',
            'home_pitching_era', 'away_pitching_era',
            'home_pitching_ip', 'away_pitching_ip',
            'home_pitching_h', 'away_pitching_h',
            'home_pitching_er', 'away_pitching_er',
            'home_pitching_hr', 'away_pitching_hr',
            'home_pitching_bb', 'away_pitching_bb',
            'home_pitching_k', 'away_pitching_k',
            'home_pitching_oba', 'away_pitching_oba',
            'home_pitching_whip', 'away_pitching_whip',
            'home_fielding_e', 'away_fielding_e'
        ]
        
        # Reorder columns
        df = df[required_columns]
        
        # Save to CSV
        output_path = os.path.join(OUTPUT_BASE_DIR, f"boxscores_{date_str}.csv")
        df.to_csv(output_path, index=False)
        
        print(f"✅ {date_str}: Saved {len(game_rows)} game(s) to {output_path}")
        saved_files += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("📈 SUMMARY")
    print("=" * 80)
    print(f"Total games found:     {total_games}")
    print(f"Successfully fetched:  {successful_games}")
    print(f"Failed:                {failed_games}")
    print(f"Success rate:          {successful_games/total_games*100:.1f}%" if total_games > 0 else "N/A")
    print(f"Files saved:           {saved_files}")
    print(f"Output directory:      {OUTPUT_BASE_DIR}")
    print("\n" + "=" * 80)
    
    # Show sample
    if games_by_date:
        first_date = sorted(games_by_date.keys())[0]
        first_game = games_by_date[first_date][0]
        
        print("\n📋 SAMPLE: First Game")
        print("=" * 80)
        print(f"Date:          {first_game['date']}")
        print(f"Game ID:       {first_game['id']}")
        print(f"Away Team:     {first_game['away_team_display_name']} ({first_game['away_team_abbreviation']})")
        print(f"Home Team:     {first_game['home_team_display_name']} ({first_game['home_team_abbreviation']})")
        print(f"Score:         {first_game['away_batting_r']}-{first_game['home_batting_r']}")
        print(f"Total Columns: {len(required_columns)}")
        print("=" * 80)


if __name__ == "__main__":
    main()
