import pandas as pd
import glob

def check_team_game_counts(year):
    """Check which teams played fewer than expected games."""
    
    print(f"\n{'='*80}")
    print(f"Team Game Counts for {year}")
    print('='*80)
    
    # Load all boxscores
    boxscore_files = glob.glob(f'data/{year}_data/mlb_data/raw/boxscores/*.csv')
    boxscore_dfs = [pd.read_csv(f) for f in boxscore_files]
    boxscores = pd.concat(boxscore_dfs, ignore_index=True)
    
    # Count games per team (both home and away)
    away_counts = boxscores['away_team_abbreviation'].value_counts()
    home_counts = boxscores['home_team_abbreviation'].value_counts()
    total_counts = (away_counts.add(home_counts, fill_value=0)).astype(int).sort_index()
    
    expected = 162 if year != 2020 else 60
    
    print(f"\nExpected games per team: {expected}")
    print(f"\nTeam | Games | Difference")
    print("-" * 40)
    
    teams_with_issues = []
    for team in sorted(total_counts.index):
        count = total_counts[team]
        diff = count - expected
        status = "✅" if diff == 0 else "⚠️"
        diff_str = f"{diff:+d}" if diff != 0 else " 0"
        print(f"{team:4} | {count:3} | {diff_str:>4} {status}")
        
        if diff != 0:
            teams_with_issues.append((team, count, diff))
    
    if teams_with_issues:
        print(f"\n⚠️ Teams with missing/extra games:")
        for team, count, diff in teams_with_issues:
            print(f"  {team}: {count} games ({diff:+d})")
    else:
        print(f"\n✅ All teams played {expected} games")
    
    return teams_with_issues

if __name__ == "__main__":
    years = [2016, 2019, 2020]
    
    all_issues = {}
    for year in years:
        issues = check_team_game_counts(year)
        if issues:
            all_issues[year] = issues
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    
    if all_issues:
        for year, issues in all_issues.items():
            print(f"\n{year}:")
            for team, count, diff in issues:
                print(f"  {team}: {count} games ({diff:+d})")
    else:
        print("All teams played the expected number of games")
