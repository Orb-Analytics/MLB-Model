"""
Analyze the 0.5% Underdog / 1.5% Favorite strategy
Shows picking tendencies: fav/dog and home/away
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

print("="*80)
print("REGRESSED XGBOOST: 1.5% UNDERDOG / 0.5% FAVORITE STRATEGY")
print("="*80)
print()

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

df['home_win'] = (df['home_runs_scored'] > df['away_runs_scored']).astype(float)
df = df[df['home_win'].notna()].copy()

# Calculate probabilities and edges
df['market_home_prob'] = df['home_odds'].apply(odds_to_prob)
df['market_away_prob'] = df['away_odds'].apply(odds_to_prob)

df['xgb_regressed_home_prob'] = 0.65 * df['market_home_prob'] + 0.35 * df['xgb_home_prob']
df['xgb_regressed_away_prob'] = 0.65 * df['market_away_prob'] + 0.35 * (1 - df['xgb_home_prob'])

df['xgb_regressed_home_edge'] = (df['xgb_regressed_home_prob'] - df['market_home_prob']) * 100
df['xgb_regressed_away_edge'] = (df['xgb_regressed_away_prob'] - df['market_away_prob']) * 100

df['home_is_favorite'] = df['home_odds'] < df['away_odds']

print(f"Total games analyzed: {len(df)}")
print()

# =============================================================================
# APPLY STRATEGY: 1.5% UNDERDOG / 0.5% FAVORITE
# =============================================================================

underdog_threshold = 1.5
favorite_threshold = 0.5

picks = []

for _, row in df.iterrows():
    home_edge = row['xgb_regressed_home_edge']
    away_edge = row['xgb_regressed_away_edge']
    home_is_fav = row['home_is_favorite']
    
    # Determine thresholds
    home_threshold = favorite_threshold if home_is_fav else underdog_threshold
    away_threshold = underdog_threshold if home_is_fav else favorite_threshold
    
    # Check if we pick home
    if home_edge >= home_threshold:
        win = row['home_win'] == 1
        profit = calculate_profit(row['home_odds'], win)
        picks.append({
            'team': row['home_team'],
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
            'team': row['away_team'],
            'opponent': row['home_team'],
            'is_favorite': not home_is_fav,
            'is_home': False,
            'edge': away_edge,
            'odds': row['away_odds'],
            'win': win,
            'profit': profit
        })

if len(picks) == 0:
    print("No picks made with this strategy!")
    exit()

picks_df = pd.DataFrame(picks)

# =============================================================================
# OVERALL RESULTS
# =============================================================================

print("="*80)
print("OVERALL PERFORMANCE")
print("="*80)
print()

total_picks = len(picks_df)
wins = picks_df['win'].sum()
losses = total_picks - wins
win_rate = wins / total_picks * 100
total_profit = picks_df['profit'].sum()
roi = total_profit / total_picks * 100

print(f"Total Picks: {total_picks}")
print(f"Record: {int(wins)}-{int(losses)} ({win_rate:.1f}%)")
print(f"Profit: {total_profit:+.2f} units")
print(f"ROI: {roi:.1f}%")
print()

# =============================================================================
# FAVORITE vs UNDERDOG BREAKDOWN
# =============================================================================

print("="*80)
print("FAVORITE vs UNDERDOG BREAKDOWN")
print("="*80)
print()

fav_picks = picks_df[picks_df['is_favorite']]
dog_picks = picks_df[~picks_df['is_favorite']]

fav_count = len(fav_picks)
dog_count = len(dog_picks)
fav_pct = fav_count / total_picks * 100
dog_pct = dog_count / total_picks * 100

print(f"Favorites:  {fav_count:3d} picks ({fav_pct:.1f}%)")
print(f"            {int(fav_picks['win'].sum())}-{fav_count - int(fav_picks['win'].sum())} record")
print(f"            {fav_picks['win'].mean()*100:.1f}% win rate")
print(f"            {fav_picks['profit'].sum():+.2f} units profit")
print(f"            {fav_picks['profit'].sum()/fav_count*100:.1f}% ROI")
print()

print(f"Underdogs:  {dog_count:3d} picks ({dog_pct:.1f}%)")
print(f"            {int(dog_picks['win'].sum())}-{dog_count - int(dog_picks['win'].sum())} record")
print(f"            {dog_picks['win'].mean()*100:.1f}% win rate")
print(f"            {dog_picks['profit'].sum():+.2f} units profit")
print(f"            {dog_picks['profit'].sum()/dog_count*100:.1f}% ROI")
print()

if dog_pct > fav_pct:
    diff = dog_pct - fav_pct
    print(f"🐕 LEANS UNDERDOG by {diff:.1f} percentage points")
else:
    diff = fav_pct - dog_pct
    print(f"⭐ LEANS FAVORITE by {diff:.1f} percentage points")
print()

# =============================================================================
# HOME vs AWAY BREAKDOWN
# =============================================================================

print("="*80)
print("HOME vs AWAY BREAKDOWN")
print("="*80)
print()

home_picks = picks_df[picks_df['is_home']]
away_picks = picks_df[~picks_df['is_home']]

home_count = len(home_picks)
away_count = len(away_picks)
home_pct = home_count / total_picks * 100
away_pct = away_count / total_picks * 100

print(f"Home Picks: {home_count:3d} picks ({home_pct:.1f}%)")
print(f"            {int(home_picks['win'].sum())}-{home_count - int(home_picks['win'].sum())} record")
print(f"            {home_picks['win'].mean()*100:.1f}% win rate")
print(f"            {home_picks['profit'].sum():+.2f} units profit")
print(f"            {home_picks['profit'].sum()/home_count*100:.1f}% ROI")
print()

print(f"Away Picks: {away_count:3d} picks ({away_pct:.1f}%)")
print(f"            {int(away_picks['win'].sum())}-{away_count - int(away_picks['win'].sum())} record")
print(f"            {away_picks['win'].mean()*100:.1f}% win rate")
print(f"            {away_picks['profit'].sum():+.2f} units profit")
print(f"            {away_picks['profit'].sum()/away_count*100:.1f}% ROI")
print()

if home_pct > away_pct:
    diff = home_pct - away_pct
    print(f"🏠 LEANS HOME by {diff:.1f} percentage points")
else:
    diff = away_pct - home_pct
    print(f"✈️  LEANS AWAY by {diff:.1f} percentage points")
print()

# =============================================================================
# QUADRANT ANALYSIS
# =============================================================================

print("="*80)
print("QUADRANT ANALYSIS (Favorite/Underdog × Home/Away)")
print("="*80)
print()

print(f"{'Category':<25} {'Picks':<8} {'Record':<12} {'Win%':<8} {'Profit':<10} {'ROI':<8}")
print("-" * 80)

# Favorite Home
fav_home = picks_df[(picks_df['is_favorite']) & (picks_df['is_home'])]
if len(fav_home) > 0:
    print(f"{'Favorite Home':<25} {len(fav_home):<8} "
          f"{int(fav_home['win'].sum())}-{len(fav_home)-int(fav_home['win'].sum()):<11} "
          f"{fav_home['win'].mean()*100:<7.1f}% {fav_home['profit'].sum():<+9.2f} "
          f"{fav_home['profit'].sum()/len(fav_home)*100:<7.1f}%")

# Favorite Away
fav_away = picks_df[(picks_df['is_favorite']) & (~picks_df['is_home'])]
if len(fav_away) > 0:
    print(f"{'Favorite Away':<25} {len(fav_away):<8} "
          f"{int(fav_away['win'].sum())}-{len(fav_away)-int(fav_away['win'].sum()):<11} "
          f"{fav_away['win'].mean()*100:<7.1f}% {fav_away['profit'].sum():<+9.2f} "
          f"{fav_away['profit'].sum()/len(fav_away)*100:<7.1f}%")

# Underdog Home
dog_home = picks_df[(~picks_df['is_favorite']) & (picks_df['is_home'])]
if len(dog_home) > 0:
    print(f"{'Underdog Home':<25} {len(dog_home):<8} "
          f"{int(dog_home['win'].sum())}-{len(dog_home)-int(dog_home['win'].sum()):<11} "
          f"{dog_home['win'].mean()*100:<7.1f}% {dog_home['profit'].sum():<+9.2f} "
          f"{dog_home['profit'].sum()/len(dog_home)*100:<7.1f}%")

# Underdog Away
dog_away = picks_df[(~picks_df['is_favorite']) & (~picks_df['is_home'])]
if len(dog_away) > 0:
    print(f"{'Underdog Away':<25} {len(dog_away):<8} "
          f"{int(dog_away['win'].sum())}-{len(dog_away)-int(dog_away['win'].sum()):<11} "
          f"{dog_away['win'].mean()*100:<7.1f}% {dog_away['profit'].sum():<+9.2f} "
          f"{dog_away['profit'].sum()/len(dog_away)*100:<7.1f}%")

print()
print("="*80)
print("SUMMARY")
print("="*80)
print(f"Strategy: Be LIBERAL on favorites (0.5% threshold)")
print(f"          Be SELECTIVE on underdogs (1.5% threshold)")
print()
print(f"Result: Picks {dog_pct:.1f}% UNDERDOGS, {fav_pct:.1f}% FAVORITES")
print(f"        Picks {home_pct:.1f}% HOME, {away_pct:.1f}% AWAY")
print()
