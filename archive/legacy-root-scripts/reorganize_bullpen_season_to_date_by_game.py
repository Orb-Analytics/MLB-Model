"""
Reorganize team bullpen season-to-date stats from team-per-row format to game-per-row format.
Each row will represent a game with home and away team stats in alternating columns.
"""

import pandas as pd
import glob
import os

def reorganize_to_game_format():
    """
    Transform season-to-date stats from team-per-row to game-per-row format.
    """
    
    # Load the schedule to get game structure
    print("Loading MLB schedule...")
    schedule_df = pd.read_csv('mlb_official_2025_schedule.csv')
    
    # Get all season-to-date stats files
    stats_files = sorted(glob.glob('data/mlb_data/derived_stats/team_bullpen_season_to_date_stats/team_bullpen_season_to_date_*.csv'))
    # Exclude the consolidated file
    stats_files = [f for f in stats_files if not f.endswith('_all.csv')]
    
    print(f"Found {len(stats_files)} season-to-date stats files")
    
    # Create output directory
    output_dir = 'data/mlb_data/derived_stats/team_bullpen_season_to_date_stats_by_game'
    os.makedirs(output_dir, exist_ok=True)
    
    all_game_records = []
    total_games_processed = 0
    
    for stats_file in stats_files:
        # Extract date from filename
        date_str = stats_file.split('_')[-1].replace('.csv', '')
        
        # Load season-to-date stats for this date
        stats_df = pd.read_csv(stats_file)
        
        # Filter schedule for games on this date
        games_on_date = schedule_df[schedule_df['date'] == date_str].copy()
        
        if len(games_on_date) == 0:
            print(f"Skipping {date_str}: no games in schedule")
            continue
        
        print(f"Processing {date_str}: {len(games_on_date)} games")
        
        # Create a dictionary for quick team lookup
        team_stats_dict = {}
        for _, row in stats_df.iterrows():
            team_stats_dict[row['team_id']] = row
        
        # Process each game
        game_records = []
        for _, game in games_on_date.iterrows():
            home_team_id = game['home_team_id']
            away_team_id = game['away_team_id']
            
            # Get stats for both teams (these are season-to-date stats AFTER this game)
            # Note: These stats include the current game
            home_stats = team_stats_dict.get(home_team_id)
            away_stats = team_stats_dict.get(away_team_id)
            
            if home_stats is None or away_stats is None:
                print(f"  Warning: Missing stats for game {game['mlb_game_pk']}")
                continue
            
            # Create game record with alternating home/away columns
            from collections import OrderedDict
            game_record = OrderedDict([
                ('game_pk', game['mlb_game_pk']),
                ('date', date_str),
                
                # Alternating home/away for each stat
                ('home_team_id', home_team_id),
                ('away_team_id', away_team_id),
                ('home_team_name', game['home_team_name']),
                ('away_team_name', game['away_team_name']),
                ('home_games', int(home_stats['games'])),
                ('away_games', int(away_stats['games'])),
                ('home_total_ip', float(home_stats['total_ip'])),
                ('away_total_ip', float(away_stats['total_ip'])),
                ('home_total_hits', int(home_stats['total_hits'])),
                ('away_total_hits', int(away_stats['total_hits'])),
                ('home_total_earned_runs', int(home_stats['total_earned_runs'])),
                ('away_total_earned_runs', int(away_stats['total_earned_runs'])),
                ('home_total_walks', int(home_stats['total_walks'])),
                ('away_total_walks', int(away_stats['total_walks'])),
                ('home_total_strikeouts', int(home_stats['total_strikeouts'])),
                ('away_total_strikeouts', int(away_stats['total_strikeouts'])),
                ('home_total_homeruns', int(home_stats['total_homeruns'])),
                ('away_total_homeruns', int(away_stats['total_homeruns'])),
                ('home_era', float(home_stats['era'])),
                ('away_era', float(away_stats['era'])),
                ('home_whip', float(home_stats['whip'])),
                ('away_whip', float(away_stats['whip'])),
                ('home_k_per_9', float(home_stats['k_per_9'])),
                ('away_k_per_9', float(away_stats['k_per_9'])),
                ('home_k_bb_ratio', float(home_stats['k_bb_ratio'])),
                ('away_k_bb_ratio', float(away_stats['k_bb_ratio'])),
                ('home_hr_per_9', float(home_stats['hr_per_9'])),
                ('away_hr_per_9', float(away_stats['hr_per_9'])),
                ('home_bb_per_9', float(home_stats['bb_per_9'])),
                ('away_bb_per_9', float(away_stats['bb_per_9'])),
            ])
            
            game_records.append(game_record)
            all_game_records.append(game_record)
            total_games_processed += 1
        
        # Save date-specific file
        if game_records:
            output_file = f"{output_dir}/team_bullpen_season_to_date_by_game_{date_str}.csv"
            game_df = pd.DataFrame(game_records)
            game_df.to_csv(output_file, index=False)
            print(f"  Saved {len(game_records)} game records to {output_file}")
    
    print(f"\nProcessing complete!")
    print(f"Total games processed: {total_games_processed}")
    
    # Save consolidated file
    if all_game_records:
        print("\nCreating consolidated file...")
        consolidated_df = pd.DataFrame(all_game_records)
        consolidated_file = f"{output_dir}/team_bullpen_season_to_date_by_game_all.csv"
        consolidated_df.to_csv(consolidated_file, index=False)
        print(f"Saved consolidated file: {consolidated_file}")
        print(f"Total records: {len(consolidated_df)}")
        
        # Show column order for verification
        print(f"\nColumn order (first 10):")
        for i, col in enumerate(consolidated_df.columns[:10]):
            print(f"  {i+1}. {col}")

if __name__ == "__main__":
    reorganize_to_game_format()
