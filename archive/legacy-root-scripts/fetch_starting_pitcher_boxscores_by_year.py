import pandas as pd
import requests
import time
from datetime import datetime
import os
import sys
import glob

def fetch_starting_pitcher_boxscores_for_year(year):
    """
    Fetch starting pitcher boxscores for a specific MLB season year
    Reads game_pk values from team boxscore files
    """
    print(f"\n{'='*60}")
    print(f"Fetching MLB Starting Pitcher Boxscores for {year} Season")
    print(f"{'='*60}\n")
    
    # Set directories
    boxscores_dir = f'/workspaces/MLB-Model/data/{year}_data/mlb_data/raw/boxscores'
    output_dir = f'/workspaces/MLB-Model/data/{year}_data/mlb_data/raw/starting_pitcher_boxscores'
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all boxscore CSV files
    boxscore_files = sorted(glob.glob(os.path.join(boxscores_dir, 'boxscores_*.csv')))
    
    if not boxscore_files:
        print(f"❌ No boxscore files found in {boxscores_dir}")
        print("   Please run team boxscore collection first.")
        return
    
    print(f"📂 Found {len(boxscore_files)} boxscore files to process\n")
    
    total_games = 0
    dates_processed = 0
    
    for boxscore_file in boxscore_files:
        # Extract date from filename (boxscores_YYYY-MM-DD.csv)
        filename = os.path.basename(boxscore_file)
        date_str = filename.replace('boxscores_', '').replace('.csv', '')
        
        try:
            # Read the boxscore file to get game_pk values
            df = pd.read_csv(boxscore_file)
            game_pks = df['game_pk'].unique()
            
            print(f"📊 {date_str}: Processing {len(game_pks)} games")
            dates_processed += 1
            
            pitcher_data = []
            
            for game_pk in game_pks:
                # Fetch full boxscore
                boxscore_url = f'https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore'
                
                try:
                    response = requests.get(boxscore_url)
                    response.raise_for_status()
                    boxscore = response.json()
                    
                    # Extract starting pitchers for both teams
                    teams_data = boxscore.get('teams', {})
                    home_team = teams_data.get('home', {})
                    away_team = teams_data.get('away', {})
                    
                    # Initialize row with game_pk and date
                    row = {
                        'game_pk': game_pk,
                        'date': date_str
                    }
                    
                    # Extract home starting pitcher
                    home_pitchers = home_team.get('pitchers', [])
                    if home_pitchers:
                        home_starter_id = home_pitchers[0]
                        home_players = home_team.get('players', {})
                        home_starter_key = f'ID{home_starter_id}'
                        
                        if home_starter_key in home_players:
                            home_starter = home_players[home_starter_key]
                            home_person = home_starter.get('person', {})
                            home_stats = home_starter.get('stats', {})
                            home_pitching = home_stats.get('pitching', {})
                            
                            row['home_starter_id'] = home_starter_id
                            row['home_starter_name'] = home_person.get('fullName', '')
                            row['home_starter_team'] = home_team.get('team', {}).get('name', '')
                            row['home_starter_ip'] = home_pitching.get('inningsPitched', '0.0')
                            row['home_starter_hits'] = home_pitching.get('hits', 0)
                            row['home_starter_runs'] = home_pitching.get('runs', 0)
                            row['home_starter_earned_runs'] = home_pitching.get('earnedRuns', 0)
                            row['home_starter_walks'] = home_pitching.get('baseOnBalls', 0)
                            row['home_starter_strikeouts'] = home_pitching.get('strikeOuts', 0)
                            row['home_starter_homeruns'] = home_pitching.get('homeRuns', 0)
                            row['home_starter_era'] = home_pitching.get('era', '0.00')
                            row['home_starter_whip'] = home_pitching.get('whip', '0.00')
                            row['home_starter_pitches'] = home_pitching.get('numberOfPitches', 0)
                            row['home_starter_strikes'] = home_pitching.get('strikes', 0)
                            row['home_starter_hit_batters'] = home_pitching.get('hitBatsmen', 0)
                            row['home_starter_wild_pitches'] = home_pitching.get('wildPitches', 0)
                            row['home_starter_balks'] = home_pitching.get('balks', 0)
                            row['home_starter_batters_faced'] = home_pitching.get('battersFaced', 0)
                            row['home_starter_ground_outs'] = home_pitching.get('groundOuts', 0)
                            row['home_starter_air_outs'] = home_pitching.get('airOuts', 0)
                            row['home_starter_wins'] = home_pitching.get('wins', 0)
                            row['home_starter_losses'] = home_pitching.get('losses', 0)
                            row['home_starter_saves'] = home_pitching.get('saves', 0)
                            row['home_starter_blown_saves'] = home_pitching.get('blownSaves', 0)
                            row['home_starter_holds'] = home_pitching.get('holds', 0)
                    
                    # Extract away starting pitcher
                    away_pitchers = away_team.get('pitchers', [])
                    if away_pitchers:
                        away_starter_id = away_pitchers[0]
                        away_players = away_team.get('players', {})
                        away_starter_key = f'ID{away_starter_id}'
                        
                        if away_starter_key in away_players:
                            away_starter = away_players[away_starter_key]
                            away_person = away_starter.get('person', {})
                            away_stats = away_starter.get('stats', {})
                            away_pitching = away_stats.get('pitching', {})
                            
                            row['away_starter_id'] = away_starter_id
                            row['away_starter_name'] = away_person.get('fullName', '')
                            row['away_starter_team'] = away_team.get('team', {}).get('name', '')
                            row['away_starter_ip'] = away_pitching.get('inningsPitched', '0.0')
                            row['away_starter_hits'] = away_pitching.get('hits', 0)
                            row['away_starter_runs'] = away_pitching.get('runs', 0)
                            row['away_starter_earned_runs'] = away_pitching.get('earnedRuns', 0)
                            row['away_starter_walks'] = away_pitching.get('baseOnBalls', 0)
                            row['away_starter_strikeouts'] = away_pitching.get('strikeOuts', 0)
                            row['away_starter_homeruns'] = away_pitching.get('homeRuns', 0)
                            row['away_starter_era'] = away_pitching.get('era', '0.00')
                            row['away_starter_whip'] = away_pitching.get('whip', '0.00')
                            row['away_starter_pitches'] = away_pitching.get('numberOfPitches', 0)
                            row['away_starter_strikes'] = away_pitching.get('strikes', 0)
                            row['away_starter_hit_batters'] = away_pitching.get('hitBatsmen', 0)
                            row['away_starter_wild_pitches'] = away_pitching.get('wildPitches', 0)
                            row['away_starter_balks'] = away_pitching.get('balks', 0)
                            row['away_starter_batters_faced'] = away_pitching.get('battersFaced', 0)
                            row['away_starter_ground_outs'] = away_pitching.get('groundOuts', 0)
                            row['away_starter_air_outs'] = away_pitching.get('airOuts', 0)
                            row['away_starter_wins'] = away_pitching.get('wins', 0)
                            row['away_starter_losses'] = away_pitching.get('losses', 0)
                            row['away_starter_saves'] = away_pitching.get('saves', 0)
                            row['away_starter_blown_saves'] = away_pitching.get('blownSaves', 0)
                            row['away_starter_holds'] = away_pitching.get('holds', 0)
                    
                    pitcher_data.append(row)
                    time.sleep(0.3)  # Rate limiting
                    
                except Exception as e:
                    print(f"  ⚠️  Error fetching boxscore for game {game_pk}: {e}")
                    continue
            
            # Save to CSV for this date
            if pitcher_data:
                df_pitchers = pd.DataFrame(pitcher_data)
                
                # Reorder columns to match 2024 format (alternating home/away)
                column_order = [
                    'game_pk', 'date',
                    'home_starter_id', 'away_starter_id',
                    'home_starter_name', 'away_starter_name',
                    'home_starter_team', 'away_starter_team',
                    'home_starter_ip', 'away_starter_ip',
                    'home_starter_hits', 'away_starter_hits',
                    'home_starter_runs', 'away_starter_runs',
                    'home_starter_earned_runs', 'away_starter_earned_runs',
                    'home_starter_walks', 'away_starter_walks',
                    'home_starter_strikeouts', 'away_starter_strikeouts',
                    'home_starter_homeruns', 'away_starter_homeruns',
                    'home_starter_era', 'away_starter_era',
                    'home_starter_whip', 'away_starter_whip',
                    'home_starter_pitches', 'away_starter_pitches',
                    'home_starter_strikes', 'away_starter_strikes',
                    'home_starter_hit_batters', 'away_starter_hit_batters',
                    'home_starter_wild_pitches', 'away_starter_wild_pitches',
                    'home_starter_balks', 'away_starter_balks',
                    'home_starter_batters_faced', 'away_starter_batters_faced',
                    'home_starter_ground_outs', 'away_starter_ground_outs',
                    'home_starter_air_outs', 'away_starter_air_outs',
                    'home_starter_wins', 'away_starter_wins',
                    'home_starter_losses', 'away_starter_losses',
                    'home_starter_saves', 'away_starter_saves',
                    'home_starter_blown_saves', 'away_starter_blown_saves',
                    'home_starter_holds', 'away_starter_holds'
                ]
                
                # Only select columns that exist
                df_pitchers = df_pitchers[[col for col in column_order if col in df_pitchers.columns]]
                
                output_file = os.path.join(output_dir, f'starting_pitcher_boxscores_{date_str}.csv')
                df_pitchers.to_csv(output_file, index=False)
                
                total_games += len(game_pks)
                print(f"  ✅ {date_str}: Saved {len(game_pks)} games")
            
            time.sleep(0.5)  # Rate limiting between dates
            
        except Exception as e:
            print(f"  ⚠️  Error processing {date_str}: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"✅ Complete! Processed {dates_processed} dates with {total_games} total games")
    print(f"📁 Output location: {output_dir}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fetch_starting_pitcher_boxscores_by_year.py <year>")
        print("Example: python fetch_starting_pitcher_boxscores_by_year.py 2023")
        sys.exit(1)
    
    year = int(sys.argv[1])
    
    if year < 2009 or year > 2025:
        print(f"Error: Year {year} is out of range. Please use years between 2009 and 2025.")
        sys.exit(1)
    
    fetch_starting_pitcher_boxscores_for_year(year)
