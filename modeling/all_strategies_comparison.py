"""
Compare all strategies with latest data
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
    boxscores.append(bs)

df_boxscores = pd.concat(boxscores, ignore_index=True)
df_boxscores = df_boxscores.rename(columns={
    'home_batting_r': 'home_runs_scored',
    'away_batting_r': 'away_runs_scored',
    'home_team_abbreviation': 'home_team',
    'away_team_abbreviation': 'away_team'
})

# Merge
df = df.merge(df_boxscores[['date', 'home_team', 'away_team', 'home_runs_scored', 'away_runs_scored']],
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
        'name': '0.5% Dog / 1.5% Fav (REGRESSED)',
        'underdog_threshold': 0.5,
        'favorite_threshold': 1.5,
        'approach': 'regressed'
    },
    {
        'name': '1% Symmetric (REGRESSED)',
        'underdog_threshold': 1.0,
        'favorite_threshold': 1.0,
        'approach': 'regressed'
    },
    {
        'name': '1.5% Dog / 0.5% Fav (REGRESSED)',
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
# ANALYZE EACH STRATEGY
# =============================================================================

print("="*80)
print("STRATEGY COMPARISON - ALL DATA THROUGH JUNE 21, 2026")
print("="*80)
print()

results = []
detailed_results = []

for strategy in strategies:
    underdog_threshold = strategy['underdog_threshold']
    favorite_threshold = strategy['favorite_threshold']
    approach = strategy['approach']
    
    edge_suffix = f'_{approach}_home_edge' if approach == 'regressed' else '_raw_home_edge'
    home_edge_col = 'xgb' + edge_suffix
    away_edge_col = home_edge_col.replace('_home_', '_away_')
    
    picks = []
    
    for _, row in df.iterrows():
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
            picks.append({
                'win': win,
                'profit': profit,
                'is_favorite': home_is_fav,
                'is_home': True
            })
        
        # Check if we pick away
        if away_edge >= away_threshold:
            win = row['home_win'] == 0
            profit = calculate_profit(row['away_odds'], win)
            picks.append({
                'win': win,
                'profit': profit,
                'is_favorite': not home_is_fav,
                'is_home': False
            })
    
    if len(picks) > 0:
        picks_df = pd.DataFrame(picks)
        total_picks = len(picks_df)
        wins = picks_df['win'].sum()
        losses = total_picks - wins
        win_rate = wins / total_picks * 100
        total_profit = picks_df['profit'].sum()
        roi = total_profit / total_picks * 100
        
        # Calculate fav/dog and home/away splits
        fav_picks = picks_df[picks_df['is_favorite']]
        dog_picks = picks_df[~picks_df['is_favorite']]
        home_picks = picks_df[picks_df['is_home']]
        away_picks = picks_df[~picks_df['is_home']]
        
        fav_count = len(fav_picks)
        dog_count = len(dog_picks)
        home_count = len(home_picks)
        away_count = len(away_picks)
        
        fav_pct = (fav_count / total_picks * 100) if total_picks > 0 else 0
        dog_pct = (dog_count / total_picks * 100) if total_picks > 0 else 0
        home_pct = (home_count / total_picks * 100) if total_picks > 0 else 0
        away_pct = (away_count / total_picks * 100) if total_picks > 0 else 0
        
        results.append({
            'Strategy': strategy['name'],
            'Picks': total_picks,
            'Wins': int(wins),
            'Losses': int(losses),
            'Win%': win_rate,
            'Profit': total_profit,
            'ROI': roi
        })
        
        detailed_results.append({
            'Strategy': strategy['name'],
            'Total_Picks': total_picks,
            'Fav_Picks': fav_count,
            'Fav_Pct': fav_pct,
            'Dog_Picks': dog_count,
            'Dog_Pct': dog_pct,
            'Home_Picks': home_count,
            'Home_Pct': home_pct,
            'Away_Picks': away_count,
            'Away_Pct': away_pct,
            'Fav_Profit': fav_picks['profit'].sum() if len(fav_picks) > 0 else 0,
            'Dog_Profit': dog_picks['profit'].sum() if len(dog_picks) > 0 else 0,
            'Home_Profit': home_picks['profit'].sum() if len(home_picks) > 0 else 0,
            'Away_Profit': away_picks['profit'].sum() if len(away_picks) > 0 else 0
        })

# Create results DataFrame
results_df = pd.DataFrame(results)

# Display results
print(f"{'Strategy':<35} {'Picks':<8} {'Record':<15} {'Win%':<8} {'Profit':<12} {'ROI':<8}")
print("-" * 95)

for _, row in results_df.iterrows():
    print(f"{row['Strategy']:<35} {row['Picks']:<8} "
          f"{row['Wins']}-{row['Losses']:<14} "
          f"{row['Win%']:<7.1f}% {row['Profit']:<+11.2f} "
          f"{row['ROI']:<7.1f}%")

print()
print("="*80)
print("RANKING BY PROFIT:")
print("="*80)
results_df_sorted = results_df.sort_values('Profit', ascending=False).reset_index(drop=True)
for i, row in results_df_sorted.iterrows():
    rank_symbol = ['🥇', '🥈', '🥉', '4️⃣'][i] if i < 4 else str(i+1)
    print(f"{rank_symbol} {row['Strategy']:<35} {row['Profit']:+.2f} units ({row['ROI']:.1f}% ROI)")

print()
print("="*80)
print("RANKING BY ROI:")
print("="*80)
results_df_sorted = results_df.sort_values('ROI', ascending=False).reset_index(drop=True)
for i, row in results_df_sorted.iterrows():
    rank_symbol = ['🥇', '🥈', '🥉', '4️⃣'][i] if i < 4 else str(i+1)
    print(f"{rank_symbol} {row['Strategy']:<35} {row['ROI']:.1f}% ROI ({row['Profit']:+.2f} units)")

print()
print("="*80)
print("RANKING BY WIN RATE:")
print("="*80)
results_df_sorted = results_df.sort_values('Win%', ascending=False).reset_index(drop=True)
for i, row in results_df_sorted.iterrows():
    rank_symbol = ['🥇', '🥈', '🥉', '4️⃣'][i] if i < 4 else str(i+1)
    print(f"{rank_symbol} {row['Strategy']:<35} {row['Win%']:.1f}% ({row['Wins']}-{row['Losses']})")

print()
print("="*80)
print("FAVORITE vs UNDERDOG BREAKDOWN")
print("="*80)
print()

detailed_df = pd.DataFrame(detailed_results)
for _, row in detailed_df.iterrows():
    print(f"{row['Strategy']}:")
    print(f"  Favorites: {row['Fav_Picks']:3d} picks ({row['Fav_Pct']:5.1f}%) → {row['Fav_Profit']:+.2f}u profit")
    print(f"  Underdogs: {row['Dog_Picks']:3d} picks ({row['Dog_Pct']:5.1f}%) → {row['Dog_Profit']:+.2f}u profit")
    
    if row['Dog_Pct'] > row['Fav_Pct']:
        diff = row['Dog_Pct'] - row['Fav_Pct']
        print(f"  🐕 LEANS UNDERDOG by {diff:.1f} percentage points")
    else:
        diff = row['Fav_Pct'] - row['Dog_Pct']
        print(f"  ⭐ LEANS FAVORITE by {diff:.1f} percentage points")
    print()

print("="*80)
print("HOME vs AWAY BREAKDOWN")
print("="*80)
print()

for _, row in detailed_df.iterrows():
    print(f"{row['Strategy']}:")
    print(f"  Home: {row['Home_Picks']:3d} picks ({row['Home_Pct']:5.1f}%) → {row['Home_Profit']:+.2f}u profit")
    print(f"  Away: {row['Away_Picks']:3d} picks ({row['Away_Pct']:5.1f}%) → {row['Away_Profit']:+.2f}u profit")
    
    if row['Home_Pct'] > row['Away_Pct']:
        diff = row['Home_Pct'] - row['Away_Pct']
        print(f"  🏠 LEANS HOME by {diff:.1f} percentage points")
    else:
        diff = row['Away_Pct'] - row['Home_Pct']
        print(f"  ✈️  LEANS AWAY by {diff:.1f} percentage points")
    print()

print()
