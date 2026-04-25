"""
Fetch all March 2025 regular season game box scores from MLB Stats API.
Creates both individual game CSVs and a combined master CSV.
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import json
import time

# Configuration
START_DATE = datetime(2025, 3, 1)
END_DATE = datetime(2025, 3, 31)
OUTPUT_DIR = "data/mlb_stats_boxscores/march_2025"
MASTER_CSV = "data/mlb_stats_boxscores/march_2025_master.csv"

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("data/mlb_stats_boxscores", exist_ok=True)


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
        print(f"Error fetching games for {date_str}: {e}")
        return []


def get_game_boxscore(game_pk):
    """Fetch detailed boxscore for a specific game."""
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    
    except Exception as e:
        print(f"Error fetching boxscore for game {game_pk}: {e}")
        return None


def extract_team_boxscore(game_info, boxscore_data):
    """Extract team-level statistics from boxscore."""
    
    if not boxscore_data or 'teams' not in boxscore_data:
        return None
    
    teams = boxscore_data['teams']
    away_team = teams['away']
    home_team = teams['home']
    
    # Extract basic game info
    game_date = game_info.get('officialDate', '')
    game_pk = game_info.get('gamePk', '')
    venue = game_info.get('venue', {}).get('name', '')
    
    # Extract team names
    away_team_name = away_team['team']['name']
    home_team_name = home_team['team']['name']
    
    # Extract batting stats
    away_batting = away_team['teamStats']['batting']
    home_batting = home_team['teamStats']['batting']
    
    # Extract pitching stats
    away_pitching = away_team['teamStats']['pitching']
    home_pitching = home_team['teamStats']['pitching']
    
    # Extract fielding stats
    away_fielding = away_team['teamStats']['fielding']
    home_fielding = home_team['teamStats']['fielding']
    
    # Build comprehensive stats dictionary
    stats = {
        # Game Info
        'game_pk': game_pk,
        'date': game_date,
        'venue': venue,
        'away_team': away_team_name,
        'home_team': home_team_name,
        
        # Away Team Batting
        'away_runs': away_batting.get('runs', 0),
        'away_hits': away_batting.get('hits', 0),
        'away_doubles': away_batting.get('doubles', 0),
        'away_triples': away_batting.get('triples', 0),
        'away_homeruns': away_batting.get('homeRuns', 0),
        'away_rbi': away_batting.get('rbi', 0),
        'away_walks': away_batting.get('baseOnBalls', 0),
        'away_strikeouts': away_batting.get('strikeOuts', 0),
        'away_stolen_bases': away_batting.get('stolenBases', 0),
        'away_caught_stealing': away_batting.get('caughtStealing', 0),
        'away_hit_by_pitch': away_batting.get('hitByPitch', 0),
        'away_at_bats': away_batting.get('atBats', 0),
        'away_obp': away_batting.get('obp', '.000'),
        'away_slg': away_batting.get('slg', '.000'),
        'away_ops': away_batting.get('ops', '.000'),
        'away_avg': away_batting.get('avg', '.000'),
        'away_left_on_base': away_batting.get('leftOnBase', 0),
        'away_sac_bunts': away_batting.get('sacBunts', 0),
        'away_sac_flies': away_batting.get('sacFlies', 0),
        'away_ground_into_dp': away_batting.get('groundIntoDoublePlay', 0),
        'away_total_bases': away_batting.get('totalBases', 0),
        
        # Home Team Batting
        'home_runs': home_batting.get('runs', 0),
        'home_hits': home_batting.get('hits', 0),
        'home_doubles': home_batting.get('doubles', 0),
        'home_triples': home_batting.get('triples', 0),
        'home_homeruns': home_batting.get('homeRuns', 0),
        'home_rbi': home_batting.get('rbi', 0),
        'home_walks': home_batting.get('baseOnBalls', 0),
        'home_strikeouts': home_batting.get('strikeOuts', 0),
        'home_stolen_bases': home_batting.get('stolenBases', 0),
        'home_caught_stealing': home_batting.get('caughtStealing', 0),
        'home_hit_by_pitch': home_batting.get('hitByPitch', 0),
        'home_at_bats': home_batting.get('atBats', 0),
        'home_obp': home_batting.get('obp', '.000'),
        'home_slg': home_batting.get('slg', '.000'),
        'home_ops': home_batting.get('ops', '.000'),
        'home_avg': home_batting.get('avg', '.000'),
        'home_left_on_base': home_batting.get('leftOnBase', 0),
        'home_sac_bunts': home_batting.get('sacBunts', 0),
        'home_sac_flies': home_batting.get('sacFlies', 0),
        'home_ground_into_dp': home_batting.get('groundIntoDoublePlay', 0),
        'home_total_bases': home_batting.get('totalBases', 0),
        
        # Away Team Pitching
        'away_innings_pitched': away_pitching.get('inningsPitched', '0.0'),
        'away_earned_runs': away_pitching.get('earnedRuns', 0),
        'away_pitcher_strikeouts': away_pitching.get('strikeOuts', 0),
        'away_pitcher_walks': away_pitching.get('baseOnBalls', 0),
        'away_pitcher_hits': away_pitching.get('hits', 0),
        'away_pitcher_homeruns': away_pitching.get('homeRuns', 0),
        'away_pitcher_era': away_pitching.get('era', '0.00'),
        'away_pitcher_whip': away_pitching.get('whip', '0.00'),
        'away_hit_batters': away_pitching.get('hitBatsmen', 0),
        'away_wild_pitches': away_pitching.get('wildPitches', 0),
        'away_balks': away_pitching.get('balks', 0),
        'away_pitches_thrown': away_pitching.get('numberOfPitches', 0),
        'away_strikes': away_pitching.get('strikes', 0),
        
        # Home Team Pitching
        'home_innings_pitched': home_pitching.get('inningsPitched', '0.0'),
        'home_earned_runs': home_pitching.get('earnedRuns', 0),
        'home_pitcher_strikeouts': home_pitching.get('strikeOuts', 0),
        'home_pitcher_walks': home_pitching.get('baseOnBalls', 0),
        'home_pitcher_hits': home_pitching.get('hits', 0),
        'home_pitcher_homeruns': home_pitching.get('homeRuns', 0),
        'home_pitcher_era': home_pitching.get('era', '0.00'),
        'home_pitcher_whip': home_pitching.get('whip', '0.00'),
        'home_hit_batters': home_pitching.get('hitBatsmen', 0),
        'home_wild_pitches': home_pitching.get('wildPitches', 0),
        'home_balks': home_pitching.get('balks', 0),
        'home_pitches_thrown': home_pitching.get('numberOfPitches', 0),
        'home_strikes': home_pitching.get('strikes', 0),
        
        # Away Team Fielding
        'away_errors': away_fielding.get('errors', 0),
        'away_putouts': away_fielding.get('putouts', 0),
        'away_assists': away_fielding.get('assists', 0),
        'away_chances': away_fielding.get('chances', 0),
        'away_passed_balls': away_fielding.get('passedBall', 0),
        'away_double_plays': away_fielding.get('doublePlays', 0),
        
        # Home Team Fielding
        'home_errors': home_fielding.get('errors', 0),
        'home_putouts': home_fielding.get('putouts', 0),
        'home_assists': home_fielding.get('assists', 0),
        'home_chances': home_fielding.get('chances', 0),
        'home_passed_balls': home_fielding.get('passedBall', 0),
        'home_double_plays': home_fielding.get('doublePlays', 0),
    }
    
    return stats


def main():
    """Main execution function."""
    print("=" * 80)
    print("MLB Stats API - March 2025 Box Score Fetcher")
    print("=" * 80)
    print(f"Date Range: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print("=" * 80)
    print()
    
    all_boxscores = []
    total_games = 0
    successful_games = 0
    failed_games = 0
    
    # Loop through each date in March
    current_date = START_DATE
    while current_date <= END_DATE:
        date_str = current_date.strftime("%Y-%m-%d")
        print(f"\n📅 Processing {date_str}...")
        
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
            
            # Extract stats
            stats = extract_team_boxscore(game, boxscore_data)
            
            if not stats:
                print(f"      ❌ Failed to extract stats")
                failed_games += 1
                continue
            
            # Save individual game CSV
            game_df = pd.DataFrame([stats])
            game_csv_path = os.path.join(OUTPUT_DIR, f"game_{game_pk}.csv")
            game_df.to_csv(game_csv_path, index=False)
            
            # Add to master list
            all_boxscores.append(stats)
            successful_games += 1
            
            print(f"      ✅ Score: {stats['away_runs']}-{stats['home_runs']}")
            print(f"      📄 Saved to: {game_csv_path}")
            
            # Small delay to be respectful to API
            time.sleep(0.5)
        
        current_date += timedelta(days=1)
    
    # Save master CSV with all games
    print("\n" + "=" * 80)
    print("💾 Saving master CSV...")
    
    if all_boxscores:
        master_df = pd.DataFrame(all_boxscores)
        master_df.to_csv(MASTER_CSV, index=False)
        print(f"✅ Master CSV saved: {MASTER_CSV}")
        print(f"📊 Total columns: {len(master_df.columns)}")
        print(f"📊 Total rows: {len(master_df)}")
    else:
        print("❌ No boxscores to save")
    
    # Summary
    print("\n" + "=" * 80)
    print("📈 SUMMARY")
    print("=" * 80)
    print(f"Total games found:     {total_games}")
    print(f"Successfully fetched:  {successful_games}")
    print(f"Failed:                {failed_games}")
    print(f"Success rate:          {successful_games/total_games*100:.1f}%" if total_games > 0 else "N/A")
    print("\n" + "=" * 80)
    
    # Show sample stats if any games were fetched
    if all_boxscores:
        print("\n📋 SAMPLE: First Game Stats")
        print("=" * 80)
        first_game = all_boxscores[0]
        print(f"Date:      {first_game['date']}")
        print(f"Venue:     {first_game['venue']}")
        print(f"Away Team: {first_game['away_team']}")
        print(f"Home Team: {first_game['home_team']}")
        print(f"Score:     {first_game['away_runs']}-{first_game['home_runs']}")
        print(f"\nAway Batting: {first_game['away_at_bats']} AB, {first_game['away_hits']} H, "
              f"{first_game['away_doubles']} 2B, {first_game['away_homeruns']} HR, "
              f"{first_game['away_rbi']} RBI, {first_game['away_walks']} BB, "
              f"{first_game['away_strikeouts']} SO")
        print(f"Home Batting: {first_game['home_at_bats']} AB, {first_game['home_hits']} H, "
              f"{first_game['home_doubles']} 2B, {first_game['home_homeruns']} HR, "
              f"{first_game['home_rbi']} RBI, {first_game['home_walks']} BB, "
              f"{first_game['home_strikeouts']} SO")
        print("=" * 80)


if __name__ == "__main__":
    main()
