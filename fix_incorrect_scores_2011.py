#!/usr/bin/env python3
"""
Fix the 8 games in 2011 BDL outlook that have incorrect scores.
"""

import pandas as pd
import shutil
from datetime import datetime

# Mapping of BDL ID to correct MLB scores
CORRECTIONS = {
    52353: {'game_pk': 289037, 'date': '2011-09-08', 'away_score': 0, 'home_score': 0},   # LAD @ WSH
    57233: {'game_pk': 289321, 'date': '2011-09-28', 'away_score': 8, 'home_score': 0},   # STL @ HOU
    57235: {'game_pk': 289320, 'date': '2011-09-28', 'away_score': 3, 'home_score': 7},   # PIT @ MIL
    57236: {'game_pk': 289315, 'date': '2011-09-28', 'away_score': 0, 'home_score': 1},   # KC @ MIN
    57237: {'game_pk': 289316, 'date': '2011-09-28', 'away_score': 7, 'home_score': 5},   # LAD @ ARI
    57238: {'game_pk': 289322, 'date': '2011-09-28', 'away_score': 3, 'home_score': 1},   # TEX @ LAA
    57239: {'game_pk': 289311, 'date': '2011-09-28', 'away_score': 2, 'home_score': 9},   # CHC @ SD
    57240: {'game_pk': 289318, 'date': '2011-09-28', 'away_score': 2, 'home_score': 0},   # OAK @ SEA
}

outlook_dir = 'data/2011_data/mlb_data/raw/bdl_data/game_outlook'

# Create backup
backup_dir = f'{outlook_dir}/backup_before_score_correction_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
print(f"📁 Creating backup: {backup_dir}")

# Process each unique date
dates = set(c['date'] for c in CORRECTIONS.values())

print("\n" + "=" * 80)
print("Correcting Scores for 8 Games in 2011 BDL Outlook")
print("=" * 80)

for date in sorted(dates):
    outlook_file = f'{outlook_dir}/game_outlook_{date}.csv'
    
    # Backup
    import os
    os.makedirs(backup_dir, exist_ok=True)
    backup_file = f'{backup_dir}/game_outlook_{date}.csv'
    shutil.copy2(outlook_file, backup_file)
    
    # Load file
    df = pd.read_csv(outlook_file)
    
    print(f"\n📅 {date}")
    
    # Find games to correct in this file
    games_to_fix = {bdl_id: correction for bdl_id, correction in CORRECTIONS.items() 
                    if correction['date'] == date}
    
    for bdl_id, correction in games_to_fix.items():
        if bdl_id in df['id'].values:
            idx = df[df['id'] == bdl_id].index[0]
            old_away = df.loc[idx, 'away_team_score']
            old_home = df.loc[idx, 'home_team_score']
            
            df.loc[idx, 'away_team_score'] = correction['away_score']
            df.loc[idx, 'home_team_score'] = correction['home_score']
            
            teams_str = f"{df.loc[idx, 'away_team_abbreviation']} @ {df.loc[idx, 'home_team_abbreviation']}"
            print(f"   ✅ ID {bdl_id} ({teams_str})")
            print(f"      OLD: {int(old_away)}-{int(old_home)}")
            print(f"      NEW: {correction['away_score']}-{correction['home_score']}")
            print(f"      MLB game_pk: {correction['game_pk']}")
    
    # Save updated file
    df.to_csv(outlook_file, index=False)
    print(f"   💾 Saved {outlook_file}")

print("\n" + "=" * 80)
print("✅ All scores corrected!")
print(f"📁 Backup saved to: {backup_dir}")
print("=" * 80)

# Verify the corrections
print("\nVerifying corrections...")
for date in sorted(dates):
    outlook_file = f'{outlook_dir}/game_outlook_{date}.csv'
    df = pd.read_csv(outlook_file)
    
    games_to_check = {bdl_id: correction for bdl_id, correction in CORRECTIONS.items() 
                      if correction['date'] == date}
    
    for bdl_id, correction in games_to_check.items():
        if bdl_id in df['id'].values:
            row = df[df['id'] == bdl_id].iloc[0]
            expected = f"{correction['away_score']}-{correction['home_score']}"
            actual = f"{int(row['away_team_score'])}-{int(row['home_team_score'])}"
            status = "✅" if expected == actual else "❌"
            print(f"{status} ID {bdl_id}: Expected {expected}, Got {actual}")

print("\n🎉 Score corrections complete!")
