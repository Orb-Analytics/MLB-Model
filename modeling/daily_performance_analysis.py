"""
Analyze day-by-day performance for recent period
Shows exactly when and where the models started declining
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def odds_to_prob(odds):
    """Convert American odds to implied probability"""
    if pd.isna(odds):
        return np.nan
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    else:
        return 100 / (odds + 100)

def calculate_profit(odds, win):
    """Calculate profit/loss for a bet"""
    if pd.isna(odds):
        return 0
    if win:
        if odds < 0:
            return 100 / abs(odds)
        else:
            return odds / 100
    else:
        return -1

# =============================================================================
# LOAD DATA
# =============================================================================

print("Loading data...")

# Load XGBoost predictions
xgb_files = sorted((REPO_ROOT / 'modeling' / 'mlb_xgb_ml' / 'predictions').glob('predictions_2026-*.csv'))
xgb_predictions = []
for f in xgb_files:
    df = pd.read_csv(f)
    xgb_predictions.append(df)

df = pd.concat(xgb_predictions, ignore_index=True)
df = df.rename(columns={
    'xgboost_home_prob': 'xgb_home_prob',
    'home team': 'home_team',
    'away team': 'away_team',
    'home odds': 'home_odds',
    'away odds': 'away_odds'
})

# Load boxscores
boxscore_files = sorted((REPO_ROOT / 'data' / '2026_data' / 'mlb_data' / 'raw' / 'boxscores').glob('boxscores_2026-*.csv'))
boxscores = []
for f in boxscore_files:
    bs = pd.read_csv(f)
    date_str = f.stem.replace('boxscores_', '')
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    date_fmt = f'{date_obj.month}/{date_obj.day}/{date_obj.year}'
    bs['date'] = date_fmt
    bs['date_obj'] = date_obj
    boxscores.append(bs)

df_boxscores = pd.concat(boxscores, ignore_index=True)
df_boxscores = df_boxscores.rename(columns={
    'home_batting_r': 'home_runs_scored',
    'away_batting_r': 'away_runs_scored',
    'home_team_abbreviation': 'home_team',
    'away_team_abbreviation': 'away_team'
})

# Merge
df = df.merge(df_boxscores[['date', 'home_team', 'away_team', 'home_runs_scored', 'away_runs_scored', 'date_obj']],
              on=['date', 'home_team', 'away_team'], how='left')

# Only calculate home_win if both scores exist
df['home_win'] = np.where(
    df['home_runs_scored'].notna() & df['away_runs_scored'].notna(),
    (df['home_runs_scored'] > df['away_runs_scored']).astype(float),
    np.nan
)
df = df[df['home_win'].notna()].copy()

# Calculate probabilities and edges
df['market_home_prob'] = df['home_odds'].apply(odds_to_prob)
df['market_away_prob'] = df['away_odds'].apply(odds_to_prob)

# RAW edges
df['xgb_raw_home_edge'] = (df['xgb_home_prob'] - df['market_home_prob']) * 100
df['xgb_raw_away_edge'] = ((1 - df['xgb_home_prob']) - df['market_away_prob']) * 100

# REGRESSED probabilities and edges
df['xgb_regressed_home_prob'] = 0.65 * df['market_home_prob'] + 0.35 * df['xgb_home_prob']
df['xgb_regressed_away_prob'] = 0.65 * df['market_away_prob'] + 0.35 * (1 - df['xgb_home_prob'])

df['xgb_regressed_home_edge'] = (df['xgb_regressed_home_prob'] - df['market_home_prob']) * 100
df['xgb_regressed_away_edge'] = (df['xgb_regressed_away_prob'] - df['market_away_prob']) * 100

df['home_is_favorite'] = df['home_odds'] < df['away_odds']

print(f"Total games analyzed: {len(df)}")
print()

# =============================================================================
# DEFINE STRATEGIES
# =============================================================================

strategies = [
    {
        'name': '0.5% Dog / 1.5% Fav (REG)',
        'underdog_threshold': 0.5,
        'favorite_threshold': 1.5,
        'approach': 'regressed'
    },
    {
        'name': '1% Symmetric (REG)',
        'underdog_threshold': 1.0,
        'favorite_threshold': 1.0,
        'approach': 'regressed'
    },
    {
        'name': '1.5% Dog / 0.5% Fav (REG)',
        'underdog_threshold': 1.5,
        'favorite_threshold': 0.5,
        'approach': 'regressed'
    },
    {
        'name': '1% Symmetric (RAW)',
        'underdog_threshold': 1.0,
        'favorite_threshold': 1.0,
        'approach': 'raw'
    }
]

# =============================================================================
# ANALYZE DAILY PERFORMANCE
# =============================================================================

# Focus on recent period - last 3 weeks
recent_cutoff = datetime(2026, 6, 1)
df_recent = df[df['date_obj'] >= recent_cutoff].copy()

print("="*80)
print("DAILY PERFORMANCE BREAKDOWN: JUNE 1-21, 2026")
print("="*80)
print()

# Get unique dates sorted
dates = sorted(df_recent['date_obj'].unique())

for strategy in strategies:
    print("="*80)
    print(f"{strategy['name']}")
    print("="*80)
    print()
    
    underdog_threshold = strategy['underdog_threshold']
    favorite_threshold = strategy['favorite_threshold']
    approach = strategy['approach']
    
    edge_suffix = f'_{approach}_home_edge' if approach == 'regressed' else '_raw_home_edge'
    home_edge_col = 'xgb' + edge_suffix
    away_edge_col = home_edge_col.replace('_home_', '_away_')
    
    cumulative_profit = 0
    
    print(f"{'Date':<12} {'Picks':<7} {'Record':<10} {'Win%':<7} {'Daily P/L':<12} {'Cumulative':<12}")
    print("-" * 80)
    
    for date_obj in dates:
        date_str = f"{date_obj.month}/{date_obj.day}/{date_obj.year}"
        df_day = df_recent[df_recent['date_obj'] == date_obj]
        
        picks = []
        
        for _, row in df_day.iterrows():
            home_edge = row[home_edge_col]
            away_edge = row[away_edge_col]
            home_is_fav = row['home_is_favorite']
            
            # Determine thresholds
            home_threshold = favorite_threshold if home_is_fav else underdog_threshold
            away_threshold = underdog_threshold if home_is_fav else favorite_threshold
            
            # Check if we pick home
            if home_edge >= home_threshold:
                win = row['home_win'] == 1
                profit = calculate_profit(row['home_odds'], win)
                picks.append({'win': win, 'profit': profit})
            
            # Check if we pick away
            if away_edge >= away_threshold:
                win = row['home_win'] == 0
                profit = calculate_profit(row['away_odds'], win)
                picks.append({'win': win, 'profit': profit})
        
        if len(picks) > 0:
            picks_df = pd.DataFrame(picks)
            total_picks = len(picks_df)
            wins = picks_df['win'].sum()
            win_rate = wins / total_picks * 100
            daily_profit = picks_df['profit'].sum()
            cumulative_profit += daily_profit
            
            # Format date nicely
            date_display = date_obj.strftime('%m/%d')
            
            # Color code based on profit
            profit_str = f"{daily_profit:+.2f}u"
            cumulative_str = f"{cumulative_profit:+.2f}u"
            
            print(f"{date_display:<12} {total_picks:<7} {int(wins)}-{int(total_picks-wins):<9} "
                  f"{win_rate:<6.1f}% {profit_str:<12} {cumulative_str:<12}")
        else:
            # No picks this day
            date_display = date_obj.strftime('%m/%d')
            print(f"{date_display:<12} {'0':<7} {'-':<10} {'-':<7} {'-':<12} {cumulative_profit:+.2f}u")
    
    print()
    print(f"TOTAL: {cumulative_profit:+.2f} units")
    print()

print("="*80)
print("ANALYSIS COMPLETE")
print("="*80)
