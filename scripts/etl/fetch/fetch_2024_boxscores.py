"""
Fetch 2024 MLB Team Boxscores
Outputs team game boxscores to: /workspaces/MLB-Model/data/2024_data/mlb_data/raw/boxscores/
Format: One CSV per date (boxscores_YYYY-MM-DD.csv)
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import os
from collections import defaultdict
import time

# Configuration for 2024 season
START_DATE = datetime(2024, 3, 20)  # 2024 season opener
END_DATE = datetime(2024, 9, 29)    # End of 2024 regular season
OUTPUT_DIR = "/workspaces/MLB-Model/data/2024_data/mlb_data/raw/boxscores"
SEASON_YEAR = 2024

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Team info cache
TEAM_INFO_CACHE = {}
TEAM_GAME_COUNTS = defaultdict(int)


def fetch_team_info():
    """Fetch all MLB team information."""
    global TEAM_INFO_CACHE
    
    if TEAM_INFO_CACHE:
        return TEAM_INFO_CACHE
    
    url = "https://statsapi.mlb.com/api/v1/teams"
    params = {"sportId": 1, "season": SEASON_YEAR}
    
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
        "sportId": 1,
        "date": date_str
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'dates' not in data or len(data['dates']) == 0:
            return []
        
        games = data['dates'][0]['games']
        # Filter for regular season only (gameType == 'R')
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


def extract_boxscore_row(game_info, boxscore_data, team_info, date_str):
    """Extract boxscore data in the required schema format."""
    
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
    
    # Increment game counts
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
    
    # Build row with exact schema
    row = {
        'game_pk': game_info.get('gamePk', ''),
        'date': date_str,
        'home_team_id': home_info.get('id', ''),
        'away_team_id': away_info.get('id', ''),
        'home_team_abbreviation': home_info.get('abbreviation', ''),
        'away_team_abbreviation': away_info.get('abbreviation', ''),
        'home_team_display_name': home_info.get('display_name', home_team_name),
        'away_team_display_name': away_info.get('display_name', away_team_name),
        'home_team_name': home_info.get('name', ''),
        'away_team_name': away_info.get('name', ''),
        'home_postseason': 0,
        'away_postseason': 0,
        'home_season_type': 'regular',
        'away_season_type': 'regular',
        'home_season': SEASON_YEAR,
        'away_season': SEASON_YEAR,
        'home_gp': TEAM_GAME_COUNTS[home_team_name],
        'away_gp': TEAM_GAME_COUNTS[away_team_name],
        'home_batting_ab': home_batting.get('atBats', 0),
        'away_batting_ab': away_batting.get('atBats', 0),
        'home_batting_r': home_batting.get('runs', 0),
        'away_batting_r': away_batting.get('runs', 0),
        'home_batting_h': home_batting.get('hits', 0),
        'away_batting_h': away_batting.get('hits', 0),
        'home_batting_2b': home_batting.get('doubles', 0),
        'away_batting_2b': away_batting.get('doubles', 0),
        'home_batting_3b': home_batting.get('triples', 0),
        'away_batting_3b': away_batting.get('triples', 0),
        'home_batting_hr': home_batting.get('homeRuns', 0),
        'away_batting_hr': away_batting.get('homeRuns', 0),
        'home_batting_rbi': home_batting.get('rbi', 0),
        'away_batting_rbi': away_batting.get('rbi', 0),
        'home_batting_tb': home_batting.get('totalBases', 0),
        'away_batting_tb': away_batting.get('totalBases', 0),
        'home_batting_bb': home_batting.get('baseOnBalls', 0),
        'away_batting_bb': away_batting.get('baseOnBalls', 0),
        'home_batting_so': home_batting.get('strikeOuts', 0),
        'away_batting_so': away_batting.get('strikeOuts', 0),
        'home_batting_sb': home_batting.get('stolenBases', 0),
        'away_batting_sb': away_batting.get('stolenBases', 0),
        'home_batting_avg': home_batting.get('avg', '.000'),
        'away_batting_avg': away_batting.get('avg', '.000'),
        'home_batting_obp': home_batting.get('obp', '.000'),
        'away_batting_obp': away_batting.get('obp', '.000'),
        'home_batting_slg': home_batting.get('slg', '.000'),
        'away_batting_slg': away_batting.get('slg', '.000'),
        'home_batting_ops': home_batting.get('ops', '.000'),
        'away_batting_ops': away_batting.get('ops', '.000'),
        'home_pitching_w': home_won,
        'away_pitching_w': away_won,
        'home_pitching_l': home_loss,
        'away_pitching_l': away_loss,
        'home_pitching_era': home_pitching.get('era', '0.00'),
        'away_pitching_era': away_pitching.get('era', '0.00'),
        'home_pitching_ip': home_pitching.get('inningsPitched', '0.0'),
        'away_pitching_ip': away_pitching.get('inningsPitched', '0.0'),
        'home_pitching_h': home_pitching.get('hits', 0),
        'away_pitching_h': away_pitching.get('hits', 0),
        'home_pitching_er': home_pitching.get('earnedRuns', 0),
        'away_pitching_er': away_pitching.get('earnedRuns', 0),
        'home_pitching_hr': home_pitching.get('homeRuns', 0),
        'away_pitching_hr': away_pitching.get('homeRuns', 0),
        'home_pitching_bb': home_pitching.get('baseOnBalls', 0),
        'away_pitching_bb': away_pitching.get('baseOnBalls', 0),
        'home_pitching_k': home_pitching.get('strikeOuts', 0),
        'away_pitching_k': away_pitching.get('strikeOuts', 0),
        'home_pitching_oba': f".{int((home_pitching.get('hits', 0) / max(home_pitching.get('atBats', 1), 1)) * 1000):03d}",
        'away_pitching_oba': f".{int((away_pitching.get('hits', 0) / max(away_pitching.get('atBats', 1), 1)) * 1000):03d}",
        'home_pitching_whip': home_pitching.get('whip', '0.00'),
        'away_pitching_whip': away_pitching.get('whip', '0.00'),
        'home_fielding_e': home_fielding.get('errors', 0),
        'away_fielding_e': away_fielding.get('errors', 0),
        'date_dt': date_str
    }
    
    return row


def process_date(date_str):
    """Process all games for a single date."""
    output_file = os.path.join(OUTPUT_DIR, f"boxscores_{date_str}.csv")
    
    # Skip if already exists
    if os.path.exists(output_file):
        print(f"  ⏭  {date_str}: Already exists, skipping")
        return True, 0
    
    # Get games for this date
    games = get_games_by_date(date_str)
    
    if not games:
        print(f"  ⚠  {date_str}: No games found")
        return False, 0
    
    print(f"  📊 {date_str}: Found {len(games)} games")
    
    # Fetch team info
    team_info = fetch_team_info()
    
    # Process each game
    rows = []
    for game in games:
        game_pk = game['gamePk']
        
        # Fetch boxscore
        boxscore = get_game_boxscore(game_pk)
        
        if not boxscore:
            continue
        
        # Extract row
        row = extract_boxscore_row(game, boxscore, team_info, date_str)
        
        if row:
            rows.append(row)
        
        # Be nice to the API
        time.sleep(0.3)
    
    if not rows:
        print(f"  ⚠  {date_str}: No boxscores extracted")
        return False, 0
    
    # Save to CSV
    df = pd.DataFrame(rows)
    df.to_csv(output_file, index=False)
    print(f"  ✅ {date_str}: Saved {len(rows)} games")
    
    return True, len(rows)


def main():
    """Main execution function."""
    print("=" * 80)
    print("FETCHING 2024 MLB TEAM BOXSCORES")
    print("=" * 80)
    print(f"Season: {SEASON_YEAR}")
    print(f"Date range: {START_DATE.date()} to {END_DATE.date()}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("-" * 80)
    
    # Fetch team info once
    fetch_team_info()
    
    # Process each date
    current_date = START_DATE
    total_games = 0
    success_count = 0
    
    while current_date <= END_DATE:
        date_str = current_date.strftime("%Y-%m-%d")
        
        success, game_count = process_date(date_str)
        
        if success:
            success_count += 1
            total_games += game_count
        
        current_date += timedelta(days=1)
        
        # Small delay between dates
        time.sleep(0.5)
    
    print("-" * 80)
    print(f"✅ Complete! Processed {success_count} dates with {total_games} total games")
    print("=" * 80)


if __name__ == "__main__":
    main()
