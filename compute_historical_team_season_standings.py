"""
Compute team season standings for historical years (2009-2024).
For each game, calculate both teams' cumulative stats BEFORE that game is played.
Outputs daily CSV files aligned with boxscores.
"""

import pandas as pd
import glob
import os
from collections import defaultdict
import sys

# MLB team metadata with league and division info
# Note: Division alignments changed in 2013 (Astros moved from NL Central to AL West)
TEAM_METADATA = {
    # American League East
    110: {'abbr': 'BAL', 'name': 'Orioles', 'display': 'Baltimore Orioles', 'league': 'American League', 'league_short': 'AL', 'division': 'AL East', 'division_short': 'AL East'},
    111: {'abbr': 'BOS', 'name': 'Red Sox', 'display': 'Boston Red Sox', 'league': 'American League', 'league_short': 'AL', 'division': 'AL East', 'division_short': 'AL East'},
    147: {'abbr': 'NYY', 'name': 'Yankees', 'display': 'New York Yankees', 'league': 'American League', 'league_short': 'AL', 'division': 'AL East', 'division_short': 'AL East'},
    139: {'abbr': 'TB', 'name': 'Rays', 'display': 'Tampa Bay Rays', 'league': 'American League', 'league_short': 'AL', 'division': 'AL East', 'division_short': 'AL East'},
    141: {'abbr': 'TOR', 'name': 'Blue Jays', 'display': 'Toronto Blue Jays', 'league': 'American League', 'league_short': 'AL', 'division': 'AL East', 'division_short': 'AL East'},
    
    # American League Central
    145: {'abbr': 'CWS', 'name': 'White Sox', 'display': 'Chicago White Sox', 'league': 'American League', 'league_short': 'AL', 'division': 'AL Central', 'division_short': 'AL Central'},
    114: {'abbr': 'CLE', 'name': 'Guardians', 'display': 'Cleveland Guardians', 'league': 'American League', 'league_short': 'AL', 'division': 'AL Central', 'division_short': 'AL Central'},  # Was Indians pre-2022
    116: {'abbr': 'DET', 'name': 'Tigers', 'display': 'Detroit Tigers', 'league': 'American League', 'league_short': 'AL', 'division': 'AL Central', 'division_short': 'AL Central'},
    118: {'abbr': 'KC', 'name': 'Royals', 'display': 'Kansas City Royals', 'league': 'American League', 'league_short': 'AL', 'division': 'AL Central', 'division_short': 'AL Central'},
    142: {'abbr': 'MIN', 'name': 'Twins', 'display': 'Minnesota Twins', 'league': 'American League', 'league_short': 'AL', 'division': 'AL Central', 'division_short': 'AL Central'},
    
    # American League West
    117: {'abbr': 'HOU', 'name': 'Astros', 'display': 'Houston Astros', 'league': 'American League', 'league_short': 'AL', 'division': 'AL West', 'division_short': 'AL West'},  # Moved to AL in 2013
    108: {'abbr': 'LAA', 'name': 'Angels', 'display': 'Los Angeles Angels', 'league': 'American League', 'league_short': 'AL', 'division': 'AL West', 'division_short': 'AL West'},
    133: {'abbr': 'OAK', 'name': 'Athletics', 'display': 'Oakland Athletics', 'league': 'American League', 'league_short': 'AL', 'division': 'AL West', 'division_short': 'AL West'},
    136: {'abbr': 'SEA', 'name': 'Mariners', 'display': 'Seattle Mariners', 'league': 'American League', 'league_short': 'AL', 'division': 'AL West', 'division_short': 'AL West'},
    140: {'abbr': 'TEX', 'name': 'Rangers', 'display': 'Texas Rangers', 'league': 'American League', 'league_short': 'AL', 'division': 'AL West', 'division_short': 'AL West'},
    
    # National League East
    144: {'abbr': 'ATL', 'name': 'Braves', 'display': 'Atlanta Braves', 'league': 'National League', 'league_short': 'NL', 'division': 'NL East', 'division_short': 'NL East'},
    146: {'abbr': 'MIA', 'name': 'Marlins', 'display': 'Miami Marlins', 'league': 'National League', 'league_short': 'NL', 'division': 'NL East', 'division_short': 'NL East'},
    121: {'abbr': 'NYM', 'name': 'Mets', 'display': 'New York Mets', 'league': 'National League', 'league_short': 'NL', 'division': 'NL East', 'division_short': 'NL East'},
    143: {'abbr': 'PHI', 'name': 'Phillies', 'display': 'Philadelphia Phillies', 'league': 'National League', 'league_short': 'NL', 'division': 'NL East', 'division_short': 'NL East'},
    120: {'abbr': 'WSH', 'name': 'Nationals', 'display': 'Washington Nationals', 'league': 'National League', 'league_short': 'NL', 'division': 'NL East', 'division_short': 'NL East'},
    
    # National League Central
    112: {'abbr': 'CHC', 'name': 'Cubs', 'display': 'Chicago Cubs', 'league': 'National League', 'league_short': 'NL', 'division': 'NL Central', 'division_short': 'NL Central'},
    113: {'abbr': 'CIN', 'name': 'Reds', 'display': 'Cincinnati Reds', 'league': 'National League', 'league_short': 'NL', 'division': 'NL Central', 'division_short': 'NL Central'},
    158: {'abbr': 'MIL', 'name': 'Brewers', 'display': 'Milwaukee Brewers', 'league': 'National League', 'league_short': 'NL', 'division': 'NL Central', 'division_short': 'NL Central'},
    134: {'abbr': 'PIT', 'name': 'Pirates', 'display': 'Pittsburgh Pirates', 'league': 'National League', 'league_short': 'NL', 'division': 'NL Central', 'division_short': 'NL Central'},
    138: {'abbr': 'STL', 'name': 'Cardinals', 'display': 'St. Louis Cardinals', 'league': 'National League', 'league_short': 'NL', 'division': 'NL Central', 'division_short': 'NL Central'},
    
    # National League West
    109: {'abbr': 'AZ', 'name': 'Diamondbacks', 'display': 'Arizona Diamondbacks', 'league': 'National League', 'league_short': 'NL', 'division': 'NL West', 'division_short': 'NL West'},
    115: {'abbr': 'COL', 'name': 'Rockies', 'display': 'Colorado Rockies', 'league': 'National League', 'league_short': 'NL', 'division': 'NL West', 'division_short': 'NL West'},
    119: {'abbr': 'LAD', 'name': 'Dodgers', 'display': 'Los Angeles Dodgers', 'league': 'National League', 'league_short': 'NL', 'division': 'NL West', 'division_short': 'NL West'},
    135: {'abbr': 'SD', 'name': 'Padres', 'display': 'San Diego Padres', 'league': 'National League', 'league_short': 'NL', 'division': 'NL West', 'division_short': 'NL West'},
    137: {'abbr': 'SF', 'name': 'Giants', 'display': 'San Francisco Giants', 'league': 'National League', 'league_short': 'NL', 'division': 'NL West', 'division_short': 'NL West'},
}

# Special handling for Astros pre-2013 (they were in NL Central)
def get_team_metadata(team_id, year):
    """Get team metadata, accounting for historical changes."""
    metadata = TEAM_METADATA[team_id].copy()
    
    # Astros moved from NL Central to AL West in 2013
    if team_id == 117 and year < 2013:
        metadata['league'] = 'National League'
        metadata['league_short'] = 'NL'
        metadata['division'] = 'NL Central'
        metadata['division_short'] = 'NL Central'
    
    return metadata


def process_year(year, verbose=True):
    """Process one year's worth of games."""
    
    if verbose:
        print("="*80)
        print(f"COMPUTING TEAM SEASON STANDINGS FOR {year}")
        print("="*80)
        print()
    
    # Load all boxscores for this year
    boxscore_pattern = f'data/{year}_data/mlb_data/raw/boxscores/boxscores_*.csv'
    boxscore_files = sorted(glob.glob(boxscore_pattern))
    
    if not boxscore_files:
        print(f"❌ No boxscore files found for {year}")
        return
    
    if verbose:
        print(f"Loading {len(boxscore_files)} boxscore files...")
    
    boxscores = pd.concat([pd.read_csv(f) for f in boxscore_files], ignore_index=True)
    
    if verbose:
        print(f"Loaded {len(boxscores)} games")
        print()
    
    # Sort by date to process chronologically
    boxscores['date_dt'] = pd.to_datetime(boxscores['date'])
    boxscores = boxscores.sort_values('date_dt').reset_index(drop=True)
    
    # Initialize team tracking dictionary
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
        'last_10_results': [],
        'streak_type': None,
        'streak_count': 0,
        'division_wins': 0,
        'division_losses': 0,
        'league_wins': 0,
        'league_losses': 0
    })
    
    # Create output directory
    output_dir = f'data/{year}_data/mlb_data/raw/team_season_standings'
    os.makedirs(output_dir, exist_ok=True)
    
    standings_data = []
    
    if verbose:
        print("Processing games chronologically...")
        print()
    
    for idx, game in boxscores.iterrows():
        if verbose and idx % 500 == 0 and idx > 0:
            print(f"  Processed {idx}/{len(boxscores)} games...")
        
        home_team_id = int(game['home_team_id'])
        away_team_id = int(game['away_team_id'])
        home_abbr = game['home_team_abbreviation']
        away_abbr = game['away_team_abbreviation']
        
        # Get team metadata
        home_meta = get_team_metadata(home_team_id, year)
        away_meta = get_team_metadata(away_team_id, year)
        
        # Get current standings BEFORE this game
        home_standing = team_stats[home_abbr].copy()
        away_standing = team_stats[away_abbr].copy()
        
        # Calculate derived stats
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
        
        # Home/road records
        home_home_record = f"{home_standing['home_wins']}-{home_standing['home_losses']}"
        away_home_record = f"{away_standing['home_wins']}-{away_standing['home_losses']}"
        home_road_record = f"{home_standing['road_wins']}-{home_standing['road_losses']}"
        away_road_record = f"{away_standing['road_wins']}-{away_standing['road_losses']}"
        
        # Calculate league/division win percentages
        home_league_wp = home_standing['league_wins'] / (home_standing['league_wins'] + home_standing['league_losses']) if (home_standing['league_wins'] + home_standing['league_losses']) > 0 else 0.0
        away_league_wp = away_standing['league_wins'] / (away_standing['league_wins'] + away_standing['league_losses']) if (away_standing['league_wins'] + away_standing['league_losses']) > 0 else 0.0
        
        home_div_wp = home_standing['division_wins'] / (home_standing['division_wins'] + home_standing['division_losses']) if (home_standing['division_wins'] + home_standing['division_losses']) > 0 else 0.0
        away_div_wp = away_standing['division_wins'] / (away_standing['division_wins'] + away_standing['division_losses']) if (away_standing['division_wins'] + away_standing['division_losses']) > 0 else 0.0
        
        # Check if divisional game
        is_divisional = (home_meta['division'] == away_meta['division'])
        
        # Build standings row
        standings_row = {
            'game_pk': game['game_pk'],
            'date': game['date'],
            'home_team_id': home_team_id,
            'away_team_id': away_team_id,
            'home_team_abbreviation': home_abbr,
            'away_team_abbreviation': away_abbr,
            'home_team_display_name': home_meta['display'],
            'away_team_display_name': away_meta['display'],
            'home_team_name': home_meta['name'],
            'away_team_name': away_meta['name'],
            'home_league_name': home_meta['league'],
            'away_league_name': away_meta['league'],
            'home_league_short_name': home_meta['league_short'],
            'away_league_short_name': away_meta['league_short'],
            'home_division_name': home_meta['division'],
            'away_division_name': away_meta['division'],
            'home_division_short_name': home_meta['division_short'],
            'away_division_short_name': away_meta['division_short'],
            'home_season': year,
            'away_season': year,
            'home_games_played': home_gp,
            'away_games_played': away_gp,
            'home_wins': home_standing['wins'],
            'away_wins': away_standing['wins'],
            'home_losses': home_standing['losses'],
            'away_losses': away_standing['losses'],
            'home_win_percent': round(home_win_pct, 3),
            'away_win_percent': round(away_win_pct, 3),
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
            'home_games_behind': 0.0,  # Placeholder
            'away_games_behind': 0.0,  # Placeholder
            'home_division_games_behind': 0.0,  # Placeholder
            'away_division_games_behind': 0.0,  # Placeholder
            'home_league_win_percent': round(home_league_wp, 3),
            'away_league_win_percent': round(away_league_wp, 3),
            'home_division_win_percent': round(home_div_wp, 3),
            'away_division_win_percent': round(away_div_wp, 3),
            'home_home_wins': home_standing['home_wins'],
            'away_home_wins': away_standing['home_wins'],
            'home_home_losses': home_standing['home_losses'],
            'away_home_losses': away_standing['home_losses'],
            'home_road_wins': home_standing['road_wins'],
            'away_road_wins': away_standing['road_wins'],
            'home_road_losses': home_standing['road_losses'],
            'away_road_losses': away_standing['road_losses'],
            'home_streak': home_streak,
            'away_streak': away_streak,
            'home_playoff_seed': 0,  # Placeholder
            'away_playoff_seed': 0,  # Placeholder
            'home_playoff_percent': 0.0,  # Placeholder
            'away_playoff_percent': 0.0,  # Placeholder
            'home_wildcard_percent': 0.0,  # Placeholder
            'away_wildcard_percent': 0.0,  # Placeholder
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
            'is_divisional_game': is_divisional
        }
        
        standings_data.append(standings_row)
        
        # NOW update team stats with this game's results
        home_runs = int(game['home_batting_r'])
        away_runs = int(game['away_batting_r'])
        home_won = home_runs > away_runs
        away_won = away_runs > home_runs
        
        # Update games played
        team_stats[home_abbr]['games_played'] += 1
        team_stats[away_abbr]['games_played'] += 1
        
        # Update wins/losses
        if home_won:
            team_stats[home_abbr]['wins'] += 1
            team_stats[away_abbr]['losses'] += 1
            home_result = 'W'
            away_result = 'L'
        else:
            team_stats[home_abbr]['losses'] += 1
            team_stats[away_abbr]['wins'] += 1
            home_result = 'L'
            away_result = 'W'
        
        # Update points
        team_stats[home_abbr]['points_for'] += home_runs
        team_stats[home_abbr]['points_against'] += away_runs
        team_stats[away_abbr]['points_for'] += away_runs
        team_stats[away_abbr]['points_against'] += home_runs
        
        # Update home/road splits
        if home_won:
            team_stats[home_abbr]['home_wins'] += 1
            team_stats[away_abbr]['road_losses'] += 1
        else:
            team_stats[home_abbr]['home_losses'] += 1
            team_stats[away_abbr]['road_wins'] += 1
        
        # Update streaks
        for team, result in [(home_abbr, home_result), (away_abbr, away_result)]:
            if team_stats[team]['streak_type'] == result:
                team_stats[team]['streak_count'] += 1
            else:
                team_stats[team]['streak_type'] = result
                team_stats[team]['streak_count'] = 1
        
        # Update last 10
        for team, result in [(home_abbr, home_result), (away_abbr, away_result)]:
            team_stats[team]['last_10_results'].append(result)
            if len(team_stats[team]['last_10_results']) > 10:
                team_stats[team]['last_10_results'].pop(0)
        
        # Update division/league records
        same_league = (home_meta['league'] == away_meta['league'])
        same_division = is_divisional
        
        if same_league:
            team_stats[home_abbr]['league_wins'] += 1 if home_won else 0
            team_stats[home_abbr]['league_losses'] += 0 if home_won else 1
            team_stats[away_abbr]['league_wins'] += 1 if away_won else 0
            team_stats[away_abbr]['league_losses'] += 0 if away_won else 1
        
        if same_division:
            team_stats[home_abbr]['division_wins'] += 1 if home_won else 0
            team_stats[home_abbr]['division_losses'] += 0 if home_won else 1
            team_stats[away_abbr]['division_wins'] += 1 if away_won else 0
            team_stats[away_abbr]['division_losses'] += 0 if away_won else 1
    
    if verbose:
        print(f"  Processed {len(boxscores)}/{len(boxscores)} games... DONE")
        print()
    
    # Create DataFrame
    standings_df = pd.DataFrame(standings_data)
    
    # Save by date
    if verbose:
        print(f"Saving standings files by date...")
    
    saved_files = 0
    for date_str, group in standings_df.groupby('date'):
        file_path = f'{output_dir}/team_season_standings_{date_str}.csv'
        group.to_csv(file_path, index=False)
        saved_files += 1
    
    if verbose:
        print(f"✓ Saved {saved_files} files to {output_dir}/")
        print()
        print("="*80)
        print(f"SUMMARY FOR {year}")
        print("="*80)
        print(f"  Total games processed: {len(standings_df):,}")
        print(f"  Files created: {saved_files}")
        print(f"  Output directory: {output_dir}")
        print("="*80)
        print()
    
    return {
        'year': year,
        'games': len(standings_df),
        'files': saved_files
    }


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        years = [int(y) for y in sys.argv[1:]]
    else:
        years = list(range(2009, 2025))
    
    print("="*80)
    print("TEAM SEASON STANDINGS COMPUTATION - HISTORICAL YEARS")
    print("="*80)
    print(f"\nYears to process: {', '.join(map(str, years))}")
    print()
    
    results = []
    
    for year in years:
        result = process_year(year, verbose=True)
        if result:
            results.append(result)
    
    # Final summary
    if len(results) > 1:
        print("="*80)
        print("FINAL SUMMARY - ALL YEARS")
        print("="*80)
        
        total_games = sum(r['games'] for r in results)
        total_files = sum(r['files'] for r in results)
        
        print(f"\nTotal games processed: {total_games:,}")
        print(f"Total files created:   {total_files:,}")
        
        print(f"\nBreakdown by year:")
        for r in results:
            print(f"  {r['year']}: {r['files']:3d} files, {r['games']:5,d} games")
        
        print("="*80)


if __name__ == "__main__":
    main()
