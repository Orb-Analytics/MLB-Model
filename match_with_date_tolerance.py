"""
Improved balldontlie ID matching with:
1. ±1 day date tolerance (for UTC timezone differences)
2. Game score validation as failsafe
3. Team abbreviation mapping
"""

import pandas as pd
import glob
from datetime import timedelta

# Team abbreviation mappings (balldontlie → MLB)
# Outlook uses these, box scores use MLB abbreviations
TEAM_ABB_MAPPING = {
    'ARI': 'AZ',   # Arizona Diamondbacks
    'CHW': 'CWS',  # Chicago White Sox
    'OAK': 'ATH'   # Oakland Athletics
}

def map_team_abb(abb):
    """Map MLB abbreviation to balldontlie abbreviation."""
    return TEAM_ABB_MAPPING.get(abb, abb)

print("="*80)
print("IMPROVED BALLDONTLIE ID MATCHING")
print("="*80)
print()

# Load all box scores
boxscores = pd.concat([pd.read_csv(f) for f in glob.glob('data/bdl_data/boxscores/boxscores_2025-*.csv')], 
                      ignore_index=True)
print(f"Loaded {len(boxscores)} box scores")

# Load all outlook data
outlook = pd.concat([pd.read_csv(f) for f in glob.glob('data/bdl_data/game_outlook/game_outlook_2025-*.csv')], 
                    ignore_index=True)
print(f"Loaded {len(outlook)} outlook games")

# Map outlook team abbreviations to match box scores
outlook['home_team_abb_mlb'] = outlook['home_team_abbreviation'].apply(map_team_abb)
outlook['away_team_abb_mlb'] = outlook['away_team_abbreviation'].apply(map_team_abb)

# Convert date columns to datetime for comparison
boxscores['date_dt'] = pd.to_datetime(boxscores['date'])
outlook['date_dt'] = pd.to_datetime(outlook['date']).dt.date

print()
print("="*80)
print("MATCHING WITH ±1 DAY TOLERANCE AND SCORE VALIDATION")
print("="*80)
print()

# Dictionary to store matches
matches = {}
match_details = []

for idx, box_game in boxscores.iterrows():
    box_date = box_game['date_dt'].date()
    home_abb = box_game['home_team_abbreviation']
    away_abb = box_game['away_team_abbreviation']
    
    # Get scores from box scores
    # Box scores have runs in columns like 'home_batting_r' and 'away_batting_r'
    home_score = box_game.get('home_batting_r', None)
    away_score = box_game.get('away_batting_r', None)
    
    # Look for matches within ±1 day
    date_range = [box_date - timedelta(days=1), box_date, box_date + timedelta(days=1)]
    
    candidates = outlook[
        (outlook['date_dt'].isin(date_range)) &
        (outlook['home_team_abb_mlb'] == home_abb) &
        (outlook['away_team_abb_mlb'] == away_abb)
    ]
    
    if len(candidates) == 0:
        # No match found
        match_details.append({
            'box_game_pk': box_game['id'],
            'matchup': f"{away_abb} @ {home_abb}",
            'box_date': box_date,
            'status': 'NO_MATCH',
            'balldontlie_id': None
        })
        continue
    
    # Strategy: ALWAYS prioritize score matching over date matching
    # 1. Score match (anywhere in ±1 day range) 
    # 2. Exact date (if no score match possible)
    # 3. Closest date (fallback)
    
    # First, try to find score match anywhere in the ±1 day range
    if pd.notna(home_score) and pd.notna(away_score):
        score_matches = candidates[
            (candidates['home_team_score'] == home_score) &
            (candidates['away_team_score'] == away_score)
        ]
        
        if len(score_matches) > 0:
            # Found score match! Use it regardless of date
            if len(score_matches) == 1:
                matched_game = score_matches.iloc[0]
            else:
                # Multiple score matches - take closest date
                score_matches = score_matches.copy()
                score_matches['date_diff'] = abs((score_matches['date_dt'] - box_date).apply(lambda x: x.days))
                matched_game = score_matches.sort_values('date_diff').iloc[0]
            
            date_diff = (matched_game['date_dt'] - box_date).days
            status = 'SCORE_MATCH' if date_diff == 0 else f'SCORE_MATCH_DATE{date_diff:+d}'
            
            matches[box_game['id']] = matched_game['id']
            match_details.append({
                'box_game_pk': box_game['id'],
                'matchup': f"{away_abb} @ {home_abb}",
                'box_date': box_date,
                'outlook_date': matched_game['date_dt'],
                'status': status,
                'balldontlie_id': matched_game['id'],
                'date_diff': date_diff
            })
            continue
    
    # No score match found or no score available - use date-based matching
    exact_date_candidates = candidates[candidates['date_dt'] == box_date]
    
    if len(exact_date_candidates) > 0:
        # We have exact date match(es)
        if len(exact_date_candidates) == 1:
            # Single exact date match - use it regardless of score
            matched_game = exact_date_candidates.iloc[0]
            
            # Check if score also matches
            if (pd.notna(home_score) and pd.notna(away_score) and
                matched_game['home_team_score'] == home_score and 
                matched_game['away_team_score'] == away_score):
                status = 'EXACT_DATE_SCORE'
            else:
                status = 'EXACT_DATE_ONLY'
            
            matches[box_game['id']] = matched_game['id']
            match_details.append({
                'box_game_pk': box_game['id'],
                'matchup': f"{away_abb} @ {home_abb}",
                'box_date': box_date,
                'outlook_date': matched_game['date_dt'],
                'status': status,
                'balldontlie_id': matched_game['id'],
                'date_diff': 0
            })
            continue
        else:
            # Multiple exact date matches - try to use score to pick the right one
            if pd.notna(home_score) and pd.notna(away_score):
                score_matches = exact_date_candidates[
                    (exact_date_candidates['home_team_score'] == home_score) &
                    (exact_date_candidates['away_team_score'] == away_score)
                ]
                
                if len(score_matches) > 0:
                    # Found score match on exact date
                    matched_game = score_matches.iloc[0]
                    matches[box_game['id']] = matched_game['id']
                    match_details.append({
                        'box_game_pk': box_game['id'],
                        'matchup': f"{away_abb} @ {home_abb}",
                        'box_date': box_date,
                        'outlook_date': matched_game['date_dt'],
                        'status': 'EXACT_DATE_SCORE_MULTI',
                        'balldontlie_id': matched_game['id'],
                        'date_diff': 0
                    })
                    continue
            
            # No score match or no score available - just take first exact date match
            matched_game = exact_date_candidates.iloc[0]
            matches[box_game['id']] = matched_game['id']
            match_details.append({
                'box_game_pk': box_game['id'],
                'matchup': f"{away_abb} @ {home_abb}",
                'box_date': box_date,
                'outlook_date': matched_game['date_dt'],
                'status': 'EXACT_DATE_MULTI_FIRST',
                'balldontlie_id': matched_game['id'],
                'date_diff': 0
            })
            continue
    
    # No exact date match - we have ±1 day matches
    if pd.notna(home_score) and pd.notna(away_score):
        # Try to match by score
        score_matches = candidates[
            (candidates['home_team_score'] == home_score) &
            (candidates['away_team_score'] == away_score)
        ]
        
        if len(score_matches) > 0:
            # Found score match in ±1 day range
            # Take the closest one
            score_matches = score_matches.copy()
            score_matches['date_diff'] = abs((score_matches['date_dt'] - box_date).apply(lambda x: x.days))
            matched_game = score_matches.sort_values('date_diff').iloc[0]
            
            matches[box_game['id']] = matched_game['id']
            match_details.append({
                'box_game_pk': box_game['id'],
                'matchup': f"{away_abb} @ {home_abb}",
                'box_date': box_date,
                'outlook_date': matched_game['date_dt'],
                'status': 'NEARBY_DATE_SCORE',
                'balldontlie_id': matched_game['id'],
                'date_diff': int(matched_game['date_diff'])
            })
            continue
    
    # No score match - just take closest date
    candidates = candidates.copy()
    candidates['date_diff'] = abs((candidates['date_dt'] - box_date).apply(lambda x: x.days))
    matched_game = candidates.sort_values('date_diff').iloc[0]
    
    matches[box_game['id']] = matched_game['id']
    match_details.append({
        'box_game_pk': box_game['id'],
        'matchup': f"{away_abb} @ {home_abb}",
        'box_date': box_date,
        'outlook_date': matched_game['date_dt'],
        'status': 'NEARBY_DATE_ONLY',
        'balldontlie_id': matched_game['id'],
        'date_diff': int(matched_game['date_diff'])
    })

# Add balldontlie_game_id to box scores
boxscores['balldontlie_game_id'] = boxscores['id'].map(matches)

# Move balldontlie_game_id to first column
cols = ['balldontlie_game_id'] + [col for col in boxscores.columns if col != 'balldontlie_game_id']
boxscores = boxscores[cols]

print()
print("="*80)
print("MATCHING RESULTS")
print("="*80)
print()

# Create details dataframe
details_df = pd.DataFrame(match_details)

print(f"Total games: {len(boxscores)}")
print(f"Matched: {boxscores['balldontlie_game_id'].notna().sum()} ({boxscores['balldontlie_game_id'].notna().sum()/len(boxscores)*100:.1f}%)")
print(f"Unmatched: {boxscores['balldontlie_game_id'].isna().sum()} ({boxscores['balldontlie_game_id'].isna().sum()/len(boxscores)*100:.1f}%)")
print()

if len(details_df) > 0:
    print("Matching breakdown by status:")
    status_counts = details_df['status'].value_counts()
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    print()
    
    # Check date differences
    matched_details = details_df[details_df['balldontlie_id'].notna()]
    if len(matched_details) > 0 and 'date_diff' in matched_details.columns:
        print("Date difference distribution:")
        date_diff_counts = matched_details['date_diff'].value_counts()
        for diff, count in sorted(date_diff_counts.items()):
            print(f"  {int(diff):+d} days: {count}")
        print()

# Show some examples of different match types
print("="*80)
print("SAMPLE MATCHES")
print("="*80)
print()

if len(details_df) > 0:
    # Score validated matches
    score_validated = details_df[details_df['status'].str.contains('SCORE', na=False)]
    if len(score_validated) > 0:
        print(f"Score-validated matches (showing first 5 of {len(score_validated)}):")
        for _, row in score_validated.head(5).iterrows():
            date_diff_str = f"({row.get('date_diff', 0):+d} day)" if 'date_diff' in row and row['date_diff'] != 0 else ""
            print(f"  {row['box_date']} | {row['matchup']:20} | BDL ID: {row['balldontlie_id']} {date_diff_str}")
        print()
    
    # Exact date matches
    exact_date = details_df[details_df['status'].str.contains('EXACT_DATE', na=False)]
    if len(exact_date) > 0:
        print(f"Exact date matches (showing first 5 of {len(exact_date)}):")
        for _, row in exact_date.head(5).iterrows():
            print(f"  {row['box_date']} | {row['matchup']:20} | BDL ID: {row['balldontlie_id']}")
        print()
    
    # Unmatched games
    unmatched = details_df[details_df['status'] == 'NO_MATCH']
    if len(unmatched) > 0:
        print(f"Remaining unmatched (showing first 10 of {len(unmatched)}):")
        for _, row in unmatched.head(10).iterrows():
            print(f"  {row['box_date']} | {row['matchup']:20} | PK: {row['box_game_pk']}")
        print()

print()
print("="*80)
print("SAVING UPDATED FILES")
print("="*80)
print()

# Group by date and save
saved_files = 0
for date_str, group in boxscores.groupby('date'):
    file_path = f'data/bdl_data/boxscores/boxscores_{date_str}.csv'
    group.to_csv(file_path, index=False)
    saved_files += 1

print(f"✅ Saved {saved_files} files")
print()
print("COMPLETE!")
print(f"Match rate improved from 87.5% to {boxscores['balldontlie_game_id'].notna().sum()/len(boxscores)*100:.1f}%")
