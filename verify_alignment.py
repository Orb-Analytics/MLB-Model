#!/usr/bin/env python3
"""
Verify that starting pitcher boxscore CSVs align with team boxscore CSVs
"""
import os
import pandas as pd
from pathlib import Path

def verify_year_alignment(year):
    """Verify alignment for a single year"""
    boxscores_dir = Path(f'/workspaces/MLB-Model/data/{year}_data/mlb_data/raw/boxscores')
    pitchers_dir = Path(f'/workspaces/MLB-Model/data/{year}_data/mlb_data/raw/starting_pitcher_boxscores')
    
    if not boxscores_dir.exists() or not pitchers_dir.exists():
        return {
            'year': year,
            'status': 'MISSING_DIRS',
            'boxscore_files': 0,
            'pitcher_files': 0,
            'missing_pitcher_files': [],
            'extra_pitcher_files': [],
            'mismatched_game_pks': []
        }
    
    # Get all files
    boxscore_files = set([f.name.replace('boxscores_', '').replace('.csv', '') 
                          for f in boxscores_dir.glob('boxscores_*.csv')])
    pitcher_files = set([f.name.replace('starting_pitcher_boxscores_', '').replace('.csv', '') 
                         for f in pitchers_dir.glob('starting_pitcher_boxscores_*.csv')])
    
    # Find missing and extra files
    missing_pitcher = sorted(boxscore_files - pitcher_files)
    extra_pitcher = sorted(pitcher_files - boxscore_files)
    
    # Check game_pk alignment for matching files
    mismatched = []
    for date in sorted(boxscore_files & pitcher_files):
        box_file = boxscores_dir / f'boxscores_{date}.csv'
        pit_file = pitchers_dir / f'starting_pitcher_boxscores_{date}.csv'
        
        try:
            box_df = pd.read_csv(box_file)
            pit_df = pd.read_csv(pit_file)
            
            box_pks = set(box_df['game_pk'].unique())
            pit_pks = set(pit_df['game_pk'].unique())
            
            if box_pks != pit_pks:
                mismatched.append({
                    'date': date,
                    'box_only': sorted(box_pks - pit_pks),
                    'pit_only': sorted(pit_pks - box_pks)
                })
        except Exception as e:
            mismatched.append({
                'date': date,
                'error': str(e)
            })
    
    return {
        'year': year,
        'status': 'ALIGNED' if not missing_pitcher and not extra_pitcher and not mismatched else 'MISALIGNED',
        'boxscore_files': len(boxscore_files),
        'pitcher_files': len(pitcher_files),
        'missing_pitcher_files': missing_pitcher,
        'extra_pitcher_files': extra_pitcher,
        'mismatched_game_pks': mismatched
    }

# Verify all years
print("=" * 80)
print("STARTING PITCHER BOXSCORE ALIGNMENT VERIFICATION")
print("=" * 80)
print()

all_results = []
for year in range(2009, 2024):
    result = verify_year_alignment(year)
    all_results.append(result)
    
    status_emoji = "✅" if result['status'] == 'ALIGNED' else "⚠️"
    print(f"{status_emoji} {year}: {result['pitcher_files']}/{result['boxscore_files']} files", end="")
    
    if result['missing_pitcher_files']:
        print(f" | Missing: {len(result['missing_pitcher_files'])}", end="")
    if result['extra_pitcher_files']:
        print(f" | Extra: {len(result['extra_pitcher_files'])}", end="")
    if result['mismatched_game_pks']:
        print(f" | Mismatched: {len(result['mismatched_game_pks'])}", end="")
    print()

print()
print("=" * 80)

# Summary
all_aligned = all([r['status'] == 'ALIGNED' for r in all_results])
if all_aligned:
    print("🎉 ALL YEARS PERFECTLY ALIGNED!")
else:
    print("⚠️  SOME MISALIGNMENTS FOUND")
    print()
    for result in all_results:
        if result['status'] != 'ALIGNED':
            print(f"\n{result['year']}:")
            if result['missing_pitcher_files']:
                print(f"  Missing pitcher files: {result['missing_pitcher_files'][:5]}")
                if len(result['missing_pitcher_files']) > 5:
                    print(f"    ... and {len(result['missing_pitcher_files']) - 5} more")
            if result['extra_pitcher_files']:
                print(f"  Extra pitcher files: {result['extra_pitcher_files'][:5]}")
            if result['mismatched_game_pks']:
                print(f"  Mismatched game_pks: {len(result['mismatched_game_pks'])} dates")
                for m in result['mismatched_game_pks'][:3]:
                    print(f"    {m}")

print("=" * 80)
