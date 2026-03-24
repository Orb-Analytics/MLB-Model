import pandas as pd
import glob

def compare_sorted_game_pks(year):
    """Compare game_pks from boxscores and outlook when both are sorted."""
    
    print(f"\n{'='*80}")
    print(f"Comparing Sorted game_pk Lists for {year}")
    print('='*80)
    
    # Load all boxscores
    boxscore_files = sorted(glob.glob(f'data/{year}_data/mlb_data/raw/boxscores/*.csv'))
    boxscore_dfs = [pd.read_csv(f) for f in boxscore_files]
    boxscores = pd.concat(boxscore_dfs, ignore_index=True)
    
    # Load all game outlook
    outlook_files = sorted(glob.glob(f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook/*.csv'))
    outlook_dfs = [pd.read_csv(f) for f in outlook_files]
    outlook = pd.concat(outlook_dfs, ignore_index=True)
    
    print(f"\nDatasets loaded:")
    print(f"  Boxscores: {len(boxscores):,} games")
    print(f"  Outlook:   {len(outlook):,} games")
    
    # Sort both by game_pk
    boxscores_sorted = boxscores.sort_values('game_pk')
    outlook_sorted = outlook.sort_values('game_pk')
    
    # Get game_pk lists
    box_pks = boxscores_sorted['game_pk'].tolist()
    out_pks = outlook_sorted['game_pk'].astype(int).tolist()
    
    # Display side-by-side comparison
    print(f"\n{'='*80}")
    print("Side-by-Side Comparison (First 20 games sorted by game_pk):")
    print('='*80)
    print(f"{'#':<6} | {'Boxscore game_pk':>15} | {'Outlook game_pk':>15} | {'Match':^7}")
    print("-" * 70)
    
    for i in range(min(20, len(box_pks))):
        match = "✅ Yes" if box_pks[i] == out_pks[i] else "❌ No"
        print(f"{i+1:<6} | {box_pks[i]:>15,} | {out_pks[i]:>15,} | {match:^7}")
    
    print(f"\n{'='*80}")
    print("Side-by-Side Comparison (Last 20 games sorted by game_pk):")
    print('='*80)
    print(f"{'#':<6} | {'Boxscore game_pk':>15} | {'Outlook game_pk':>15} | {'Match':^7}")
    print("-" * 70)
    
    for i in range(max(0, len(box_pks)-20), len(box_pks)):
        match = "✅ Yes" if box_pks[i] == out_pks[i] else "❌ No"
        print(f"{i+1:<6} | {box_pks[i]:>15,} | {out_pks[i]:>15,} | {match:^7}")
    
    # Check if perfectly aligned
    print(f"\n{'='*80}")
    print("ALIGNMENT VERIFICATION:")
    print('='*80)
    
    if box_pks == out_pks:
        print(f"✅ PERFECT ALIGNMENT!")
        print(f"\nAll {len(box_pks):,} game_pks match in exact order:")
        print(f"  • Same game_pk values ✓")
        print(f"  • Same order when sorted ✓")
        print(f"  • Can merge on game_pk or by position ✓")
        
        # Additional checks
        print(f"\nData Quality Checks:")
        print(f"  • Boxscore unique game_pks: {len(set(box_pks)):,} (no duplicates: {'✓' if len(set(box_pks)) == len(box_pks) else '✗'})")
        print(f"  • Outlook unique game_pks:  {len(set(out_pks)):,} (no duplicates: {'✓' if len(set(out_pks)) == len(out_pks) else '✗'})")
        print(f"  • Min game_pk: {min(box_pks):,}")
        print(f"  • Max game_pk: {max(box_pks):,}")
        
        return True
    else:
        print(f"❌ MISALIGNMENT DETECTED")
        
        # Find mismatches
        mismatches = []
        for i, (b, o) in enumerate(zip(box_pks, out_pks)):
            if b != o:
                mismatches.append((i, b, o))
        
        print(f"\nFound {len(mismatches)} mismatches")
        print(f"\nFirst 5 mismatches:")
        for i, b, o in mismatches[:5]:
            print(f"  Position {i+1}: Boxscore={b:,} | Outlook={o:,}")
        
        return False

if __name__ == "__main__":
    result = compare_sorted_game_pks(2010)
    
    print(f"\n{'='*80}")
    if result:
        print("CONCLUSION: ✅ game_pks align perfectly in sorted order!")
    else:
        print("CONCLUSION: ❌ Alignment issues detected")
    print('='*80)
