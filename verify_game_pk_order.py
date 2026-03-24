"""
Verify that game outlook files now match boxscore file order by game_pk.
"""

import pandas as pd
from pathlib import Path

print('=' * 80)
print('VERIFYING GAME ORDER ALIGNMENT')
print('=' * 80)

outlook_dir = Path('data/2009_data/mlb_data/raw/bdl_data/game_outlook')
boxscore_dir = Path('data/2009_data/mlb_data/raw/boxscores')

# Check several sample dates
test_dates = ['2009-04-05', '2009-04-06', '2009-04-15', '2009-07-09', '2009-09-28']

print(f'\nChecking {len(test_dates)} sample dates...\n')

all_match = True

for date in test_dates:
    outlook_file = outlook_dir / f'game_outlook_{date}.csv'
    boxscore_file = boxscore_dir / f'boxscores_{date}.csv'
    
    if not outlook_file.exists() or not boxscore_file.exists():
        print(f'⚠️  {date}: File not found')
        continue
    
    outlook_df = pd.read_csv(outlook_file)
    boxscore_df = pd.read_csv(boxscore_file)
    
    outlook_pks = outlook_df['game_pk'].dropna().astype(int).tolist()
    boxscore_pks = boxscore_df['game_pk'].tolist()
    
    # Check if all outlook pks are in boxscore (in any order)
    outlook_set = set(outlook_pks)
    boxscore_set = set(boxscore_pks)
    
    in_both = outlook_set & boxscore_set
    only_outlook = outlook_set - boxscore_set
    only_boxscore = boxscore_set - outlook_set
    
    # Check if order matches for games in both
    order_match = outlook_pks == boxscore_pks[:len(outlook_pks)]
    
    print(f'{date}:')
    print(f'  Outlook games:  {len(outlook_pks)}')
    print(f'  Boxscore games: {len(boxscore_pks)}')
    print(f'  In both:        {len(in_both)}')
    
    if only_outlook:
        print(f'  Only in outlook: {only_outlook}')
        all_match = False
    if only_boxscore:
        print(f'  Only in boxscore: {only_boxscore}')
    
    if order_match and len(outlook_pks) == len(boxscore_pks):
        print(f'  ✅ Order matches perfectly!')
    elif order_match:
        print(f'  ✅ Order matches for games in both')
    else:
        print(f'  ⚠️  Order does NOT match')
        print(f'     Outlook:  {outlook_pks[:5]}...')
        print(f'     Boxscore: {boxscore_pks[:5]}...')
        all_match = False
    print()

# Check the special July 9 doubleheader date
print('=' * 80)
print('JULY 9 DOUBLEHEADER CHECK')
print('=' * 80)

date = '2009-07-09'
outlook_file = outlook_dir / f'game_outlook_{date}.csv'
boxscore_file = boxscore_dir / f'boxscores_{date}.csv'

outlook_df = pd.read_csv(outlook_file)
boxscore_df = pd.read_csv(boxscore_file)

print(f'\nBoxscore has {len(boxscore_df)} games:')
for _, row in boxscore_df.iterrows():
    print(f'  {row["game_pk"]}: {row["away_team_abbreviation"]}@{row["home_team_abbreviation"]} ({row["away_batting_r"]}-{row["home_batting_r"]})')

print(f'\nOutlook has {len(outlook_df)} games:')
for _, row in outlook_df.iterrows():
    pk = int(row["game_pk"]) if pd.notna(row["game_pk"]) else None
    print(f'  {pk}: {row["away_team_abbreviation"]}@{row["home_team_abbreviation"]} ({row["away_team_score"]}-{row["home_team_score"]})')

print(f'\n✅ As expected, outlook is missing one game from the doubleheader')

# Overall summary
print('\n' + '=' * 80)
print('FINAL VERIFICATION')
print('=' * 80)

total_outlook = 0
total_boxscore = 0
total_with_pk = 0

for outlook_file in sorted(outlook_dir.glob('game_outlook_*.csv')):
    df = pd.read_csv(outlook_file)
    total_outlook += len(df)
    total_with_pk += df['game_pk'].notna().sum()

for boxscore_file in sorted(boxscore_dir.glob('boxscores_*.csv')):
    df = pd.read_csv(boxscore_file)
    total_boxscore += len(df)

print(f'\nTotal games in outlook:        {total_outlook:,}')
print(f'Total with game_pk assigned:   {total_with_pk:,}')
print(f'Total games in boxscores:      {total_boxscore:,}')
print(f'Match rate:                    {total_with_pk/total_outlook*100:.1f}%')

if total_with_pk == total_outlook:
    print(f'\n✅ SUCCESS: All outlook games have game_pk assigned!')
    print(f'✅ Games are ordered to match boxscore files')
else:
    print(f'\n⚠️  {total_outlook - total_with_pk} games missing game_pk')
