"""
Regressed XGBoost - Separate Analysis of Favorites vs Underdogs
Tests performance at different edge thresholds for each category independently
"""

import pandas as pd
import numpy as np
from pathlib import Path

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
            return 100 / abs(odds)  # Favorite wins
        else:
            return odds / 100  # Underdog wins
    else:
        return -1  # Loss

# =============================================================================
# LOAD DATA
# =============================================================================

print("="*80)
print("REGRESSED XGBOOST - FAVORITES vs UNDERDOGS ANALYSIS")
print("="*80)
print()

# Load all XGBoost predictions
xgb_files = sorted((REPO_ROOT / 'modeling' / 'mlb_xgb_ml' / 'predictions').glob('predictions_2026-*.csv'))
xgb_predictions = []
for f in xgb_files:
    df = pd.read_csv(f)
    xgb_predictions.append(df)

df_xgb = pd.concat(xgb_predictions, ignore_index=True)
df_xgb = df_xgb.rename(columns={
    'xgboost_home_prob': 'xgb_home_prob',
    'home team': 'home_team',
    'away team': 'away_team',
    'home odds': 'home_odds',
    'away odds': 'away_odds'
})

print(f"Loaded {len(df_xgb)} XGBoost predictions")

# Load actual results from boxscores
from datetime import datetime
boxscore_files = sorted((REPO_ROOT / 'data' / '2026_data' / 'mlb_data' / 'raw' / 'boxscores').glob('boxscores_2026-*.csv'))
boxscores = []
for f in boxscore_files:
    bs = pd.read_csv(f)
    # Extract date from filename
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

# Merge with actual results
df = df_xgb.merge(df_boxscores[['date', 'home_team', 'away_team', 'home_runs_scored', 'away_runs_scored']],
                  on=['date', 'home_team', 'away_team'], how='left')

# Calculate actual winner
df['home_win'] = (df['home_runs_scored'] > df['away_runs_scored']).astype(float)

# Filter to only games with results
df = df[df['home_win'].notna()].copy()

print(f"Games with results: {len(df)}")
print()

# Calculate market probabilities
df['market_home_prob'] = df['home_odds'].apply(odds_to_prob)
df['market_away_prob'] = df['away_odds'].apply(odds_to_prob)

# Calculate REGRESSED probabilities (65% market + 35% model)
df['xgb_regressed_home_prob'] = 0.65 * df['market_home_prob'] + 0.35 * df['xgb_home_prob']
df['xgb_regressed_away_prob'] = 0.65 * df['market_away_prob'] + 0.35 * (1 - df['xgb_home_prob'])

# Calculate REGRESSED edges
df['xgb_regressed_home_edge'] = (df['xgb_regressed_home_prob'] - df['market_home_prob']) * 100
df['xgb_regressed_away_edge'] = (df['xgb_regressed_away_prob'] - df['market_away_prob']) * 100

# Determine favorite/underdog
df['home_is_favorite'] = df['home_odds'] < df['away_odds']

# =============================================================================
# FAVORITES ANALYSIS
# =============================================================================

print("="*80)
print("FAVORITES ONLY - Performance by Edge Threshold")
print("="*80)
print()

thresholds = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

print(f"{'Threshold':<12} {'Picks':<8} {'Record':<12} {'Win%':<8} {'Profit':<10} {'ROI':<8} {'Avg Edge':<10}")
print("-" * 80)

favorite_results = []

for threshold in thresholds:
    picks = []
    
    for _, row in df.iterrows():
        home_edge = row['xgb_regressed_home_edge']
        away_edge = row['xgb_regressed_away_edge']
        home_is_fav = row['home_is_favorite']
        
        # Pick home if home is favorite and has sufficient edge
        if home_is_fav and home_edge >= threshold:
            win = row['home_win'] == 1
            profit = calculate_profit(row['home_odds'], win)
            picks.append({
                'edge': home_edge,
                'odds': row['home_odds'],
                'win': win,
                'profit': profit
            })
        
        # Pick away if away is favorite and has sufficient edge
        if not home_is_fav and away_edge >= threshold:
            win = row['home_win'] == 0
            profit = calculate_profit(row['away_odds'], win)
            picks.append({
                'edge': away_edge,
                'odds': row['away_odds'],
                'win': win,
                'profit': profit
            })
    
    if len(picks) > 0:
        picks_df = pd.DataFrame(picks)
        total_picks = len(picks_df)
        wins = picks_df['win'].sum()
        losses = total_picks - wins
        win_rate = wins / total_picks * 100
        total_profit = picks_df['profit'].sum()
        roi = total_profit / total_picks * 100
        avg_edge = picks_df['edge'].mean()
        
        favorite_results.append({
            'threshold': threshold,
            'picks': total_picks,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'profit': total_profit,
            'roi': roi,
            'avg_edge': avg_edge
        })
        
        print(f"{threshold}%{'':<9} {total_picks:<8} {int(wins)}-{int(losses):<11} "
              f"{win_rate:<7.1f}% {total_profit:<+9.2f} {roi:<7.1f}% {avg_edge:<9.2f}")

print()

# =============================================================================
# UNDERDOGS ANALYSIS
# =============================================================================

print("="*80)
print("UNDERDOGS ONLY - Performance by Edge Threshold")
print("="*80)
print()

print(f"{'Threshold':<12} {'Picks':<8} {'Record':<12} {'Win%':<8} {'Profit':<10} {'ROI':<8} {'Avg Edge':<10}")
print("-" * 80)

underdog_results = []

for threshold in thresholds:
    picks = []
    
    for _, row in df.iterrows():
        home_edge = row['xgb_regressed_home_edge']
        away_edge = row['xgb_regressed_away_edge']
        home_is_fav = row['home_is_favorite']
        
        # Pick home if home is underdog and has sufficient edge
        if not home_is_fav and home_edge >= threshold:
            win = row['home_win'] == 1
            profit = calculate_profit(row['home_odds'], win)
            picks.append({
                'edge': home_edge,
                'odds': row['home_odds'],
                'win': win,
                'profit': profit
            })
        
        # Pick away if away is underdog and has sufficient edge
        if home_is_fav and away_edge >= threshold:
            win = row['home_win'] == 0
            profit = calculate_profit(row['away_odds'], win)
            picks.append({
                'edge': away_edge,
                'odds': row['away_odds'],
                'win': win,
                'profit': profit
            })
    
    if len(picks) > 0:
        picks_df = pd.DataFrame(picks)
        total_picks = len(picks_df)
        wins = picks_df['win'].sum()
        losses = total_picks - wins
        win_rate = wins / total_picks * 100
        total_profit = picks_df['profit'].sum()
        roi = total_profit / total_picks * 100
        avg_edge = picks_df['edge'].mean()
        
        underdog_results.append({
            'threshold': threshold,
            'picks': total_picks,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'profit': total_profit,
            'roi': roi,
            'avg_edge': avg_edge
        })
        
        print(f"{threshold}%{'':<9} {total_picks:<8} {int(wins)}-{int(losses):<11} "
              f"{win_rate:<7.1f}% {total_profit:<+9.2f} {roi:<7.1f}% {avg_edge:<9.2f}")

print()

# =============================================================================
# SUMMARY COMPARISON
# =============================================================================

print("="*80)
print("SUMMARY: FAVORITES vs UNDERDOGS")
print("="*80)
print()

print(f"{'Threshold':<12} {'Favorites ROI':<15} {'Favorites Picks':<17} {'Underdogs ROI':<15} {'Underdogs Picks':<17} {'Better?':<10}")
print("-" * 95)

for fav_result in favorite_results:
    threshold = fav_result['threshold']
    # Find matching underdog result
    dog_result = next((r for r in underdog_results if r['threshold'] == threshold), None)
    
    if dog_result:
        fav_roi_str = f"{fav_result['roi']:+.1f}%"
        fav_picks_str = f"{fav_result['picks']} picks"
        dog_roi_str = f"{dog_result['roi']:+.1f}%"
        dog_picks_str = f"{dog_result['picks']} picks"
        
        better = "Favorites" if fav_result['roi'] > dog_result['roi'] else "Underdogs"
        
        print(f"{threshold}%{'':<9} {fav_roi_str:<15} {fav_picks_str:<17} "
              f"{dog_roi_str:<15} {dog_picks_str:<17} {better:<10}")

print()

# Find best thresholds
best_fav = max(favorite_results, key=lambda x: x['roi'])
best_dog = max(underdog_results, key=lambda x: x['roi'])
best_fav_profit = max(favorite_results, key=lambda x: x['profit'])
best_dog_profit = max(underdog_results, key=lambda x: x['profit'])

print("="*80)
print("BEST STRATEGIES:")
print("="*80)
print()
print(f"🏆 Best Favorites ROI:")
print(f"   {best_fav['threshold']}% threshold: {best_fav['picks']} picks, "
      f"{int(best_fav['wins'])}-{int(best_fav['losses'])} ({best_fav['win_rate']:.1f}%), "
      f"{best_fav['profit']:+.2f}u, {best_fav['roi']:.1f}% ROI")
print()
print(f"🏆 Best Favorites Profit:")
print(f"   {best_fav_profit['threshold']}% threshold: {best_fav_profit['picks']} picks, "
      f"{int(best_fav_profit['wins'])}-{int(best_fav_profit['losses'])} ({best_fav_profit['win_rate']:.1f}%), "
      f"{best_fav_profit['profit']:+.2f}u, {best_fav_profit['roi']:.1f}% ROI")
print()
print(f"🏆 Best Underdogs ROI:")
print(f"   {best_dog['threshold']}% threshold: {best_dog['picks']} picks, "
      f"{int(best_dog['wins'])}-{int(best_dog['losses'])} ({best_dog['win_rate']:.1f}%), "
      f"{best_dog['profit']:+.2f}u, {best_dog['roi']:.1f}% ROI")
print()
print(f"🏆 Best Underdogs Profit:")
print(f"   {best_dog_profit['threshold']}% threshold: {best_dog_profit['picks']} picks, "
      f"{int(best_dog_profit['wins'])}-{int(best_dog_profit['losses'])} ({best_dog_profit['win_rate']:.1f}%), "
      f"{best_dog_profit['profit']:+.2f}u, {best_dog_profit['roi']:.1f}% ROI")
print()
print("="*80)
