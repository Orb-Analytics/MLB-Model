"""
Compute Team Bullpen Boxscores

Purpose:
    For each game, compute bullpen stats by subtracting starting pitcher stats
    from team total stats.
    
Approach:
    Bullpen Stats = Team Total Stats - Starting Pitcher Stats
    
Input:
    - data/mlb_data/team_boxscores/team_boxscores_YYYY-MM-DD.csv
    - data/mlb_data/starting_pitcher_boxscores/starting_pitcher_boxscores_YYYY-MM-DD.csv
    
Output:
    - data/mlb_data/team_bullpen_boxscores/team_bullpen_boxscores_YYYY-MM-DD.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Directories
TEAM_BOXSCORES_DIR = Path("data/mlb_data/team_boxscores")
STARTER_BOXSCORES_DIR = Path("data/mlb_data/starting_pitcher_boxscores")
OUTPUT_DIR = Path("data/mlb_data/team_bullpen_boxscores")

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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
    
    # Compute bullpen derived stats
    bullpen_era = safe_divide(bullpen_er * 9, bullpen_ip, 0.0)
    bullpen_whip = safe_divide(bullpen_h + bullpen_bb, bullpen_ip, 0.0)
    bullpen_k_per_9 = safe_divide(bullpen_k * 9, bullpen_ip, 0.0)
    bullpen_k_bb_ratio = safe_divide(bullpen_k, bullpen_bb, 0.0)
    bullpen_hr_per_9 = safe_divide(bullpen_hr * 9, bullpen_ip, 0.0)
    bullpen_bb_per_9 = safe_divide(bullpen_bb * 9, bullpen_ip, 0.0)
    
    # Round to 2 decimal places
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


def process_date(date_str):
    """
    Process all games for a specific date.
    
    Args:
        date_str: Date string (YYYY-MM-DD)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    # File paths
    team_file = TEAM_BOXSCORES_DIR / f"team_boxscores_{date_str}.csv"
    starter_file = STARTER_BOXSCORES_DIR / f"starting_pitcher_boxscores_{date_str}.csv"
    output_file = OUTPUT_DIR / f"team_bullpen_boxscores_{date_str}.csv"
    
    # Check if output already exists
    if output_file.exists():
        return True, "Already exists (skipped)"
    
    # Check if input files exist
    if not team_file.exists():
        return False, "Team boxscore not found"
    
    if not starter_file.exists():
        return False, "Starter boxscore not found"
    
    # Load data
    team_df = pd.read_csv(team_file)
    starter_df = pd.read_csv(starter_file)
    
    # Check row counts match
    if len(team_df) != len(starter_df):
        return False, f"Row count mismatch: team={len(team_df)}, starter={len(starter_df)}"
    
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
    
    # Create DataFrame with alternating columns
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
    
    return True, f"Saved {len(all_rows)} games"


def main():
    """Process all dates."""
    print("="*80)
    print("COMPUTING TEAM BULLPEN BOXSCORES")
    print("="*80)
    
    # Get all team boxscore files
    team_files = sorted(TEAM_BOXSCORES_DIR.glob("team_boxscores_*.csv"))
    
    print(f"\nFound {len(team_files)} team boxscore files")
    print(f"Output directory: {OUTPUT_DIR}")
    print()
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for i, filepath in enumerate(team_files, 1):
        # Extract date from filename
        filename = filepath.stem  # e.g., 'team_boxscores_2025-03-18'
        date_str = filename.replace('team_boxscores_', '')
        
        print(f"[{i}/{len(team_files)}] Processing {date_str}...", end=' ')
        
        success, message = process_date(date_str)
        
        if success:
            if "skipped" in message.lower():
                skip_count += 1
                print(f"⏭  {message}")
            else:
                success_count += 1
                print(f"✓ {message}")
        else:
            error_count += 1
            print(f"❌ {message}")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"  Processed:  {success_count} files")
    print(f"  Skipped:    {skip_count} files (already existed)")
    print(f"  Errors:     {error_count} files")
    print(f"  Total:      {len(team_files)} files")
    print("="*80)
    
    # Show sample output
    output_files = sorted(OUTPUT_DIR.glob("team_bullpen_boxscores_*.csv"))
    if output_files:
        print(f"\n✓ Created {len(output_files)} team bullpen boxscore files")
        print("\nFirst 5 files:")
        for f in output_files[:5]:
            print(f"  - {f.name}")
        if len(output_files) > 5:
            print("\nLast 5 files:")
            for f in output_files[-5:]:
                print(f"  - {f.name}")


if __name__ == "__main__":
    main()
