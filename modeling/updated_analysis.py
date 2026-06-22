"""
Updated Analysis - Recent Model Performance
- Overall records for XGBoost and CatBoost
- Week-by-week performance breakdown
- Asymmetric edge threshold testing for XGBoost
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

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
print("UPDATED MODEL ANALYSIS - PRODUCTION PERFORMANCE")
print("="*80)
print()

# Load all XGBoost predictions
xgb_files = sorted((REPO_ROOT / 'modeling' / 'mlb_xgb_ml' / 'predictions').glob('predictions_2026-*.csv'))
xgb_predictions = []
for f in xgb_files:
    df = pd.read_csv(f)
    xgb_predictions.append(df)

df_xgb = pd.concat(xgb_predictions, ignore_index=True)
print(f"Loaded {len(df_xgb)} XGBoost predictions from {len(xgb_files)} files")

# Load all CatBoost predictions
cb_files = sorted((REPO_ROOT / 'modeling' / 'catboost_predictions').glob('predictions_2026-*.csv'))
cb_predictions = []
for f in cb_files:
    df = pd.read_csv(f)
    cb_predictions.append(df)

df_cb = pd.concat(cb_predictions, ignore_index=True)
print(f"Loaded {len(df_cb)} CatBoost predictions from {len(cb_files)} files")

# Rename columns for clarity and standardize column names
df_xgb = df_xgb.rename(columns={
    'xgboost_home_prob': 'xgb_home_prob',
    'home team': 'home_team',
    'away team': 'away_team',
    'home odds': 'home_odds',
    'away odds': 'away_odds'
})
df_cb = df_cb.rename(columns={'catboost_home_prob': 'cb_home_prob'})

# Merge predictions
df = df_xgb.merge(df_cb[['date', 'home_team', 'away_team', 'cb_home_prob']], 
                  on=['date', 'home_team', 'away_team'], how='outer')

print(f"Combined dataset: {len(df)} games")
print()

# Load actual results from boxscores
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
df = df.merge(df_boxscores[['date', 'home_team', 'away_team', 'home_runs_scored', 'away_runs_scored']],
              on=['date', 'home_team', 'away_team'], how='left')

# Calculate actual winner
df['home_win'] = (df['home_runs_scored'] > df['away_runs_scored']).astype(float)

# Filter to only games with results
df_with_results = df[df['home_win'].notna()].copy()
print(f"Games with results: {len(df_with_results)}")
print()

# Calculate market probabilities and edges
df_with_results['market_home_prob'] = df_with_results['home_odds'].apply(odds_to_prob)
df_with_results['market_away_prob'] = df_with_results['away_odds'].apply(odds_to_prob)

# Calculate RAW edges (model prob - market prob, in percentage points)
df_with_results['xgb_raw_home_edge'] = (df_with_results['xgb_home_prob'] - df_with_results['market_home_prob']) * 100
df_with_results['xgb_raw_away_edge'] = ((1 - df_with_results['xgb_home_prob']) - df_with_results['market_away_prob']) * 100
df_with_results['cb_raw_home_edge'] = (df_with_results['cb_home_prob'] - df_with_results['market_home_prob']) * 100
df_with_results['cb_raw_away_edge'] = ((1 - df_with_results['cb_home_prob']) - df_with_results['market_away_prob']) * 100

# Calculate REGRESSED probabilities (65% market + 35% model)
df_with_results['xgb_regressed_home_prob'] = 0.65 * df_with_results['market_home_prob'] + 0.35 * df_with_results['xgb_home_prob']
df_with_results['xgb_regressed_away_prob'] = 0.65 * df_with_results['market_away_prob'] + 0.35 * (1 - df_with_results['xgb_home_prob'])
df_with_results['cb_regressed_home_prob'] = 0.65 * df_with_results['market_home_prob'] + 0.35 * df_with_results['cb_home_prob']
df_with_results['cb_regressed_away_prob'] = 0.65 * df_with_results['market_away_prob'] + 0.35 * (1 - df_with_results['cb_home_prob'])

# Calculate REGRESSED edges
df_with_results['xgb_regressed_home_edge'] = (df_with_results['xgb_regressed_home_prob'] - df_with_results['market_home_prob']) * 100
df_with_results['xgb_regressed_away_edge'] = (df_with_results['xgb_regressed_away_prob'] - df_with_results['market_away_prob']) * 100
df_with_results['cb_regressed_home_edge'] = (df_with_results['cb_regressed_home_prob'] - df_with_results['market_home_prob']) * 100
df_with_results['cb_regressed_away_edge'] = (df_with_results['cb_regressed_away_prob'] - df_with_results['market_away_prob']) * 100

# Determine favorite/underdog
df_with_results['home_is_favorite'] = df_with_results['home_odds'] < df_with_results['away_odds']

# Add week number
df_with_results['date_obj'] = pd.to_datetime(df_with_results['date'])
df_with_results['week'] = df_with_results['date_obj'].dt.isocalendar().week

# =============================================================================
# OVERALL PERFORMANCE
# =============================================================================

print("="*80)
print("OVERALL MODEL PERFORMANCE (ALL GAMES WITH RESULTS)")
print("="*80)
print()

# For overall performance, let's use a simple 1% edge threshold
threshold = 1.0

def analyze_model(df, model_prefix, approach='raw'):
    """Analyze overall performance for a model
    
    Args:
        df: DataFrame with predictions and results
        model_prefix: 'xgb' or 'cb'
        approach: 'raw' or 'regressed'
    """
    
    results = {}
    
    # Select the appropriate edge columns
    if approach == 'raw':
        home_edge_col = f'{model_prefix}_raw_home_edge'
        away_edge_col = f'{model_prefix}_raw_away_edge'
    else:  # regressed
        home_edge_col = f'{model_prefix}_regressed_home_edge'
        away_edge_col = f'{model_prefix}_regressed_away_edge'
    
    # Make picks where either home or away has edge >= threshold
    home_picks = df[df[home_edge_col] >= threshold].copy()
    away_picks = df[df[away_edge_col] >= threshold].copy()
    
    # Calculate results for home picks
    home_picks['win'] = home_picks['home_win'] == 1
    home_picks['profit'] = home_picks.apply(
        lambda row: calculate_profit(row['home_odds'], row['win']), axis=1
    )
    
    # Calculate results for away picks
    away_picks['win'] = away_picks['home_win'] == 0
    away_picks['profit'] = away_picks.apply(
        lambda row: calculate_profit(row['away_odds'], row['win']), axis=1
    )
    
    # Combine all picks
    all_picks = pd.concat([home_picks, away_picks])
    
    results['total_picks'] = len(all_picks)
    results['wins'] = all_picks['win'].sum()
    results['losses'] = len(all_picks) - results['wins']
    results['win_rate'] = results['wins'] / results['total_picks'] * 100 if results['total_picks'] > 0 else 0
    results['total_profit'] = all_picks['profit'].sum()
    results['roi'] = results['total_profit'] / results['total_picks'] * 100 if results['total_picks'] > 0 else 0
    
    return results, all_picks

xgb_raw_results, xgb_raw_picks = analyze_model(df_with_results, 'xgb', 'raw')
xgb_reg_results, xgb_reg_picks = analyze_model(df_with_results, 'xgb', 'regressed')
cb_raw_results, cb_raw_picks = analyze_model(df_with_results, 'cb', 'raw')
cb_reg_results, cb_reg_picks = analyze_model(df_with_results, 'cb', 'regressed')

print(f"📊 XGBOOST RAW (1% Edge Threshold):")
print(f"   Total Picks: {xgb_raw_results['total_picks']}")
print(f"   Record: {int(xgb_raw_results['wins'])}-{int(xgb_raw_results['losses'])} ({xgb_raw_results['win_rate']:.1f}%)")
print(f"   Profit: {xgb_raw_results['total_profit']:+.2f} units")
print(f"   ROI: {xgb_raw_results['roi']:.1f}%")
print()

print(f"📊 XGBOOST REGRESSED (1% Edge Threshold):")
print(f"   Total Picks: {xgb_reg_results['total_picks']}")
print(f"   Record: {int(xgb_reg_results['wins'])}-{int(xgb_reg_results['losses'])} ({xgb_reg_results['win_rate']:.1f}%)")
print(f"   Profit: {xgb_reg_results['total_profit']:+.2f} units")
print(f"   ROI: {xgb_reg_results['roi']:.1f}%")
print()

print(f"📊 CATBOOST RAW (1% Edge Threshold):")
print(f"   Total Picks: {cb_raw_results['total_picks']}")
print(f"   Record: {int(cb_raw_results['wins'])}-{int(cb_raw_results['losses'])} ({cb_raw_results['win_rate']:.1f}%)")
print(f"   Profit: {cb_raw_results['total_profit']:+.2f} units")
print(f"   ROI: {cb_raw_results['roi']:.1f}%")
print()

print(f"📊 CATBOOST REGRESSED (1% Edge Threshold):")
print(f"   Total Picks: {cb_reg_results['total_picks']}")
print(f"   Record: {int(cb_reg_results['wins'])}-{int(cb_reg_results['losses'])} ({cb_reg_results['win_rate']:.1f}%)")
print(f"   Profit: {cb_reg_results['total_profit']:+.2f} units")
print(f"   ROI: {cb_reg_results['roi']:.1f}%")
print()

# =============================================================================
# WEEK-BY-WEEK BREAKDOWN
# =============================================================================

print("="*80)
print("WEEK-BY-WEEK PERFORMANCE BREAKDOWN")
print("="*80)
print()

weeks = sorted(df_with_results['week'].unique())

print("XGBOOST RAW - Week by Week (1% Edge):")
print("-" * 80)
print(f"{'Week':<6} {'Dates':<20} {'Picks':<7} {'Record':<12} {'Win%':<8} {'Profit':<10} {'ROI':<8}")
print("-" * 80)

for week in weeks:
    week_data = df_with_results[df_with_results['week'] == week]
    week_results, week_picks = analyze_model(week_data, 'xgb', 'raw')
    
    # Get date range for the week
    dates = week_data['date_obj'].dt.strftime('%m/%d').unique()
    date_range = f"{dates[0]} - {dates[-1]}" if len(dates) > 1 else dates[0]
    
    if week_results['total_picks'] > 0:
        print(f"{week:<6} {date_range:<20} {week_results['total_picks']:<7} "
              f"{int(week_results['wins'])}-{int(week_results['losses']):<11} "
              f"{week_results['win_rate']:<7.1f}% {week_results['total_profit']:<+9.2f} "
              f"{week_results['roi']:<7.1f}%")

print()
print("XGBOOST REGRESSED - Week by Week (1% Edge):")
print("-" * 80)
print(f"{'Week':<6} {'Dates':<20} {'Picks':<7} {'Record':<12} {'Win%':<8} {'Profit':<10} {'ROI':<8}")
print("-" * 80)

for week in weeks:
    week_data = df_with_results[df_with_results['week'] == week]
    week_results, week_picks = analyze_model(week_data, 'xgb', 'regressed')
    
    # Get date range for the week
    dates = week_data['date_obj'].dt.strftime('%m/%d').unique()
    date_range = f"{dates[0]} - {dates[-1]}" if len(dates) > 1 else dates[0]
    
    if week_results['total_picks'] > 0:
        print(f"{week:<6} {date_range:<20} {week_results['total_picks']:<7} "
              f"{int(week_results['wins'])}-{int(week_results['losses']):<11} "
              f"{week_results['win_rate']:<7.1f}% {week_results['total_profit']:<+9.2f} "
              f"{week_results['roi']:<7.1f}%")

print()
print("CATBOOST RAW - Week by Week (1% Edge):")
print("-" * 80)
print(f"{'Week':<6} {'Dates':<20} {'Picks':<7} {'Record':<12} {'Win%':<8} {'Profit':<10} {'ROI':<8}")
print("-" * 80)

for week in weeks:
    week_data = df_with_results[df_with_results['week'] == week]
    week_results, week_picks = analyze_model(week_data, 'cb', 'raw')
    
    # Get date range for the week
    dates = week_data['date_obj'].dt.strftime('%m/%d').unique()
    date_range = f"{dates[0]} - {dates[-1]}" if len(dates) > 1 else dates[0]
    
    if week_results['total_picks'] > 0:
        print(f"{week:<6} {date_range:<20} {week_results['total_picks']:<7} "
              f"{int(week_results['wins'])}-{int(week_results['losses']):<11} "
              f"{week_results['win_rate']:<7.1f}% {week_results['total_profit']:<+9.2f} "
              f"{week_results['roi']:<7.1f}%")

print()
print("CATBOOST REGRESSED - Week by Week (1% Edge):")
print("-" * 80)
print(f"{'Week':<6} {'Dates':<20} {'Picks':<7} {'Record':<12} {'Win%':<8} {'Profit':<10} {'ROI':<8}")
print("-" * 80)

for week in weeks:
    week_data = df_with_results[df_with_results['week'] == week]
    week_results, week_picks = analyze_model(week_data, 'cb', 'regressed')
    
    # Get date range for the week
    dates = week_data['date_obj'].dt.strftime('%m/%d').unique()
    date_range = f"{dates[0]} - {dates[-1]}" if len(dates) > 1 else dates[0]
    
    if week_results['total_picks'] > 0:
        print(f"{week:<6} {date_range:<20} {week_results['total_picks']:<7} "
              f"{int(week_results['wins'])}-{int(week_results['losses']):<11} "
              f"{week_results['win_rate']:<7.1f}% {week_results['total_profit']:<+9.2f} "
              f"{week_results['roi']:<7.1f}%")

print()

# =============================================================================
# ASYMMETRIC EDGE THRESHOLD TESTING (XGBOOST ONLY)
# =============================================================================

print("="*80)
print("ASYMMETRIC EDGE THRESHOLD ANALYSIS - XGBOOST")
print("="*80)
print()

def test_asymmetric_strategy(df, favorite_threshold, underdog_threshold, approach='raw'):
    """Test asymmetric edge thresholds
    
    Args:
        df: DataFrame with predictions and results
        favorite_threshold: Edge threshold for favorites
        underdog_threshold: Edge threshold for underdogs
        approach: 'raw' or 'regressed'
    """
    
    picks = []
    
    # Select the appropriate edge columns
    if approach == 'raw':
        home_edge_col = 'xgb_raw_home_edge'
        away_edge_col = 'xgb_raw_away_edge'
    else:  # regressed
        home_edge_col = 'xgb_regressed_home_edge'
        away_edge_col = 'xgb_regressed_away_edge'
    
    for _, row in df.iterrows():
        home_edge = row[home_edge_col]
        away_edge = row[away_edge_col]
        home_is_fav = row['home_is_favorite']
        
        # Determine thresholds based on favorite/underdog status
        home_threshold = favorite_threshold if home_is_fav else underdog_threshold
        away_threshold = underdog_threshold if home_is_fav else favorite_threshold
        
        # Check if we pick home
        if home_edge >= home_threshold:
            win = row['home_win'] == 1
            profit = calculate_profit(row['home_odds'], win)
            picks.append({
                'date': row['date'],
                'pick': row['home_team'],
                'opponent': row['away_team'],
                'is_favorite': home_is_fav,
                'is_home': True,
                'edge': home_edge,
                'odds': row['home_odds'],
                'win': win,
                'profit': profit
            })
        
        # Check if we pick away
        if away_edge >= away_threshold:
            win = row['home_win'] == 0
            profit = calculate_profit(row['away_odds'], win)
            picks.append({
                'date': row['date'],
                'pick': row['away_team'],
                'opponent': row['home_team'],
                'is_favorite': not home_is_fav,
                'is_home': False,
                'edge': away_edge,
                'odds': row['away_odds'],
                'win': win,
                'profit': profit
            })
    
    if len(picks) == 0:
        return None
    
    picks_df = pd.DataFrame(picks)
    
    results = {
        'total_picks': len(picks_df),
        'wins': picks_df['win'].sum(),
        'losses': len(picks_df) - picks_df['win'].sum(),
        'win_rate': picks_df['win'].mean() * 100,
        'total_profit': picks_df['profit'].sum(),
        'roi': picks_df['profit'].sum() / len(picks_df) * 100,
        'favorite_picks': picks_df['is_favorite'].sum(),
        'underdog_picks': (~picks_df['is_favorite']).sum(),
        'favorite_wins': picks_df[picks_df['is_favorite']]['win'].sum(),
        'underdog_wins': picks_df[~picks_df['is_favorite']]['win'].sum(),
        'favorite_profit': picks_df[picks_df['is_favorite']]['profit'].sum(),
        'underdog_profit': picks_df[~picks_df['is_favorite']]['profit'].sum(),
    }
    
    return results

# Test three asymmetric strategies
strategies = [
    (0.5, 1.5, "0.5% Favorite / 1.5% Underdog"),
    (0.5, 2.0, "0.5% Favorite / 2.0% Underdog"),
    (0.5, 3.0, "0.5% Favorite / 3.0% Underdog"),
]

print("="*80)
print("RAW PREDICTIONS")
print("="*80)
print()
print("Strategy: Lower threshold for FAVORITES, Higher threshold for UNDERDOGS")
print()

print(f"{'Strategy':<30} {'Picks':<8} {'Record':<12} {'Win%':<8} {'Profit':<10} {'ROI':<8} {'Fav/Dog Split':<15}")
print("-" * 105)

for favorite_thresh, underdog_thresh, label in strategies:
    results = test_asymmetric_strategy(df_with_results, favorite_thresh, underdog_thresh, 'raw')
    
    if results:
        fav_dog_split = f"{int(results['favorite_picks'])}/{int(results['underdog_picks'])}"
        print(f"{label:<30} {results['total_picks']:<8} "
              f"{int(results['wins'])}-{int(results['losses']):<11} "
              f"{results['win_rate']:<7.1f}% {results['total_profit']:<+9.2f} "
              f"{results['roi']:<7.1f}% {fav_dog_split:<15}")

print()
print("Detailed Breakdown by Strategy (RAW):")
print("="*80)

for favorite_thresh, underdog_thresh, label in strategies:
    results = test_asymmetric_strategy(df_with_results, favorite_thresh, underdog_thresh, 'raw')
    
    if results:
        print(f"\n{label}:")
        print(f"  Overall: {results['total_picks']} picks, {int(results['wins'])}-{int(results['losses'])} "
              f"({results['win_rate']:.1f}%), {results['total_profit']:+.2f}u, {results['roi']:.1f}% ROI")
        
        # Favorites breakdown
        fav_picks = int(results['favorite_picks'])
        if fav_picks > 0:
            fav_wins = int(results['favorite_wins'])
            fav_losses = fav_picks - fav_wins
            fav_wr = fav_wins / fav_picks * 100
            fav_profit = results['favorite_profit']
            fav_roi = fav_profit / fav_picks * 100
            print(f"    Favorites: {fav_picks} picks, {fav_wins}-{fav_losses} ({fav_wr:.1f}%), "
                  f"{fav_profit:+.2f}u, {fav_roi:.1f}% ROI")
        
        # Underdogs breakdown
        dog_picks = int(results['underdog_picks'])
        if dog_picks > 0:
            dog_wins = int(results['underdog_wins'])
            dog_losses = dog_picks - dog_wins
            dog_wr = dog_wins / dog_picks * 100
            dog_profit = results['underdog_profit']
            dog_roi = dog_profit / dog_picks * 100
            print(f"    Underdogs: {dog_picks} picks, {dog_wins}-{dog_losses} ({dog_wr:.1f}%), "
                  f"{dog_profit:+.2f}u, {dog_roi:.1f}% ROI")

print()
print()
print("="*80)
print("REGRESSED PREDICTIONS")
print("="*80)
print()
print("Strategy: Lower threshold for FAVORITES, Higher threshold for UNDERDOGS")
print()

print(f"{'Strategy':<30} {'Picks':<8} {'Record':<12} {'Win%':<8} {'Profit':<10} {'ROI':<8} {'Fav/Dog Split':<15}")
print("-" * 105)

for favorite_thresh, underdog_thresh, label in strategies:
    results = test_asymmetric_strategy(df_with_results, favorite_thresh, underdog_thresh, 'regressed')
    
    if results:
        fav_dog_split = f"{int(results['favorite_picks'])}/{int(results['underdog_picks'])}"
        print(f"{label:<30} {results['total_picks']:<8} "
              f"{int(results['wins'])}-{int(results['losses']):<11} "
              f"{results['win_rate']:<7.1f}% {results['total_profit']:<+9.2f} "
              f"{results['roi']:<7.1f}% {fav_dog_split:<15}")

print()
print("Detailed Breakdown by Strategy (REGRESSED):")
print("="*80)

for favorite_thresh, underdog_thresh, label in strategies:
    results = test_asymmetric_strategy(df_with_results, favorite_thresh, underdog_thresh, 'regressed')
    
    if results:
        print(f"\n{label}:")
        print(f"  Overall: {results['total_picks']} picks, {int(results['wins'])}-{int(results['losses'])} "
              f"({results['win_rate']:.1f}%), {results['total_profit']:+.2f}u, {results['roi']:.1f}% ROI")
        
        # Favorites breakdown
        fav_picks = int(results['favorite_picks'])
        if fav_picks > 0:
            fav_wins = int(results['favorite_wins'])
            fav_losses = fav_picks - fav_wins
            fav_wr = fav_wins / fav_picks * 100
            fav_profit = results['favorite_profit']
            fav_roi = fav_profit / fav_picks * 100
            print(f"    Favorites: {fav_picks} picks, {fav_wins}-{fav_losses} ({fav_wr:.1f}%), "
                  f"{fav_profit:+.2f}u, {fav_roi:.1f}% ROI")
        
        # Underdogs breakdown
        dog_picks = int(results['underdog_picks'])
        if dog_picks > 0:
            dog_wins = int(results['underdog_wins'])
            dog_losses = dog_picks - dog_wins
            dog_wr = dog_wins / dog_picks * 100
            dog_profit = results['underdog_profit']
            dog_roi = dog_profit / dog_picks * 100
            print(f"    Underdogs: {dog_picks} picks, {dog_wins}-{dog_losses} ({dog_wr:.1f}%), "
                  f"{dog_profit:+.2f}u, {dog_roi:.1f}% ROI")

print()
print("="*80)
print("ANALYSIS COMPLETE")
print("="*80)
