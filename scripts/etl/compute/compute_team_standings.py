"""
Compute team season standings going into each game.
For each game, calculate both teams' cumulative stats BEFORE that game is played.
"""

import pandas as pd
import glob
import os
from collections import defaultdict

print("="*80)
print("COMPUTING TEAM SEASON STANDINGS")
print("="*80)
print()

# Load all box scores
print("Loading box scores...")
boxscores = pd.concat([pd.read_csv(f) for f in glob.glob('data/bdl_data/boxscores/boxscores_2025-*.csv')], 
                      ignore_index=True)
print(f"Loaded {len(boxscores)} games")

# Sort by date to process chronologically
boxscores['date_dt'] = pd.to_datetime(boxscores['date'])
boxscores = boxscores.sort_values('date_dt').reset_index(drop=True)

print()
print("Initializing team tracking...")

# Dictionary to track each team's cumulative stats
team_stats = defaultdict(lambda: {
    'games_played': 0,
    'wins': 0,
    'losses': 0,
    'points_for': 0,
    'points_against': 0,
    'home_wins': 0,
    'home_losses': 0,
    'road_wins': 0,
    'road_losses': 0,
    'last_10_results': [],  # List of recent W/L results
    'streak_type': None,  # 'W' or 'L'
    'streak_count': 0,
    'division_wins': 0,
    'division_losses': 0,
    'league_wins': 0,
    'league_losses': 0
})

# Create output directory
output_dir = 'data/bdl_data/team_season_standings'
os.makedirs(output_dir, exist_ok=True)

standings_data = []

print()
print("Processing games chronologically...")
print()

for idx, game in boxscores.iterrows():
    if idx % 500 == 0:
        print(f"  Processed {idx}/{len(boxscores)} games...")
    
    home_team = game['home_team_abbreviation']
    away_team = game['away_team_abbreviation']
    
    # Get current standings BEFORE this game
    home_standing = team_stats[home_team].copy()
    away_standing = team_stats[away_team].copy()
    
    # Calculate derived stats for current standings
    home_gp = home_standing['games_played']
    away_gp = away_standing['games_played']
    
    home_win_pct = home_standing['wins'] / home_gp if home_gp > 0 else 0.0
    away_win_pct = away_standing['wins'] / away_gp if away_gp > 0 else 0.0
    
    home_avg_pf = home_standing['points_for'] / home_gp if home_gp > 0 else 0.0
    away_avg_pf = away_standing['points_for'] / away_gp if away_gp > 0 else 0.0
    
    home_avg_pa = home_standing['points_against'] / home_gp if home_gp > 0 else 0.0
    away_avg_pa = away_standing['points_against'] / away_gp if away_gp > 0 else 0.0
    
    home_diff = home_standing['points_for'] - home_standing['points_against']
    away_diff = away_standing['points_for'] - away_standing['points_against']
    
    home_differential = home_avg_pf - home_avg_pa
    away_differential = away_avg_pf - away_avg_pa
    
    # Format streak
    home_streak = f"{home_standing['streak_type']}{home_standing['streak_count']}" if home_standing['streak_count'] > 0 else "-"
    away_streak = f"{away_standing['streak_type']}{away_standing['streak_count']}" if away_standing['streak_count'] > 0 else "-"
    
    # Calculate last 10 record
    home_last_10_wins = sum(1 for r in home_standing['last_10_results'] if r == 'W')
    away_last_10_wins = sum(1 for r in away_standing['last_10_results'] if r == 'W')
    home_last_10_losses = len(home_standing['last_10_results']) - home_last_10_wins
    away_last_10_losses = len(away_standing['last_10_results']) - away_last_10_wins
    home_last_10 = f"{home_last_10_wins}-{home_last_10_losses}" if home_standing['last_10_results'] else "0-0"
    away_last_10 = f"{away_last_10_wins}-{away_last_10_losses}" if away_standing['last_10_results'] else "0-0"
    
    # Home/road record
    home_home_record = f"{home_standing['home_wins']}-{home_standing['home_losses']}"
    away_home_record = f"{away_standing['home_wins']}-{away_standing['home_losses']}"
    home_road_record = f"{home_standing['road_wins']}-{home_standing['road_losses']}"
    away_road_record = f"{away_standing['road_wins']}-{away_standing['road_losses']}"
    
    # Calculate league/division win percentages
    home_league_wp = home_standing['league_wins'] / (home_standing['league_wins'] + home_standing['league_losses']) if (home_standing['league_wins'] + home_standing['league_losses']) > 0 else 0.0
    away_league_wp = away_standing['league_wins'] / (away_standing['league_wins'] + away_standing['league_losses']) if (away_standing['league_wins'] + away_standing['league_losses']) > 0 else 0.0
    
    home_div_wp = home_standing['division_wins'] / (home_standing['division_wins'] + home_standing['division_losses']) if (home_standing['division_wins'] + home_standing['division_losses']) > 0 else 0.0
    away_div_wp = away_standing['division_wins'] / (away_standing['division_wins'] + away_standing['division_losses']) if (away_standing['division_wins'] + away_standing['division_losses']) > 0 else 0.0
    
    # Build standings row
    standings_row = {
        'balldontlie_game_id': game['balldontlie_game_id'],
        'id': game['id'],
        'date': game['date'],
        'home_team_id': game['home_team_id'],
        'away_team_id': game['away_team_id'],
        'home_team_abbreviation': home_team,
        'away_team_abbreviation': away_team,
        'home_team_display_name': game['home_team_display_name'],
        'away_team_display_name': game['away_team_display_name'],
        'home_team_name': game['home_team_name'],
        'away_team_name': game['away_team_name'],
        
        # League/Division info (from box scores)
        'home_league_name': 'American League' if game.get('home_team_league', 'American') == 'American' else 'National League',
        'away_league_name': 'American League' if game.get('away_team_league', 'American') == 'American' else 'National League',
        'home_league_short_name': 'AL' if game.get('home_team_league', 'American') == 'American' else 'NL',
        'away_league_short_name': 'AL' if game.get('away_team_league', 'American') == 'American' else 'NL',
        'home_division_name': game.get('home_team_division', 'Unknown'),
        'away_division_name': game.get('away_team_division', 'Unknown'),
        'home_division_short_name': game.get('home_team_division', 'Unknown'),
        'away_division_short_name': game.get('away_team_division', 'Unknown'),
        
        # Season
        'home_season': game['home_season'],
        'away_season': game['away_season'],
        
        # Win/Loss Record
        'home_games_played': home_gp,
        'away_games_played': away_gp,
        'home_wins': home_standing['wins'],
        'away_wins': away_standing['wins'],
        'home_losses': home_standing['losses'],
        'away_losses': away_standing['losses'],
        'home_win_percent': round(home_win_pct, 3),
        'away_win_percent': round(away_win_pct, 3),
        
        # Scoring Stats
        'home_points_for': home_standing['points_for'],
        'away_points_for': away_standing['points_for'],
        'home_points_against': home_standing['points_against'],
        'away_points_against': away_standing['points_against'],
        'home_point_differential': home_diff,
        'away_point_differential': away_diff,
        'home_avg_points_for': round(home_avg_pf, 2),
        'away_avg_points_for': round(away_avg_pf, 2),
        'home_avg_points_against': round(home_avg_pa, 2),
        'away_avg_points_against': round(away_avg_pa, 2),
        'home_differential': round(home_differential, 2),
        'away_differential': round(away_differential, 2),
        
        # Games Behind (placeholder - requires division context)
        'home_games_behind': 0.0,
        'away_games_behind': 0.0,
        'home_division_games_behind': 0.0,
        'away_division_games_behind': 0.0,
        
        # League/Division Win Percentages
        'home_league_win_percent': round(home_league_wp, 3),
        'away_league_win_percent': round(away_league_wp, 3),
        'home_division_win_percent': round(home_div_wp, 3),
        'away_division_win_percent': round(away_div_wp, 3),
        
        # Home/Road Splits
        'home_home_wins': home_standing['home_wins'],
        'away_home_wins': away_standing['home_wins'],
        'home_home_losses': home_standing['home_losses'],
        'away_home_losses': away_standing['home_losses'],
        'home_road_wins': home_standing['road_wins'],
        'away_road_wins': away_standing['road_wins'],
        'home_road_losses': home_standing['road_losses'],
        'away_road_losses': away_standing['road_losses'],
        
        # Streak
        'home_streak': home_streak,
        'away_streak': away_streak,
        
        # Playoff Info (placeholder)
        'home_playoff_seed': 0,
        'away_playoff_seed': 0,
        'home_playoff_percent': 0.0,
        'away_playoff_percent': 0.0,
        'home_wildcard_percent': 0.0,
        'away_wildcard_percent': 0.0,
        
        # Record Formats
        'home_total': f"{home_standing['wins']}-{home_standing['losses']}",
        'away_total': f"{away_standing['wins']}-{away_standing['losses']}",
        'home_home': home_home_record,
        'away_home': away_home_record,
        'home_road': home_road_record,
        'away_road': away_road_record,
        'home_intra_division': f"{home_standing['division_wins']}-{home_standing['division_losses']}",
        'away_intra_division': f"{away_standing['division_wins']}-{away_standing['division_losses']}",
        'home_intra_league': f"{home_standing['league_wins']}-{home_standing['league_losses']}",
        'away_intra_league': f"{away_standing['league_wins']}-{away_standing['league_losses']}",
        'home_last_ten_games': home_last_10,
        'away_last_ten_games': away_last_10,
    }
    
    standings_data.append(standings_row)
    
    # NOW update the team stats with this game's results
    home_runs = int(game['home_batting_r'])
    away_runs = int(game['away_batting_r'])
    home_won = home_runs > away_runs
    away_won = away_runs > home_runs
    
    # Update games played
    team_stats[home_team]['games_played'] += 1
    team_stats[away_team]['games_played'] += 1
    
    # Update wins/losses
    if home_won:
        team_stats[home_team]['wins'] += 1
        team_stats[away_team]['losses'] += 1
        home_result = 'W'
        away_result = 'L'
    else:
        team_stats[home_team]['losses'] += 1
        team_stats[away_team]['wins'] += 1
        home_result = 'L'
        away_result = 'W'
    
    # Update points
    team_stats[home_team]['points_for'] += home_runs
    team_stats[home_team]['points_against'] += away_runs
    team_stats[away_team]['points_for'] += away_runs
    team_stats[away_team]['points_against'] += home_runs
    
    # Update home/road splits
    if home_won:
        team_stats[home_team]['home_wins'] += 1
        team_stats[away_team]['road_losses'] += 1
    else:
        team_stats[home_team]['home_losses'] += 1
        team_stats[away_team]['road_wins'] += 1
    
    # Update streaks
    for team, result in [(home_team, home_result), (away_team, away_result)]:
        if team_stats[team]['streak_type'] == result:
            team_stats[team]['streak_count'] += 1
        else:
            team_stats[team]['streak_type'] = result
            team_stats[team]['streak_count'] = 1
    
    # Update last 10
    for team, result in [(home_team, home_result), (away_team, away_result)]:
        team_stats[team]['last_10_results'].append(result)
        if len(team_stats[team]['last_10_results']) > 10:
            team_stats[team]['last_10_results'].pop(0)
    
    # Update division/league records (need to check if teams are in same division/league)
    # For now, mark all as league games
    team_stats[home_team]['league_wins'] += 1 if home_won else 0
    team_stats[home_team]['league_losses'] += 0 if home_won else 1
    team_stats[away_team]['league_wins'] += 1 if away_won else 0
    team_stats[away_team]['league_losses'] += 0 if away_won else 1

print(f"  Processed {len(boxscores)}/{len(boxscores)} games... DONE")
print()
print("Creating DataFrame...")
standings_df = pd.DataFrame(standings_data)

print()
print(f"Created standings for {len(standings_df)} games")
print()

# Save by date
print("Saving standings files by date...")
saved_files = 0
for date_str, group in standings_df.groupby('date'):
    file_path = f'{output_dir}/team_season_standings_{date_str}.csv'
    group.to_csv(file_path, index=False)
    saved_files += 1

print(f"✅ Saved {saved_files} files to {output_dir}/")
print()

# Show sample output
print("="*80)
print("SAMPLE OUTPUT")
print("="*80)
print()
print("First game standings:")
first_game = standings_df.iloc[0]
print(f"Date: {first_game['date']}")
print(f"Matchup: {first_game['away_team_abbreviation']} @ {first_game['home_team_abbreviation']}")
print(f"Home team record going in: {first_game['home_total']} ({first_game['home_win_percent']:.3f})")
print(f"Away team record going in: {first_game['away_total']} ({first_game['away_win_percent']:.3f})")
print()

# Check a mid-season game
mid_game = standings_df.iloc[len(standings_df)//2]
print("Mid-season game standings:")
print(f"Date: {mid_game['date']}")
print(f"Matchup: {mid_game['away_team_abbreviation']} @ {mid_game['home_team_abbreviation']}")
print(f"Home: {mid_game['home_team_display_name']} - {mid_game['home_total']} ({mid_game['home_win_percent']:.3f})")
print(f"  Points: {mid_game['home_points_for']}-{mid_game['home_points_against']} ({mid_game['home_differential']:+.2f} avg diff)")
print(f"  Home/Road: {mid_game['home_home']} / {mid_game['home_road']}")
print(f"  Streak: {mid_game['home_streak']}")
print(f"  Last 10: {mid_game['home_last_ten_games']}")
print()
print(f"Away: {mid_game['away_team_display_name']} - {mid_game['away_total']} ({mid_game['away_win_percent']:.3f})")
print(f"  Points: {mid_game['away_points_for']}-{mid_game['away_points_against']} ({mid_game['away_differential']:+.2f} avg diff)")
print(f"  Home/Road: {mid_game['away_home']} / {mid_game['away_road']}")
print(f"  Streak: {mid_game['away_streak']}")
print(f"  Last 10: {mid_game['away_last_ten_games']}")

print()
print("="*80)
print("COMPLETE!")
print("="*80)
