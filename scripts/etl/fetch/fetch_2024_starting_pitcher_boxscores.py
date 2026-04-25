"""
Fetch 2024 MLB Starting Pitcher Boxscores
Outputs starting pitcher boxscores to: /workspaces/MLB-Model/data/2024_data/mlb_data/raw/starting_pitcher_boxscores/
Format: One CSV per date (starting_pitcher_boxscores_YYYY-MM-DD.csv)
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import time
from pathlib import Path

# Configuration for 2024 season
START_DATE = datetime(2024, 3, 20)  # 2024 season opener
END_DATE = datetime(2024, 9, 29)    # End of 2024 regular season
BOXSCORES_DIR = Path("/workspaces/MLB-Model/data/2024_data/mlb_data/raw/boxscores")
OUTPUT_DIR = Path("/workspaces/MLB-Model/data/2024_data/mlb_data/raw/starting_pitcher_boxscores")
SEASON_YEAR = 2024

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MLB_STATS_API = "https://statsapi.mlb.com/api/v1"


def get_game_boxscore_json(game_pk):
    """Fetch the full boxscore JSON from MLB API."""
    url = f"{MLB_STATS_API}/game/{game_pk}/boxscore"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"    ❌ Error fetching game {game_pk}: {e}")
        return None


def extract_starting_pitcher_stats(boxscore_data):
    """Extract starting pitcher stats from boxscore."""
    if not boxscore_data or 'teams' not in boxscore_data:
        return None
    
    teams = boxscore_data['teams']
    pitcher_stats = {}
    
    for side in ['home', 'away']:
        team_data = teams[side]
        pitcher_ids = team_data.get('pitchers', [])
        players = team_data.get('players', {})
        
        if not pitcher_ids:
            continue
        
        # Starting pitcher is first in the list
        starter_id = pitcher_ids[0]
        starter_key = f"ID{starter_id}"
        
        if starter_key not in players:
            continue
        
        starter_data = players[starter_key]
        person = starter_data.get('person', {})
        stats = starter_data.get('stats', {}).get('pitching', {})
        
        pitcher_stats[side] = {
            'id': person.get('id'),
            'name': person.get('fullName'),
            'team': team_data.get('team', {}).get('name'),
            'ip': stats.get('inningsPitched', 0),
            'hits': stats.get('hits', 0),
            'runs': stats.get('runs', 0),
            'earned_runs': stats.get('earnedRuns', 0),
            'walks': stats.get('baseOnBalls', 0),
            'strikeouts': stats.get('strikeOuts', 0),
            'homeruns': stats.get('homeRuns', 0),
            'era': stats.get('era', 0),
            'whip': stats.get('whip', 0),
            'pitches': stats.get('numberOfPitches', 0),
            'strikes': stats.get('strikes', 0),
            'hit_batters': stats.get('hitBatsmen', 0),
            'wild_pitches': stats.get('wildPitches', 0),
            'balks': stats.get('balks', 0),
            'batters_faced': stats.get('battersFaced', 0),
            'ground_outs': stats.get('groundOuts', 0),
            'air_outs': stats.get('airOuts', 0),
            'wins': stats.get('wins', 0),
            'losses': stats.get('losses', 0),
            'saves': stats.get('saves', 0),
            'blown_saves': stats.get('blownSaves', 0),
            'holds': stats.get('holds', 0),
        }
    
    return pitcher_stats


def create_starting_pitcher_row(game_pk, date_str, pitcher_stats):
    """Create single row with exact column structure."""
    if not pitcher_stats or 'home' not in pitcher_stats or 'away' not in pitcher_stats:
        return None
    
    home = pitcher_stats['home']
    away = pitcher_stats['away']
    
    row = {
        'game_pk': game_pk,
        'date': date_str,
        'home_starter_id': home['id'],
        'away_starter_id': away['id'],
        'home_starter_name': home['name'],
        'away_starter_name': away['name'],
        'home_starter_team': home['team'],
        'away_starter_team': away['team'],
        'home_starter_ip': home['ip'],
        'away_starter_ip': away['ip'],
        'home_starter_hits': home['hits'],
        'away_starter_hits': away['hits'],
        'home_starter_runs': home['runs'],
        'away_starter_runs': away['runs'],
        'home_starter_earned_runs': home['earned_runs'],
        'away_starter_earned_runs': away['earned_runs'],
        'home_starter_walks': home['walks'],
        'away_starter_walks': away['walks'],
        'home_starter_strikeouts': home['strikeouts'],
        'away_starter_strikeouts': away['strikeouts'],
        'home_starter_homeruns': home['homeruns'],
        'away_starter_homeruns': away['homeruns'],
        'home_starter_era': home['era'],
        'away_starter_era': away['era'],
        'home_starter_whip': home['whip'],
        'away_starter_whip': away['whip'],
        'home_starter_pitches': home['pitches'],
        'away_starter_pitches': away['pitches'],
        'home_starter_strikes': home['strikes'],
        'away_starter_strikes': away['strikes'],
        'home_starter_hit_batters': home['hit_batters'],
        'away_starter_hit_batters': away['hit_batters'],
        'home_starter_wild_pitches': home['wild_pitches'],
        'away_starter_wild_pitches': away['wild_pitches'],
        'home_starter_balks': home['balks'],
        'away_starter_balks': away['balks'],
        'home_starter_batters_faced': home['batters_faced'],
        'away_starter_batters_faced': away['batters_faced'],
        'home_starter_ground_outs': home['ground_outs'],
        'away_starter_ground_outs': away['ground_outs'],
        'home_starter_air_outs': home['air_outs'],
        'away_starter_air_outs': away['air_outs'],
        'home_starter_wins': home['wins'],
        'away_starter_wins': away['wins'],
        'home_starter_losses': home['losses'],
        'away_starter_losses': away['losses'],
        'home_starter_saves': home['saves'],
        'away_starter_saves': away['saves'],
        'home_starter_blown_saves': home['blown_saves'],
        'away_starter_blown_saves': away['blown_saves'],
        'home_starter_holds': home['holds'],
        'away_starter_holds': away['holds'],
    }
    
    return row


def process_date(date_str):
    """Process starting pitchers for all games on a single date."""
    output_file = OUTPUT_DIR / f"starting_pitcher_boxscores_{date_str}.csv"
    
    # Skip if already exists
    if output_file.exists():
        print(f"  ⏭  {date_str}: Already exists, skipping")
        return True, 0
    
    # Check if team boxscores exist for this date
    boxscores_file = BOXSCORES_DIR / f"boxscores_{date_str}.csv"
    
    if not boxscores_file.exists():
        print(f"  ⚠  {date_str}: No boxscores file found")
        return False, 0
    
    # Read team boxscores to get game IDs
    try:
        team_df = pd.read_csv(boxscores_file)
    except Exception as e:
        print(f"  ❌ {date_str}: Error reading boxscores - {e}")
        return False, 0
    
    if team_df.empty:
        print(f"  ⚠  {date_str}: Empty boxscores file")
        return False, 0
    
    print(f"  📊 {date_str}: Processing {len(team_df)} games")
    
    # Collect starting pitcher stats
    all_rows = []
    
    for idx, game_row in team_df.iterrows():
        game_pk = game_row['game_pk']
        
        # Fetch boxscore
        boxscore = get_game_boxscore_json(game_pk)
        
        if not boxscore:
            continue
        
        # Extract starting pitcher stats
        pitcher_stats = extract_starting_pitcher_stats(boxscore)
        
        if not pitcher_stats or 'home' not in pitcher_stats or 'away' not in pitcher_stats:
            print(f"    ⚠ Game {game_pk}: Could not extract starters")
            continue
        
        # Create row
        row = create_starting_pitcher_row(game_pk, date_str, pitcher_stats)
        
        if row:
            all_rows.append(row)
        
        # Be nice to the API
        time.sleep(0.3)
    
    if not all_rows:
        print(f"  ⚠  {date_str}: No starter data extracted")
        return False, 0
    
    # Save to CSV
    df = pd.DataFrame(all_rows)
    df.to_csv(output_file, index=False)
    print(f"  ✅ {date_str}: Saved {len(all_rows)} games")
    
    return True, len(all_rows)


def main():
    """Main execution function."""
    print("=" * 80)
    print("FETCHING 2024 MLB STARTING PITCHER BOXSCORES")
    print("=" * 80)
    print(f"Season: {SEASON_YEAR}")
    print(f"Date range: {START_DATE.date()} to {END_DATE.date()}")
    print(f"Input directory: {BOXSCORES_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("-" * 80)
    
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
