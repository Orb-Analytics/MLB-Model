#!/usr/bin/env python3
"""
ETL Script: Calculate Cumulative Team Season Standings

IMPORTANT: This script calculates standings progressively to avoid data leakage.
For each game, the standings reflect only games played BEFORE that game.

Approach:
1. Load ALL game_outlook CSVs and sort chronologically
2. For each team, maintain running cumulative stats (wins, losses, points, streaks, etc.)
3. For each game, record the standings as of BEFORE that game starts
4. Update running stats with that game's outcome after recording
5. First game of season for each team will have all zeros/nulls

Output Schema (76 columns total):
- Original 4 columns from game outlook: id, date, home_team_id, away_team_id
- 36 home team standings columns (home_ prefix) - stats BEFORE this game
- 36 away team standings columns (away_ prefix) - stats BEFORE this game
- Columns alternate home/away for each stat type

Usage:
    # Process and save all dates:
    python src/etl/fetch_team_season_standings.py
    
    # Process all dates but only save specific range:
    python src/etl/fetch_team_season_standings.py --start-date 2025-03-31 --end-date 2025-04-30
    
    Note: Always processes ALL games from season start to maintain cumulative accuracy.
    Date filters only affect which results are saved to files.
"""

import os
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import deque
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Directory paths
GAME_OUTLOOK_DIR = Path('data/bdl_data/game_outlook')
OUTPUT_DIR = Path('data/bdl_data/team_season_standings')

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Output column order (76 columns total) - alternating home/away for each stat type
OUTPUT_COLUMNS = [
    'id', 'date', 'home_team_id', 'away_team_id',
    # Team identifiers (alternating)
    'home_team_abbreviation', 'away_team_abbreviation',
    'home_team_display_name', 'away_team_display_name',
    'home_team_name', 'away_team_name',
    'home_league_name', 'away_league_name',
    'home_league_short_name', 'away_league_short_name',
    'home_division_name', 'away_division_name',
    'home_division_short_name', 'away_division_short_name',
    # Cumulative stats (alternating)
    'home_season', 'away_season',
    'home_games_played', 'away_games_played',
    'home_wins', 'away_wins',
    'home_losses', 'away_losses',
    'home_win_percent', 'away_win_percent',
    'home_points_for', 'away_points_for',
    'home_points_against', 'away_points_against',
    'home_point_differential', 'away_point_differential',
    'home_avg_points_for', 'away_avg_points_for',
    'home_avg_points_against', 'away_avg_points_against',
    'home_differential', 'away_differential',
    'home_games_behind', 'away_games_behind',
    'home_division_games_behind', 'away_division_games_behind',
    'home_league_win_percent', 'away_league_win_percent',
    'home_division_win_percent', 'away_division_win_percent',
    'home_home_wins', 'away_home_wins',
    'home_home_losses', 'away_home_losses',
    'home_road_wins', 'away_road_wins',
    'home_road_losses', 'away_road_losses',
    'home_streak', 'away_streak',
    'home_playoff_seed', 'away_playoff_seed',
    'home_playoff_percent', 'away_playoff_percent',
    'home_wildcard_percent', 'away_wildcard_percent',
    'home_total', 'away_total',
    'home_home', 'away_home',
    'home_road', 'away_road',
    'home_intra_division', 'away_intra_division',
    'home_intra_league', 'away_intra_league',
    'home_last_ten_games', 'away_last_ten_games',
]


class TeamStats:
    """Track cumulative stats for a team throughout the season"""
    
    def __init__(self, team_id: int, team_info: Dict[str, Any]):
        self.team_id = team_id
        self.abbreviation = team_info.get('abbreviation', '')
        self.display_name = team_info.get('display_name', '')
        self.name = team_info.get('name', '')
        self.league_name = team_info.get('league_name', '')
        self.league_short_name = team_info.get('league_short_name', '')
        self.division_name = team_info.get('division_name', '')
        self.division_short_name = team_info.get('division_short_name', '')
        
        # Cumulative stats
        self.games_played = 0
        self.wins = 0
        self.losses = 0
        self.points_for = 0
        self.points_against = 0
        self.home_wins = 0
        self.home_losses = 0
        self.road_wins = 0
        self.road_losses = 0
        
        # Recent games tracking
        self.last_10 = deque(maxlen=10)  # 'W' or 'L'
        self.streak_list = []  # All W/L results in order
        
        # Division/League tracking (opponents' info needed)
        self.division_wins = 0
        self.division_losses = 0
        self.league_wins = 0
        self.league_losses = 0
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Return current cumulative stats as a dictionary"""
        win_pct = self.wins / self.games_played if self.games_played > 0 else 0.0
        avg_pf = self.points_for / self.games_played if self.games_played > 0 else 0.0
        avg_pa = self.points_against / self.games_played if self.games_played > 0 else 0.0
        differential = self.points_for - self.points_against
        
        # Calculate streak
        streak = self._calculate_streak()
        
        # Calculate last 10 record
        last_10_wins = self.last_10.count('W')
        last_10_losses = self.last_10.count('L')
        last_10_record = f"{last_10_wins}-{last_10_losses}" if len(self.last_10) > 0 else "0-0"
        
        # League and division win percentages
        league_win_pct = self.league_wins / (self.league_wins + self.league_losses) if (self.league_wins + self.league_losses) > 0 else 0.0
        division_win_pct = self.division_wins / (self.division_wins + self.division_losses) if (self.division_wins + self.division_losses) > 0 else 0.0
        
        return {
            'team_abbreviation': self.abbreviation,
            'team_display_name': self.display_name,
            'team_name': self.name,
            'league_name': self.league_name,
            'league_short_name': self.league_short_name,
            'division_name': self.division_name,
            'division_short_name': self.division_short_name,
            'season': 2025,
            'games_played': self.games_played,
            'wins': self.wins,
            'losses': self.losses,
            'win_percent': win_pct,
            'points_for': self.points_for,
            'points_against': self.points_against,
            'point_differential': differential,
            'avg_points_for': avg_pf,
            'avg_points_against': avg_pa,
            'differential': differential,  # Same as point_differential
            'games_behind': 0.0,  # Will be calculated relative to division leader
            'division_games_behind': 0.0,  # Will be calculated
            'league_win_percent': league_win_pct,
            'division_win_percent': division_win_pct,
            'home_wins': self.home_wins,
            'home_losses': self.home_losses,
            'road_wins': self.road_wins,
            'road_losses': self.road_losses,
            'streak': streak,
            'playoff_seed': None,  # Not calculated
            'playoff_percent': None,
            'wildcard_percent': None,
            'total': f"{self.wins}-{self.losses}" if self.games_played > 0 else "0-0",
            'home': f"{self.home_wins}-{self.home_losses}" if (self.home_wins + self.home_losses) > 0 else "0-0",
            'road': f"{self.road_wins}-{self.road_losses}" if (self.road_wins + self.road_losses) > 0 else "0-0",
            'intra_division': f"{self.division_wins}-{self.division_losses}" if (self.division_wins + self.division_losses) > 0 else "0-0",
            'intra_league': f"{self.league_wins}-{self.league_losses}" if (self.league_wins + self.league_losses) > 0 else "0-0",
            'last_ten_games': last_10_record
        }
    
    def _calculate_streak(self) -> str:
        """Calculate current win/loss streak"""
        if not self.streak_list:
            return "0"
        
        current = self.streak_list[-1]
        count = 1
        for i in range(len(self.streak_list) - 2, -1, -1):
            if self.streak_list[i] == current:
                count += 1
            else:
                break
        
        return f"{count}{current}" if current else "0"
    
    def update_after_game(self, won: bool, is_home: bool, points_for: int, points_against: int,
                          is_division_game: bool, is_league_game: bool):
        """Update stats after a game completes"""
        self.games_played += 1
        
        if won:
            self.wins += 1
            self.last_10.append('W')
            self.streak_list.append('W')
            if is_home:
                self.home_wins += 1
            else:
                self.road_wins += 1
            if is_division_game:
                self.division_wins += 1
            if is_league_game:
                self.league_wins += 1
        else:
            self.losses += 1
            self.last_10.append('L')
            self.streak_list.append('L')
            if is_home:
                self.home_losses += 1
            else:
                self.road_losses += 1
            if is_division_game:
                self.division_losses += 1
            if is_league_game:
                self.league_losses += 1
        
        self.points_for += points_for
        self.points_against += points_against


def load_all_game_outlook_files() -> pd.DataFrame:
    """Load all game_outlook CSV files and combine into one DataFrame"""
    logger.info(f"Loading all game outlook files from {GAME_OUTLOOK_DIR}")
    
    all_games = []
    csv_files = sorted(GAME_OUTLOOK_DIR.glob('game_outlook_*.csv'))
    
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        all_games.append(df)
        logger.debug(f"Loaded {len(df)} games from {csv_file.name}")
    
    if not all_games:
        logger.error("No game outlook files found")
        return pd.DataFrame()
    
    combined_df = pd.concat(all_games, ignore_index=True)
    logger.info(f"Loaded {len(combined_df)} total games from {len(csv_files)} files")
    
    # Sort by date to process chronologically
    combined_df['date'] = pd.to_datetime(combined_df['date'])
    combined_df = combined_df.sort_values('date').reset_index(drop=True)
    
    return combined_df


def initialize_team_stats(games_df: pd.DataFrame) -> Dict[int, TeamStats]:
    """Initialize TeamStats objects for all teams from the first occurrence"""
    team_stats = {}
    
    # Get unique teams and their info from the games
    for _, game in games_df.iterrows():
        # Home team
        if game['home_team_id'] not in team_stats:
            team_info = {
                'abbreviation': game['home_team_abbreviation'],
                'display_name': game['home_team_display_name'],
                'name': game['home_team_name'],
                'league_name': game.get('home_team_league', ''),
                'league_short_name': game.get('home_team_league', ''),  # Use first letter or abbreviation
                'division_name': game.get('home_team_division', ''),
                'division_short_name': game.get('home_team_division', ''),  # Same as division_name
            }
            team_stats[game['home_team_id']] = TeamStats(game['home_team_id'], team_info)
        
        # Away team
        if game['away_team_id'] not in team_stats:
            team_info = {
                'abbreviation': game['away_team_abbreviation'],
                'display_name': game['away_team_display_name'],
                'name': game['away_team_name'],
                'league_name': game.get('away_team_league', ''),
                'league_short_name': game.get('away_team_league', ''),  # Use first letter or abbreviation
                'division_name': game.get('away_team_division', ''),
                'division_short_name': game.get('away_team_division', ''),  # Same as division_name
            }
            team_stats[game['away_team_id']] = TeamStats(game['away_team_id'], team_info)
    
    logger.info(f"Initialized {len(team_stats)} teams")
    return team_stats


def calculate_games_behind(team_stats: Dict[int, TeamStats]) -> Dict[int, float]:
    """Calculate games behind for each team relative to their division leader"""
    games_behind = {}
    
    # Group teams by division
    divisions = {}
    for team_id, stats in team_stats.items():
        division = stats.division_name
        if division not in divisions:
            divisions[division] = []
        divisions[division].append((team_id, stats))
    
    # For each division, find leader and calculate games behind
    for division, teams in divisions.items():
        if not teams:
            continue
        
        # Find division leader (most wins, or best win% if tied)
        leader_wins = max(stats.wins for _, stats in teams)
        leader_losses = min(stats.losses for _, stats in teams if stats.wins == leader_wins)
        
        for team_id, stats in teams:
            # Games Behind = ((Leader Wins - Team Wins) + (Team Losses - Leader Losses)) / 2
            gb = ((leader_wins - stats.wins) + (stats.losses - leader_losses)) / 2.0
            games_behind[team_id] = gb
    
    return games_behind


def process_all_games(games_df: pd.DataFrame) -> pd.DataFrame:
    """Process all games chronologically and calculate cumulative standings"""
    logger.info("Processing games chronologically to calculate cumulative standings")
    
    # Initialize team stats
    team_stats = initialize_team_stats(games_df)
    
    # Process each game
    results = []
    
    for idx, game in games_df.iterrows():
        game_id = game['id']
        game_date = game['date']
        home_team_id = game['home_team_id']
        away_team_id = game['away_team_id']
        home_score = game.get('home_team_score', 0)
        away_score = game.get('away_team_score', 0)
        
        # Get current standings BEFORE this game
        home_stats = team_stats[home_team_id].get_current_stats()
        away_stats = team_stats[away_team_id].get_current_stats()
        
        # Calculate games behind
        games_behind = calculate_games_behind(team_stats)
        home_stats['games_behind'] = games_behind.get(home_team_id, 0.0)
        away_stats['games_behind'] = games_behind.get(away_team_id, 0.0)
        home_stats['division_games_behind'] = games_behind.get(home_team_id, 0.0)  # Same for now
        away_stats['division_games_behind'] = games_behind.get(away_team_id, 0.0)
        
        # Build output row with alternating home/away columns
        row = {
            'id': game_id,
            'date': game_date,
            'home_team_id': home_team_id,
            'away_team_id': away_team_id,
            # Team identifiers
            'home_team_abbreviation': home_stats['team_abbreviation'],
            'away_team_abbreviation': away_stats['team_abbreviation'],
            'home_team_display_name': home_stats['team_display_name'],
            'away_team_display_name': away_stats['team_display_name'],
            'home_team_name': home_stats['team_name'],
            'away_team_name': away_stats['team_name'],
            'home_league_name': home_stats['league_name'],
            'away_league_name': away_stats['league_name'],
            'home_league_short_name': home_stats['league_short_name'],
            'away_league_short_name': away_stats['league_short_name'],
            'home_division_name': home_stats['division_name'],
            'away_division_name': away_stats['division_name'],
            'home_division_short_name': home_stats['division_short_name'],
            'away_division_short_name': away_stats['division_short_name'],
            # Cumulative stats
            'home_season': home_stats['season'],
            'away_season': away_stats['season'],
            'home_games_played': home_stats['games_played'],
            'away_games_played': away_stats['games_played'],
            'home_wins': home_stats['wins'],
            'away_wins': away_stats['wins'],
            'home_losses': home_stats['losses'],
            'away_losses': away_stats['losses'],
            'home_win_percent': home_stats['win_percent'],
            'away_win_percent': away_stats['win_percent'],
            'home_points_for': home_stats['points_for'],
            'away_points_for': away_stats['points_for'],
            'home_points_against': home_stats['points_against'],
            'away_points_against': away_stats['points_against'],
            'home_point_differential': home_stats['point_differential'],
            'away_point_differential': away_stats['point_differential'],
            'home_avg_points_for': home_stats['avg_points_for'],
            'away_avg_points_for': away_stats['avg_points_for'],
            'home_avg_points_against': home_stats['avg_points_against'],
            'away_avg_points_against': away_stats['avg_points_against'],
            'home_differential': home_stats['differential'],
            'away_differential': away_stats['differential'],
            'home_games_behind': home_stats['games_behind'],
            'away_games_behind': away_stats['games_behind'],
            'home_division_games_behind': home_stats['division_games_behind'],
            'away_division_games_behind': away_stats['division_games_behind'],
            'home_league_win_percent': home_stats['league_win_percent'],
            'away_league_win_percent': away_stats['league_win_percent'],
            'home_division_win_percent': home_stats['division_win_percent'],
            'away_division_win_percent': away_stats['division_win_percent'],
            'home_home_wins': home_stats['home_wins'],
            'away_home_wins': away_stats['home_wins'],
            'home_home_losses': home_stats['home_losses'],
            'away_home_losses': away_stats['home_losses'],
            'home_road_wins': home_stats['road_wins'],
            'away_road_wins': away_stats['road_wins'],
            'home_road_losses': home_stats['road_losses'],
            'away_road_losses': away_stats['road_losses'],
            'home_streak': home_stats['streak'],
            'away_streak': away_stats['streak'],
            'home_playoff_seed': home_stats['playoff_seed'],
            'away_playoff_seed': away_stats['playoff_seed'],
            'home_playoff_percent': home_stats['playoff_percent'],
            'away_playoff_percent': away_stats['playoff_percent'],
            'home_wildcard_percent': home_stats['wildcard_percent'],
            'away_wildcard_percent': away_stats['wildcard_percent'],
            'home_total': home_stats['total'],
            'away_total': away_stats['total'],
            'home_home': home_stats['home'],
            'away_home': away_stats['home'],
            'home_road': home_stats['road'],
            'away_road': away_stats['road'],
            'home_intra_division': home_stats['intra_division'],
            'away_intra_division': away_stats['intra_division'],
            'home_intra_league': home_stats['intra_league'],
            'away_intra_league': away_stats['intra_league'],
            'home_last_ten_games': home_stats['last_ten_games'],
            'away_last_ten_games': away_stats['last_ten_games'],
        }
        
        results.append(row)
        
        # NOW update team stats with this game's outcome (for future games)
        if pd.notna(home_score) and pd.notna(away_score):
            home_won = home_score > away_score
            away_won = away_score > home_score
            
            # Determine if division/league game
            home_team = team_stats[home_team_id]
            away_team = team_stats[away_team_id]
            is_division_game = (home_team.division_name == away_team.division_name)
            is_league_game = (home_team.league_name == away_team.league_name)
            
            # Update home team
            team_stats[home_team_id].update_after_game(
                won=home_won,
                is_home=True,
                points_for=int(home_score),
                points_against=int(away_score),
                is_division_game=is_division_game,
                is_league_game=is_league_game
            )
            
            # Update away team
            team_stats[away_team_id].update_after_game(
                won=away_won,
                is_home=False,
                points_for=int(away_score),
                points_against=int(home_score),
                is_division_game=is_division_game,
                is_league_game=is_league_game
            )
        
        if (idx + 1) % 100 == 0:
            logger.info(f"Processed {idx + 1}/{len(games_df)} games")
    
    logger.info(f"Completed processing {len(results)} games")
    
    # Convert to DataFrame with correct column order
    results_df = pd.DataFrame(results)
    results_df = results_df[OUTPUT_COLUMNS]
    
    return results_df


def save_by_date(results_df: pd.DataFrame):
    """Save results grouped by date to separate CSV files"""
    logger.info("Saving results grouped by date")
    
    # Convert date back to string for grouping
    results_df['date_str'] = pd.to_datetime(results_df['date']).dt.strftime('%Y-%m-%d')
    
    date_groups = results_df.groupby('date_str')
    
    for date_str, group_df in date_groups:
        output_file = OUTPUT_DIR / f'team_season_standings_{date_str}.csv'
        
        # Drop the temporary date_str column
        group_df = group_df.drop('date_str', axis=1)
        
        # Save to CSV
        group_df.to_csv(output_file, index=False)
        logger.info(f"Saved {len(group_df)} games to {output_file.name}")
    
    logger.info(f"Saved standings for {len(date_groups)} dates")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Calculate cumulatto SAVE results (YYYY-MM-DD) - still processes all games from season start')
    parser.add_argument('--end-date', type=str, help='End date to SAVE results (YYYY-MM-DD)')
    args = parser.parse_args()
    
    logger.info("Starting cumulative team season standings calculation")
    
    # Load all games (MUST process ALL to get cumulative stats)
    games_df = load_all_game_outlook_files()
    
    if games_df.empty:
        logger.error("No games loaded. Exiting.")
        return
    
    # Process ALL games to build cumulative standings
    results_df = process_all_games(games_df)
    
    # Filter results by date range if specified (for SAVING only)
    if args.start_date:
        start_date = pd.to_datetime(args.start_date).tz_localize('UTC')
        results_df = results_df[results_df['date'] >= start_date]
        logger.info(f"Filtered to save games on or after {args.start_date}")
    
    if args.end_date:
        end_date = pd.to_datetime(args.end_date).tz_localize('UTC')
        results_df = results_df[results_df['date'] <= end_date]
        logger.info(f"Filtered to save games on or before {args.end_date}"
    results_df = process_all_games(games_df)
    
    # Save results by date
    save_by_date(results_df)
    
    logger.info("Cumulative team season standings calculation complete")


if __name__ == '__main__':
    main()
