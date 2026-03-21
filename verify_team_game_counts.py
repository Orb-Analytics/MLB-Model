#!/usr/bin/env python3
"""
Verify that each team appears exactly 162 times in the dataset
(counting both home and away games)
"""

import pandas as pd

print("="*80)
print("VERIFYING EACH TEAM HAS 162 GAMES")
print("="*80)

# Load the data (we'll use boxscores as it has the game info)
df = pd.read_csv('data/bdl_data/boxscores.csv')
print(f"\nLoaded: {len(df)} games")

# Get home and away team columns
home_col = None
away_col = None

for col in df.columns:
    if 'home' in col.lower() and 'team' in col.lower() and 'id' in col.lower():
        home_col = col
    if 'away' in col.lower() and 'team' in col.lower() and 'id' in col.lower():
        away_col = col

if not home_col or not away_col:
    print("\nSearching for team ID columns...")
    print(f"Columns: {df.columns.tolist()}")
    # Try alternate names
    for col in df.columns:
        print(f"  {col}")
else:
    print(f"\nHome team column: {home_col}")
    print(f"Away team column: {away_col}")
    
    # Count games per team
    home_counts = df[home_col].value_counts().sort_index()
    away_counts = df[away_col].value_counts().sort_index()
    
    # Get all unique team IDs
    all_teams = sorted(set(home_counts.index) | set(away_counts.index))
    
    print(f"\nTotal unique teams: {len(all_teams)}")
    print("\n" + "="*80)
    print("GAME COUNT PER TEAM")
    print("="*80)
    print(f"{'Team ID':<10} {'Home Games':<12} {'Away Games':<12} {'Total':<10} {'Status'}")
    print("-"*80)
    
    issues = []
    
    for team_id in all_teams:
        home_games = home_counts.get(team_id, 0)
        away_games = away_counts.get(team_id, 0)
        total_games = home_games + away_games
        
        status = "✓" if total_games == 162 else "❌"
        
        if total_games != 162:
            issues.append({
                'team_id': team_id,
                'home': home_games,
                'away': away_games,
                'total': total_games,
                'difference': total_games - 162
            })
        
        print(f"{team_id:<10} {home_games:<12} {away_games:<12} {total_games:<10} {status}")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if not issues:
        print("\n✓✓✓ PERFECT! All 30 teams have exactly 162 games! ✓✓✓")
    else:
        print(f"\n❌ Found {len(issues)} teams with incorrect game counts:\n")
        for issue in issues:
            print(f"Team {issue['team_id']}:")
            print(f"  Home: {issue['home']}, Away: {issue['away']}")
            print(f"  Total: {issue['total']} (expected 162, difference: {issue['difference']:+d})")
            print()
    
    # Additional stats
    print("\n" + "="*80)
    print("OVERALL STATISTICS")
    print("="*80)
    print(f"Total games in dataset: {len(df)}")
    print(f"Expected total (30 teams × 162 games ÷ 2): {30 * 162 // 2}")
    print(f"Total team-games (counting each team per game): {len(df) * 2}")
    print(f"Expected team-games (30 teams × 162): {30 * 162}")
    
    if len(df) == 30 * 162 // 2:
        print("\n✓ Correct total number of games")
    else:
        print(f"\n❌ Game count mismatch: {len(df)} vs {30 * 162 // 2}")

print("\n" + "="*80)
