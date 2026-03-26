"""
Compute Team Bullpen Boxscores for Historical Years (2009-2024)

Purpose:
    For each game, compute bullpen stats by subtracting starting pitcher stats
    from team total stats.
    
Approach:
    Bullpen Stats = Team Total Stats - Starting Pitcher Stats
    
Input:
    - data/{year}_data/mlb_data/raw/boxscores/boxscores_YYYY-MM-DD.csv
    - data/{year}_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_YYYY-MM-DD.csv
    
Output:
    - data/{year}_data/mlb_data/raw/team_bullpen_boxscores/team_bullpen_boxscores_YYYY-MM-DD.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

def safe_divide(numerator, denominator, default=0.0):
    """Safely divide, returning default if denominator is 0."""
    if denominator == 0 or pd.isna(denominator):
        return default
    return numerator / denominator


def compute_bullpen_stats_for_game(team_row, starter_row, side):
    """
    Compute bullpen stats for one team in one game.
    
    Args:
        team_row: Row from team boxscore
        starter_row: Row from starting pitcher boxscore
        side: 'home' or 'away'
    
    Returns:
        dict: Bullpen stats
    """
    # Extract team stats
    team_ip = team_row[f'{side}_pitching_ip']
    team_h = team_row[f'{side}_pitching_h']
    team_er = team_row[f'{side}_pitching_er']
    team_bb = team_row[f'{side}_pitching_bb']
    team_k = team_row[f'{side}_pitching_k']
    team_hr = team_row[f'{side}_pitching_hr']
    
    # Extract starter stats
    starter_ip = starter_row[f'{side}_starter_ip']
    starter_h = starter_row[f'{side}_starter_hits']
    starter_er = starter_row[f'{side}_starter_earned_runs']
    starter_bb = starter_row[f'{side}_starter_walks']
    starter_k = starter_row[f'{side}_starter_strikeouts']
    starter_hr = starter_row[f'{side}_starter_homeruns']
    
    # Compute bullpen counting stats (team - starter)
    bullpen_ip = team_ip - starter_ip
    bullpen_h = team_h - starter_h
    bullpen_er = team_er - starter_er
    bullpen_bb = team_bb - starter_bb
    bullpen_k = team_k - starter_k
    bullpen_hr = team_hr - starter_hr
    
    # Handle negative values (data quality issues)
    if bullpen_ip < 0:
        print(f"    WARNING: Negative bullpen IP for {side} team: {bullpen_ip:.1f}")
        bullpen_ip = 0.0
    if bullpen_h < 0:
        print(f"    WARNING: Negative bullpen hits for {side} team: {bullpen_h}")
        bullpen_h = 0
    if bullpen_er < 0:
        print(f"    WARNING: Negative bullpen ER for {side} team: {bullpen_er}")
        bullpen_er = 0
    if bullpen_bb < 0:
        print(f"    WARNING: Negative bullpen BB for {side} team: {bullpen_bb}")
        bullpen_bb = 0
    if bullpen_k < 0:
        print(f"    WARNING: Negative bullpen K for {side} team: {bullpen_k}")
        bullpen_k = 0
    if bullpen_hr < 0:
        print(f"    WARNING: Negative bullpen HR for {side} team: {bullpen_hr}")
        bullpen_hr = 0
    
    # Compute bullpen derived stats
    bullpen_era = safe_divide(bullpen_er * 9, bullpen_ip, 0.0)
    bullpen_whip = safe_divide(bullpen_h + bullpen_bb, bullpen_ip, 0.0)
    bullpen_k_per_9 = safe_divide(bullpen_k * 9, bullpen_ip, 0.0)
    bullpen_k_bb_ratio = safe_divide(bullpen_k, bullpen_bb, 0.0)
    bullpen_hr_per_9 = safe_divide(bullpen_hr * 9, bullpen_ip, 0.0)
    bullpen_bb_per_9 = safe_divide(bullpen_bb * 9, bullpen_ip, 0.0)
    
    # Return stats
    return {
        f'{side}_bullpen_ip': round(bullpen_ip, 1),
        f'{side}_bullpen_hits': int(bullpen_h),
        f'{side}_bullpen_earned_runs': int(bullpen_er),
        f'{side}_bullpen_walks': int(bullpen_bb),
        f'{side}_bullpen_strikeouts': int(bullpen_k),
        f'{side}_bullpen_homeruns': int(bullpen_hr),
        f'{side}_bullpen_era': round(bullpen_era, 2),
        f'{side}_bullpen_whip': round(bullpen_whip, 2),
        f'{side}_bullpen_k_per_9': round(bullpen_k_per_9, 2),
        f'{side}_bullpen_k_bb_ratio': round(bullpen_k_bb_ratio, 2),
        f'{side}_bullpen_hr_per_9': round(bullpen_hr_per_9, 2),
        f'{side}_bullpen_bb_per_9': round(bullpen_bb_per_9, 2),
    }


def process_date(year, date_str):
    """
    Process all games for a specific date in a specific year.
    
    Args:
        year: Year (e.g., 2024)
        date_str: Date string (YYYY-MM-DD)
    
    Returns:
        tuple: (success: bool, message: str, games_count: int)
    """
    # File paths
    team_file = Path(f"data/{year}_data/mlb_data/raw/boxscores/boxscores_{date_str}.csv")
    starter_file = Path(f"data/{year}_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_{date_str}.csv")
    output_file = Path(f"data/{year}_data/mlb_data/raw/team_bullpen_boxscores/team_bullpen_boxscores_{date_str}.csv")
    
    # Check if input files exist
    if not team_file.exists():
        return False, "Team boxscore not found", 0
    
    if not starter_file.exists():
        return False, "Starter boxscore not found", 0
    
    # Load data
    try:
        team_df = pd.read_csv(team_file)
        starter_df = pd.read_csv(starter_file)
    except Exception as e:
        return False, f"Error reading files: {e}", 0
    
    # Check row counts match
    if len(team_df) != len(starter_df):
        return False, f"Row count mismatch: team={len(team_df)}, starter={len(starter_df)}", 0
    
    # Verify game_pk alignment
    if not (team_df['game_pk'].values == starter_df['game_pk'].values).all():
        return False, "game_pk mismatch between files", 0
    
    # Compute bullpen stats for each game
    all_rows = []
    
    for idx in range(len(team_df)):
        team_row = team_df.iloc[idx]
        starter_row = starter_df.iloc[idx]
        
        # Start with game identifiers
        row = {
            'game_pk': starter_row['game_pk'],
            'date': date_str,
        }
        
        # Compute bullpen stats for home team
        home_stats = compute_bullpen_stats_for_game(team_row, starter_row, 'home')
        row.update(home_stats)
        
        # Compute bullpen stats for away team
        away_stats = compute_bullpen_stats_for_game(team_row, starter_row, 'away')
        row.update(away_stats)
        
        all_rows.append(row)
    
    # Create DataFrame with proper column order
    df = pd.DataFrame(all_rows)
    
    # Reorder columns to alternate home/away
    base_cols = ['game_pk', 'date']
    stat_cols = [
        'ip', 'hits', 'earned_runs', 'walks', 'strikeouts', 'homeruns',
        'era', 'whip', 'k_per_9', 'k_bb_ratio', 'hr_per_9', 'bb_per_9'
    ]
    
    ordered_cols = base_cols.copy()
    for stat in stat_cols:
        ordered_cols.append(f'home_bullpen_{stat}')
        ordered_cols.append(f'away_bullpen_{stat}')
    
    df = df[ordered_cols]
    
    # Save
    df.to_csv(output_file, index=False)
    
    return True, f"Saved {len(all_rows)} games", len(all_rows)


def process_year(year, verbose=True):
    """
    Process all dates for a specific year.
    
    Args:
        year: Year to process (e.g., 2024)
        verbose: Print progress messages
    
    Returns:
        dict: Statistics about processing
    """
    if verbose:
        print("="*80)
        print(f"COMPUTING TEAM BULLPEN BOXSCORES FOR {year}")
        print("="*80)
    
    # Ensure output directory exists
    output_dir = Path(f"data/{year}_data/mlb_data/raw/team_bullpen_boxscores")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all team boxscore files for this year
    boxscore_dir = Path(f"data/{year}_data/mlb_data/raw/boxscores")
    team_files = sorted(boxscore_dir.glob("boxscores_*.csv"))
    
    if verbose:
        print(f"\nFound {len(team_files)} team boxscore files")
        print(f"Output directory: {output_dir}")
        print()
    
    success_count = 0
    error_count = 0
    total_games = 0
    errors = []
    
    for i, filepath in enumerate(team_files, 1):
        # Extract date from filename (boxscores_2024-03-20.csv -> 2024-03-20)
        date_str = filepath.stem.replace('boxscores_', '')
        
        if verbose:
            print(f"[{i}/{len(team_files)}] Processing {date_str}...", end=' ')
        
        success, message, games_count = process_date(year, date_str)
        
        if success:
            success_count += 1
            total_games += games_count
            if verbose:
                print(f"✓ {message}")
        else:
            error_count += 1
            errors.append((date_str, message))
            if verbose:
                print(f"✗ {message}")
    
    if verbose:
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"  Year:       {year}")
        print(f"  Processed:  {success_count} files")
        print(f"  Errors:     {error_count} files")
        print(f"  Total:      {len(team_files)} files")
        print(f"  Games:      {total_games} games")
        
        if errors:
            print(f"\n  Errors encountered:")
            for date, msg in errors[:10]:  # Show first 10 errors
                print(f"    {date}: {msg}")
            if len(errors) > 10:
                print(f"    ... and {len(errors) - 10} more")
        
        print("="*80)
    
    return {
        'year': year,
        'total_files': len(team_files),
        'success': success_count,
        'errors': error_count,
        'games': total_games,
        'error_details': errors
    }


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Process specific year(s) from command line
        years = [int(y) for y in sys.argv[1:]]
    else:
        # Default: process all years 2009-2024
        years = list(range(2009, 2025))
    
    print("="*80)
    print("TEAM BULLPEN BOXSCORES COMPUTATION - HISTORICAL YEARS")
    print("="*80)
    print(f"\nYears to process: {', '.join(map(str, years))}")
    print()
    
    all_results = []
    
    for year in years:
        result = process_year(year, verbose=True)
        all_results.append(result)
        print()
    
    # Final summary
    if len(all_results) > 1:
        print("="*80)
        print("FINAL SUMMARY - ALL YEARS")
        print("="*80)
        
        total_files = sum(r['total_files'] for r in all_results)
        total_success = sum(r['success'] for r in all_results)
        total_errors = sum(r['errors'] for r in all_results)
        total_games = sum(r['games'] for r in all_results)
        
        print(f"\nTotal files processed:  {total_success} / {total_files}")
        print(f"Total errors:           {total_errors}")
        print(f"Total games computed:   {total_games:,}")
        
        print(f"\nBreakdown by year:")
        for r in all_results:
            print(f"  {r['year']}: {r['success']:3d} files, {r['games']:5d} games, {r['errors']} errors")
        
        print("="*80)


if __name__ == "__main__":
    main()
