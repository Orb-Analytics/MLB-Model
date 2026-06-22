#!/usr/bin/env python3
"""
Apply 1.5% Dog / 0.5% Fav (REGRESSED) strategy to XGB predictions
and save picks to CSV for email system.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import sys

def apply_strategy_and_save_picks(date_str=None):
    """
    Apply asymmetric edge thresholds to regressed probabilities and save picks.
    
    Strategy: 
    - Favorites need 0.5% edge
    - Underdogs need 1.5% edge
    - REGRESSED probability = 0.65 * market_prob + 0.35 * xgboost_prob
    """
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Load predictions
    pred_file = Path(__file__).parent / 'predictions' / f'predictions_{date_str}.csv'
    if not pred_file.exists():
        print(f"❌ No predictions file found for {date_str}")
        return
    
    df = pd.read_csv(pred_file)
    print(f"📊 Loaded {len(df)} games for {date_str}")
    
    # Calculate regressed probabilities
    df['home_prob_regressed'] = 0.65 * df['home_prob_market'] + 0.35 * df['home_prob_xgboost']
    df['away_prob_regressed'] = 0.65 * df['away_prob_market'] + 0.35 * df['away_prob_xgboost']
    
    # Calculate edges (percentage points)
    df['home_edge'] = (df['home_prob_regressed'] - df['home_prob_market']) * 100
    df['away_edge'] = (df['away_prob_regressed'] - df['away_prob_market']) * 100
    
    # Determine favorites and underdogs
    df['home_is_favorite'] = df['home_odds'] < 0
    df['away_is_favorite'] = df['away_odds'] < 0
    
    picks = []
    
    for idx, row in df.iterrows():
        # Check home team
        home_threshold = 0.5 if row['home_is_favorite'] else 1.5
        if row['home_edge'] >= home_threshold:
            picks.append({
                'pick_team': row['home_team'],
                'opponent': row['away_team'],
                'is_home': True,
                'is_favorite': row['home_is_favorite'],
                'pick_odds': row['home_odds'],
                'edge': row['home_edge'],
                'cover_prob': row['home_prob_regressed'],
                'home_team': row['home_team'],
                'away_team': row['away_team'],
                'home_odds': row['home_odds'],
                'away_odds': row['away_odds'],
                'date': date_str
            })
        
        # Check away team
        away_threshold = 0.5 if row['away_is_favorite'] else 1.5
        if row['away_edge'] >= away_threshold:
            picks.append({
                'pick_team': row['away_team'],
                'opponent': row['home_team'],
                'is_home': False,
                'is_favorite': row['away_is_favorite'],
                'pick_odds': row['away_odds'],
                'edge': row['away_edge'],
                'cover_prob': row['away_prob_regressed'],
                'home_team': row['home_team'],
                'away_team': row['away_team'],
                'home_odds': row['home_odds'],
                'away_odds': row['away_odds'],
                'date': date_str
            })
    
    if not picks:
        print(f"⚠️  No picks meet thresholds for {date_str}")
        # Create empty CSV
        picks_df = pd.DataFrame(columns=[
            'pick_team', 'opponent', 'is_home', 'is_favorite', 'pick_odds',
            'edge', 'cover_prob', 'home_team', 'away_team', 'home_odds', 'away_odds', 'date'
        ])
    else:
        picks_df = pd.DataFrame(picks)
        print(f"✅ Generated {len(picks_df)} picks:")
        for _, pick in picks_df.iterrows():
            role = "FAV" if pick['is_favorite'] else "DOG"
            print(f"   {pick['pick_team']} ({role}) - Edge: {pick['edge']:.2f}% - Odds: {pick['pick_odds']:+.0f}")
    
    # Save picks to data directory for email system
    output_file = Path(__file__).parent.parent.parent / 'data' / 'mlb_todays_picks.csv'
    picks_df.to_csv(output_file, index=False)
    print(f"💾 Saved picks to {output_file}")
    
    return picks_df

if __name__ == '__main__':
    date_str = sys.argv[1] if len(sys.argv) > 1 else None
    apply_strategy_and_save_picks(date_str)
