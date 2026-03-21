"""
Add home_score and away_score columns to the 2025 dataset
Inserts them after column 11 (away_team_name)
"""
import pandas as pd
from pathlib import Path
import glob

# Load current dataset
dataset_path = Path("/workspaces/MLB-Model/data/2025_dataset/2025_dataset.csv")
df = pd.read_csv(dataset_path)

print(f"Loaded dataset: {df.shape[0]} rows × {df.shape[1]} columns")
print(f"\nFirst 12 columns: {list(df.columns[:12])}")

# Load all game scores files
scores_dir = Path("/workspaces/MLB-Model/data/game-scores")
scores_files = sorted(glob.glob(str(scores_dir / "game_scores_*.csv")))

print(f"\nFound {len(scores_files)} score files")

# Concatenate all scores
all_scores = []
for file in scores_files:
    try:
        scores_df = pd.read_csv(file)
        all_scores.append(scores_df)
    except Exception as e:
        print(f"Warning: Could not read {file}: {e}")

if all_scores:
    scores = pd.concat(all_scores, ignore_index=True)
    print(f"Loaded {len(scores)} total game scores")
    
    # Rename columns for clarity
    scores = scores.rename(columns={
        'Date': 'date',
        'Home Team': 'home_team_full',
        'Away Team': 'away_team_full',
        'Home Score': 'home_score',
        'Away Score': 'away_score'
    })
    
    # Keep only completed games with scores
    scores = scores[scores['home_score'].notna() & scores['away_score'].notna()].copy()
    print(f"Games with scores: {len(scores)}")
    
    # Create merge keys (date + display names which match the full team names)
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    scores['date'] = pd.to_datetime(scores['date']).dt.strftime('%Y-%m-%d')
    
    # Check for duplicates in scores
    score_dupes = scores.duplicated(subset=['date', 'home_team_full', 'away_team_full'], keep=False)
    if score_dupes.any():
        print(f"\nWarning: {score_dupes.sum()} duplicate scores found!")
        print(scores[score_dupes][['date', 'home_team_full', 'away_team_full', 'home_score', 'away_score']].head(10))
        # Keep only first occurrence
        scores = scores.drop_duplicates(subset=['date', 'home_team_full', 'away_team_full'], keep='first')
        print(f"After dedup: {len(scores)} unique game scores")
    
    # Check for duplicates in dataset
    df_dupes = df.duplicated(subset=['date', 'home_team_display_name', 'away_team_display_name'], keep=False)
    if df_dupes.any():
        print(f"\nWarning: {df_dupes.sum()} duplicate games in dataset!")
        print(df[df_dupes][['date', 'home_team_display_name', 'away_team_display_name']].head(10))
    
    # Merge on date and team display names
    df_merged = df.merge(
        scores[['date', 'home_team_full', 'away_team_full', 'home_score', 'away_score']],
        left_on=['date', 'home_team_display_name', 'away_team_display_name'],
        right_on=['date', 'home_team_full', 'away_team_full'],
        how='left',
        validate='1:1'  # Ensure no duplicates are created
    )
    
    # Drop the temporary merge columns
    df_merged = df_merged.drop(columns=['home_team_full', 'away_team_full'])
    
    # Check merge success
    matched = df_merged['home_score'].notna().sum()
    print(f"\nMatched {matched} out of {len(df)} games ({matched/len(df)*100:.1f}%)")
    
    # Reorder columns to insert scores after column 11 (away_team_name)
    cols = list(df_merged.columns)
    
    # Find index of away_team_name (column 11, 0-indexed = 10)
    away_team_name_idx = cols.index('away_team_name')
    
    # Split columns and insert scores
    cols_before = cols[:away_team_name_idx+1]  # Include away_team_name
    cols_after = [c for c in cols[away_team_name_idx+1:] if c not in ['home_score', 'away_score']]
    
    new_column_order = cols_before + ['home_score', 'away_score'] + cols_after
    
    df_final = df_merged[new_column_order]
    
    print(f"\nFinal dataset: {df_final.shape[0]} rows × {df_final.shape[1]} columns")
    print(f"Columns 10-14: {list(df_final.columns[10:14])}")
    
    # Save
    df_final.to_csv(dataset_path, index=False)
    print(f"\n✓ Saved updated dataset to {dataset_path}")
    
    # Show sample scores
    print("\nSample scores (first 5 games):")
    print(df_final[['date', 'home_team_name', 'away_team_name', 'home_score', 'away_score']].head())
    
else:
    print("ERROR: No score files found!")
