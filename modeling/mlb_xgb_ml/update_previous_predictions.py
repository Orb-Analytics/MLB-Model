"""
Update the pick_correct? column in previous day's predictions based on actual game results.
"""

import pandas as pd
from datetime import datetime, timedelta
import sys
import os

def update_predictions_with_results(prediction_date):
    """
    Update the pick_correct? column for a given date's predictions.
    
    Args:
        prediction_date: datetime object or string in YYYY-MM-DD format
    """
    if isinstance(prediction_date, str):
        prediction_date = datetime.strptime(prediction_date, '%Y-%m-%d')
    
    date_str = prediction_date.strftime('%Y-%m-%d')
    
    # File paths
    pred_file = f'modeling/mlb_xgb_ml/predictions/predictions_{date_str}.csv'
    box_file = f'data/2026_data/mlb_data/raw/boxscores/boxscores_{date_str}.csv'
    outlook_file = f'data/2026_data/mlb_data/raw/game_outlook/game_outlook_{date_str}.csv'
    
    # Check if files exist
    if not os.path.exists(pred_file):
        print(f"Predictions file not found: {pred_file}")
        return False
    
    if not os.path.exists(box_file):
        print(f"Boxscores file not found: {box_file}")
        return False
    
    # Read files
    print(f"Updating predictions for {date_str}...")
    preds = pd.read_csv(pred_file)
    boxes = pd.read_csv(box_file)
    
    # The game outlook file's status field flags games that may not have finished
    # (postponed/canceled/suspended/scheduled). Status alone can be stale for older
    # dates, so below we only skip grading when the boxscore ALSO shows a 0-0 score,
    # which is impossible for a completed baseball game and reliably confirms the
    # game never actually happened.
    if os.path.exists(outlook_file):
        outlook = pd.read_csv(outlook_file)[['game_pk', 'status', 'date']]
        outlook = outlook.rename(columns={'date': 'game_start_utc'})
        boxes = boxes.merge(outlook, on='game_pk', how='left')
        # Doubleheaders: two real games between the same teams on the same date.
        # Sort by start time so any duplicate matchup consistently resolves to
        # Game 1 (the earlier game) instead of arbitrary CSV row order.
        if 'game_start_utc' in boxes.columns:
            boxes = boxes.sort_values('game_start_utc')
    
    # Update each prediction
    updated_count = 0
    for idx, pred_row in preds.iterrows():
        # Find matching boxscore
        box_match = boxes[
            (boxes['home_team_abbreviation'] == pred_row['home team']) &
            (boxes['away_team_abbreviation'] == pred_row['away team'])
        ]
        
        if len(box_match) > 0:
            box_row = box_match.iloc[0]
            not_final = 'status' in boxes.columns and not pd.isna(box_row.get('status')) \
                and 'FINAL' not in str(box_row['status'])
            no_score = box_row['home_batting_r'] == 0 and box_row['away_batting_r'] == 0

            if not_final and no_score:
                print(f"  Skipping {pred_row['home team']} vs {pred_row['away team']} "
                      f"(status: {box_row['status']}, 0-0 score - game not played)")
                continue

            home_score = box_row['home_batting_r']
            away_score = box_row['away_batting_r']
            
            # Determine actual winner
            if home_score > away_score:
                actual_winner = pred_row['home team']
            else:
                actual_winner = pred_row['away team']
            
            # Check if pick was made
            pick_made = pred_row['pick_made?'] == 1
            
            if pick_made:
                model_pick = pred_row['pick?']
                pick_correct = 1 if (model_pick == actual_winner) else 0
                preds.at[idx, 'pick_correct?'] = pick_correct
                updated_count += 1
            # If no pick was made, leave the value as NaN (don't update it)
    
    # Save updated predictions
    preds.to_csv(pred_file, index=False)
    print(f"Updated {updated_count} picks in {pred_file}")
    return True

def main():
    """Main function to update previous day's predictions."""
    
    # Determine which date to update
    if len(sys.argv) > 1:
        # Use provided date
        target_date = datetime.strptime(sys.argv[1], '%Y-%m-%d')
    else:
        # Default to updating yesterday's predictions
        target_date = datetime.now() - timedelta(days=1)
    
    success = update_predictions_with_results(target_date)
    
    if success:
        print(f"Successfully updated predictions for {target_date.strftime('%Y-%m-%d')}")
    else:
        print(f"Failed to update predictions for {target_date.strftime('%Y-%m-%d')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
