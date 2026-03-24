"""
Test script to collect the first day of 2009 MLB season
Tests the data collection format before running full season collection
"""

import pandas as pd
import requests
import time
from datetime import datetime, timedelta
import os
from collections import defaultdict

def fetch_2009_opening_day():
    """
    Fetch boxscores for 2009 opening day to test format
    2009 season opened on April 5-6, 2009
    """
    print("Testing 2009 Opening Day Data Collection")
    print("=" * 60)
    
    # Set output directory
    output_dir = '/workspaces/MLB-Model/data/2009_data/mlb_data/raw/boxscores'
    os.makedirs(output_dir, exist_ok=True)
    
    # Search for opening day games (typically early April)
    start_date = datetime(2009, 4, 1)
    end_date = datetime(2009, 4, 10)
    
    team_game_counts = defaultdict(int)
    first_game_date = None
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Get schedule for this date
        schedule_url = f'https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}'
        
        try:
            response = requests.get(schedule_url)
            response.raise_for_status()
            schedule_data = response.json()
            
            # Filter for regular season games
            games = []
            if 'dates' in schedule_data and len(schedule_data['dates']) > 0:
                for date in schedule_data['dates']:
                    for game in date.get('games', []):
                        if game.get('gameType') == 'R':
                            games.append(game)
            
            if games:
                first_game_date = date_str
                print(f"\n✅ Found {len(games)} games on {date_str}")
                print(f"This appears to be opening day!\n")
                
                game_data = []
                
                for game in games:
                    game_pk = game['gamePk']
                    print(f"  Processing game {game_pk}...")
                    
                    # Fetch boxscore
                    boxscore_url = f'https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore'
                    
                    try:
                        box_response = requests.get(boxscore_url)
                        box_response.raise_for_status()
                        boxscore = box_response.json()
                        
                        # Extract team data
                        teams_data = boxscore.get('teams', {})
                        away_team = teams_data.get('away', {})
                        home_team = teams_data.get('home', {})
                        
                        # Get team info
                        away_team_info = away_team.get('team', {})
                        home_team_info = home_team.get('team', {})
                        away_team_name = away_team_info.get('name', '')
                        home_team_name = home_team_info.get('name', '')
                        
                        print(f"    {away_team_name} @ {home_team_name}")
                        
                        # Increment game counts
                        team_game_counts[away_team_name] += 1
                        team_game_counts[home_team_name] += 1
                        
                        # Extract stats
                        away_batting = away_team.get('teamStats', {}).get('batting', {})
                        home_batting = home_team.get('teamStats', {}).get('batting', {})
                        away_pitching = away_team.get('teamStats', {}).get('pitching', {})
                        home_pitching = home_team.get('teamStats', {}).get('pitching', {})
                        away_fielding = away_team.get('teamStats', {}).get('fielding', {})
                        home_fielding = home_team.get('teamStats', {}).get('fielding', {})
                        
                        # Determine winner for W/L
                        away_runs = away_batting.get('runs', 0)
                        home_runs = home_batting.get('runs', 0)
                        home_won = 1 if home_runs > away_runs else 0
                        away_won = 1 if away_runs > home_runs else 0
                        home_loss = 1 if away_runs > home_runs else 0
                        away_loss = 1 if home_runs > away_runs else 0
                        
                        # Build row with exact 2024 schema (alternating home/away)
                        row = {
                            'game_pk': game_pk,
                            'date': date_str,
                            'home_team_id': home_team_info.get('id', ''),
                            'away_team_id': away_team_info.get('id', ''),
                            'home_team_abbreviation': home_team_info.get('abbreviation', ''),
                            'away_team_abbreviation': away_team_info.get('abbreviation', ''),
                            'home_team_display_name': home_team_info.get('teamName', ''),
                            'away_team_display_name': away_team_info.get('teamName', ''),
                            'home_team_name': home_team_info.get('name', ''),
                            'away_team_name': away_team_info.get('name', ''),
                            'home_postseason': 0,
                            'away_postseason': 0,
                            'home_season_type': 'regular',
                            'away_season_type': 'regular',
                            'home_season': 2009,
                            'away_season': 2009,
                            'home_gp': team_game_counts[home_team_name],
                            'away_gp': team_game_counts[away_team_name],
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
                            'home_pitching_oba': home_pitching.get('battingAvg', '.000'),
                            'away_pitching_oba': away_pitching.get('battingAvg', '.000'),
                            'home_pitching_whip': home_pitching.get('whip', '0.00'),
                            'away_pitching_whip': away_pitching.get('whip', '0.00'),
                            'home_fielding_e': home_fielding.get('errors', 0),
                            'away_fielding_e': away_fielding.get('errors', 0),
                            'date_dt': date_str
                        }
                        
                        game_data.append(row)
                        time.sleep(0.3)
                        
                    except Exception as e:
                        print(f"  ⚠️  Error fetching boxscore for game {game_pk}: {e}")
                        continue
                
                # Save to CSV
                if game_data:
                    df = pd.DataFrame(game_data)
                    output_file = os.path.join(output_dir, f'boxscores_{date_str}.csv')
                    df.to_csv(output_file, index=False)
                    
                    print(f"\n✅ Saved {len(games)} games to: {output_file}")
                    print(f"\n📊 Column count: {len(df.columns)}")
                    print(f"📊 Row count: {len(df)}")
                    print(f"\nFirst few columns: {', '.join(list(df.columns)[:10])}")
                
                # Stop after finding first game day
                break
                
        except Exception as e:
            print(f"⚠️  Error processing {date_str}: {e}")
        
        current_date += timedelta(days=1)
    
    if first_game_date:
        print(f"\n{'='*60}")
        print(f"✅ Successfully collected 2009 opening day: {first_game_date}")
        print(f"{'='*60}\n")
        return output_dir
    else:
        print("\n❌ No games found in search range")
        return None

if __name__ == "__main__":
    fetch_2009_opening_day()
