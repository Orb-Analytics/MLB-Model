#!/usr/bin/env python3
"""
Verify and fix row order alignment across all years (2011-2024).
Ensures each game outlook file matches the exact row order of its boxscore file.
"""

import pandas as pd
import glob
import os
from pathlib import Path

def align_outlook_to_boxscore(year):
    """Align outlook files to match boxscore row order for a given year."""
    
    print(f"\n{'='*70}")
    print(f"Processing {year}")
    print('='*70)
    
    boxscore_dir = f'data/{year}_data/mlb_data/raw/boxscores'
    outlook_dir = f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook'
    
    if not os.path.exists(boxscore_dir) or not os.path.exists(outlook_dir):
        print(f"  ⚠ Directories not found for {year}, skipping...")
        return 0, 0, 0
    
    boxscore_files = sorted(glob.glob(f'{boxscore_dir}/*.csv'))
    
    fixed_count = 0
    already_aligned_count = 0
    missing_outlook_count = 0
    
    for boxscore_file in boxscore_files:
        date_str = os.path.basename(boxscore_file).replace('boxscores_', '').replace('.csv', '')
        outlook_file = f'{outlook_dir}/game_outlook_{date_str}.csv'
        
        if not os.path.exists(outlook_file):
            missing_outlook_count += 1
            continue
        
        # Load both files
        boxscore_df = pd.read_csv(boxscore_file)
        outlook_df = pd.read_csv(outlook_file)
        
        # Check if game_pks match
        box_pks = boxscore_df['game_pk'].tolist()
        outlook_pks = outlook_df['game_pk'].tolist()
        
        if box_pks == outlook_pks:
            # Already perfectly aligned
            already_aligned_count += 1
        elif set(box_pks) == set(outlook_pks):
            # Same games but different order - fix it
            # Create a mapping of game_pk to row index in boxscore
            pk_order = {pk: idx for idx, pk in enumerate(box_pks)}
            
            # Sort outlook to match boxscore order
            outlook_df['_sort_order'] = outlook_df['game_pk'].map(pk_order)
            outlook_df = outlook_df.sort_values('_sort_order').drop('_sort_order', axis=1)
            outlook_df = outlook_df.reset_index(drop=True)
            
            # Save back
            outlook_df.to_csv(outlook_file, index=False)
            fixed_count += 1
            print(f"  ✓ Fixed alignment: {date_str} ({len(box_pks)} games)")
        else:
            # Different games - this is a problem
            print(f"  ✗ ERROR {date_str}: Different games in boxscore vs outlook")
            print(f"    Boxscore: {len(box_pks)} games, Outlook: {len(outlook_pks)} games")
            missing = set(box_pks) - set(outlook_pks)
            extra = set(outlook_pks) - set(box_pks)
            if missing:
                print(f"    Missing from outlook: {missing}")
            if extra:
                print(f"    Extra in outlook: {extra}")
    
    print(f"\nSummary for {year}:")
    print(f"  Already aligned: {already_aligned_count} files")
    print(f"  Fixed: {fixed_count} files")
    print(f"  Missing outlook files: {missing_outlook_count}")
    
    return already_aligned_count, fixed_count, missing_outlook_count


def verify_alignment(year):
    """Verify perfect row-by-row alignment for a year."""
    
    boxscore_dir = f'data/{year}_data/mlb_data/raw/boxscores'
    pitcher_dir = f'data/{year}_data/mlb_data/raw/starting_pitcher_boxscores'
    outlook_dir = f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook'
    
    if not all([os.path.exists(d) for d in [boxscore_dir, pitcher_dir, outlook_dir]]):
        return 0, 0
    
    boxscore_files = sorted(glob.glob(f'{boxscore_dir}/*.csv'))
    
    aligned = 0
    misaligned = 0
    
    for boxscore_file in boxscore_files:
        date_str = os.path.basename(boxscore_file).replace('boxscores_', '').replace('.csv', '')
        pitcher_file = f'{pitcher_dir}/starting_pitcher_boxscores_{date_str}.csv'
        outlook_file = f'{outlook_dir}/game_outlook_{date_str}.csv'
        
        if not all([os.path.exists(f) for f in [pitcher_file, outlook_file]]):
            continue
        
        b = pd.read_csv(boxscore_file)
        p = pd.read_csv(pitcher_file)
        o = pd.read_csv(outlook_file)
        
        if b['game_pk'].tolist() == p['game_pk'].tolist() == o['game_pk'].tolist():
            aligned += 1
        else:
            misaligned += 1
    
    return aligned, misaligned


def main():
    print("="*70)
    print("VERIFY AND FIX ROW ORDER ALIGNMENT - ALL YEARS (2011-2024)")
    print("="*70)
    
    total_fixed = 0
    total_aligned = 0
    
    # Fix alignment for all years
    for year in range(2011, 2025):
        aligned, fixed, missing = align_outlook_to_boxscore(year)
        total_aligned += aligned
        total_fixed += fixed
    
    # Verify alignment
    print(f"\n{'='*70}")
    print("VERIFICATION - Row-by-row alignment check")
    print('='*70)
    
    all_results = []
    for year in range(2011, 2025):
        aligned, misaligned = verify_alignment(year)
        total_files = aligned + misaligned
        
        if total_files > 0:
            status = '✓' if misaligned == 0 else '✗'
            print(f"{year}: {aligned}/{total_files} files aligned {status}")
            all_results.append((year, aligned, misaligned))
    
    print(f"\n{'='*70}")
    print("FINAL SUMMARY")
    print('='*70)
    print(f"Total files already aligned: {total_aligned}")
    print(f"Total files fixed: {total_fixed}")
    
    all_aligned = all(misaligned == 0 for _, _, misaligned in all_results)
    if all_aligned:
        print("\n✓ SUCCESS: All years have perfect row-by-row alignment!")
    else:
        print("\n⚠ Some files still misaligned")
    
    print('='*70)


if __name__ == '__main__':
    main()
