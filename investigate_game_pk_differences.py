import pandas as pd
import glob

def investigate_game_pk_differences(year):
    """Find which game_pks are in one dataset but not the other."""
    
    print(f"\n{'='*80}")
    print(f"Investigating game_pk Differences for {year}")
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
    
    # Get sets of game_pks
    box_pks = set(boxscores['game_pk'].tolist())
    out_pks = set(outlook['game_pk'].astype(int).tolist())
    
    print(f"\nUnique game_pks:")
    print(f"  Boxscores: {len(box_pks):,}")
    print(f"  Outlook:   {len(out_pks):,}")
    
    # Find differences
    only_in_box = sorted(box_pks - out_pks)
    only_in_outlook = sorted(out_pks - box_pks)
    in_both = sorted(box_pks & out_pks)
    
    print(f"\n{'='*80}")
    print("SET COMPARISON:")
    print('='*80)
    print(f"  In both datasets:       {len(in_both):,} game_pks")
    print(f"  Only in boxscores:      {len(only_in_box):,} game_pks")
    print(f"  Only in outlook:        {len(only_in_outlook):,} game_pks")
    
    if only_in_box:
        print(f"\n⚠️  Games in BOXSCORES but NOT in OUTLOOK:")
        for pk in only_in_box[:10]:
            game = boxscores[boxscores['game_pk'] == pk].iloc[0]
            print(f"    {pk}: {game['home_team_abbreviation']} vs {game['away_team_abbreviation']} on {game['date']}")
        if len(only_in_box) > 10:
            print(f"    ... and {len(only_in_box) - 10} more")
    
    if only_in_outlook:
        print(f"\n⚠️  Games in OUTLOOK but NOT in BOXSCORES:")
        for pk in only_in_outlook[:10]:
            game = outlook[outlook['game_pk'] == pk].iloc[0]
            date_str = pd.to_datetime(game['date']).strftime('%Y-%m-%d')
            print(f"    {pk}: {game['home_team_abbreviation']} vs {game['away_team_abbreviation']} on {date_str}")
        if len(only_in_outlook) > 10:
            print(f"    ... and {len(only_in_outlook) - 10} more")
    
    # Check for duplicates
    print(f"\n{'='*80}")
    print("DUPLICATE CHECK:")
    print('='*80)
    
    box_dupes = boxscores['game_pk'].value_counts()
    box_dupes = box_dupes[box_dupes > 1]
    print(f"  Boxscore duplicates: {len(box_dupes)}")
    if len(box_dupes) > 0:
        print(f"    Duplicate game_pks:")
        for pk, count in box_dupes.head(5).items():
            print(f"      {pk}: appears {count} times")
    
    out_dupes = outlook['game_pk'].value_counts()
    out_dupes = out_dupes[out_dupes > 1]
    print(f"  Outlook duplicates:  {len(out_dupes)}")
    if len(out_dupes) > 0:
        print(f"    Duplicate game_pks:")
        for pk, count in out_dupes.head(5).items():
            print(f"      {int(pk)}: appears {count} times")
    
    # Summary
    print(f"\n{'='*80}")
    print("CONCLUSION:")
    print('='*80)
    
    if len(only_in_box) == 0 and len(only_in_outlook) == 0 and len(box_dupes) == 0 and len(out_dupes) == 0:
        print("✅ Perfect match: Same game_pks in both datasets, no duplicates")
        print("   Datasets can be merged on game_pk")
    else:
        print("⚠️  Datasets have differences:")
        if len(only_in_box) > 0:
            print(f"   • {len(only_in_box)} games only in boxscores")
        if len(only_in_outlook) > 0:
            print(f"   • {len(only_in_outlook)} games only in outlook")
        if len(box_dupes) > 0:
            print(f"   • {len(box_dupes)} duplicate game_pks in boxscores")
        if len(out_dupes) > 0:
            print(f"   • {len(out_dupes)} duplicate game_pks in outlook")

if __name__ == "__main__":
    investigate_game_pk_differences(2010)
