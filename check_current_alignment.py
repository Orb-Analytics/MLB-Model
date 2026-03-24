import pandas as pd
import glob

# Load boxscore and outlook files
boxscore_files = sorted(glob.glob('data/2009_data/mlb_data/raw/boxscores/boxscores_*.csv'))
outlook_base = 'data/2009_data/mlb_data/raw/bdl_data/game_outlook/'

print("Checking detailed alignment...\n")

mismatches = []
total_games = 0
matched_games = 0

for box_file in boxscore_files:
    date = box_file.split('_')[-1].replace('.csv', '')
    outlook_file = f'{outlook_base}game_outlook_{date}.csv'
    
    box_df = pd.read_csv(box_file)
    
    try:
        out_df = pd.read_csv(outlook_file)
    except FileNotFoundError:
        print(f"❌ {date}: No outlook file (boxscore has {len(box_df)} games)")
        for i, row in box_df.iterrows():
            mismatches.append({
                'date': date,
                'position': i,
                'box_pk': int(row['game_pk']),
                'out_pk': None,
                'issue': 'missing_outlook_file'
            })
        continue
    
    if len(box_df) != len(out_df):
        print(f"❌ {date}: Count mismatch - boxscore: {len(box_df)}, outlook: {len(out_df)}")
    
    for i in range(max(len(box_df), len(out_df))):
        total_games += 1
        
        if i >= len(box_df):
            mismatches.append({
                'date': date,
                'position': i,
                'box_pk': None,
                'out_pk': int(out_df.iloc[i]['game_pk']) if pd.notna(out_df.iloc[i].get('game_pk')) else None,
                'issue': 'extra_in_outlook'
            })
        elif i >= len(out_df):
            mismatches.append({
                'date': date,
                'position': i,
                'box_pk': int(box_df.iloc[i]['game_pk']),
                'out_pk': None,
                'issue': 'missing_in_outlook'
            })
        else:
            box_pk = int(box_df.iloc[i]['game_pk'])
            out_pk = out_df.iloc[i].get('game_pk')
            
            if pd.notna(out_pk):
                out_pk = int(out_pk)
                if box_pk == out_pk:
                    matched_games += 1
                else:
                    mismatches.append({
                        'date': date,
                        'position': i,
                        'box_pk': box_pk,
                        'out_pk': out_pk,
                        'issue': 'different_game_pk'
                    })
            else:
                mismatches.append({
                    'date': date,
                    'position': i,
                    'box_pk': box_pk,
                    'out_pk': None,
                    'issue': 'no_game_pk'
                })

print(f"\n{'='*80}")
print(f"Total games checked: {total_games}")
print(f"Matched: {matched_games} ({100*matched_games/total_games:.1f}%)")
print(f"Mismatches: {len(mismatches)}")
print(f"{'='*80}\n")

if len(mismatches) > 0:
    print(f"First 20 mismatches:")
    for m in mismatches[:20]:
        print(f"  {m['date']} pos {m['position']}: box={m['box_pk']}, out={m['out_pk']} [{m['issue']}]")
    
    if len(mismatches) > 20:
        print(f"  ... and {len(mismatches) - 20} more")
        
    # Check if games are on different dates
    print(f"\n{'='*80}")
    print("Checking if mismatched games exist on other dates...\n")
    
    # Build outlook game_pk to date mapping
    all_outlook_pks = {}
    for file in glob.glob(f'{outlook_base}game_outlook_*.csv'):
        date = file.split('_')[-1].replace('.csv', '')
        df = pd.read_csv(file)
        for _, row in df.iterrows():
            if pd.notna(row.get('game_pk')):
                all_outlook_pks[int(row['game_pk'])] = date
    
    # Check mismatches
    wrong_date_count = 0
    truly_missing_count = 0
    
    for m in mismatches:
        if m['box_pk'] is not None and m['issue'] in ['different_game_pk', 'missing_in_outlook', 'no_game_pk']:
            if m['box_pk'] in all_outlook_pks:
                actual_date = all_outlook_pks[m['box_pk']]
                if actual_date != m['date']:
                    print(f"  Game {m['box_pk']}: should be {m['date']}, found at {actual_date}")
                    wrong_date_count += 1
            else:
                print(f"  Game {m['box_pk']}: truly missing from all outlook files")
                truly_missing_count += 1
    
    print(f"\n{wrong_date_count} games on wrong dates")
    print(f"{truly_missing_count} games truly missing")
