# MLB Box Scores - March 2025 (By Date)

## Overview
Complete MLB regular season box scores for March 2025, organized by date with standardized schema.

**Output Location:** `/workspaces/MLB-Model/data/bdl_data/boxscores/`

## Summary Statistics
- **Total Games:** 67
- **Date Range:** March 18 - March 31, 2025
- **Files Created:** 7 (one per date)
- **Schema Columns:** 72
- **Success Rate:** 100%

## Files Created

| Date | Games | File |
|------|-------|------|
| 2025-03-18 | 1 | `boxscores_2025-03-18.csv` |
| 2025-03-19 | 1 | `boxscores_2025-03-19.csv` |
| 2025-03-27 | 14 | `boxscores_2025-03-27.csv` |
| 2025-03-28 | 9 | `boxscores_2025-03-28.csv` |
| 2025-03-29 | 15 | `boxscores_2025-03-29.csv` |
| 2025-03-30 | 13 | `boxscores_2025-03-30.csv` |
| 2025-03-31 | 14 | `boxscores_2025-03-31.csv` |

## Schema Details

### Complete Column List (72 columns)

#### Game Identifiers (2)
1. `id` - MLB game_pk identifier
2. `date` - Game date (YYYY-MM-DD)

#### Team Information (8)
3. `home_team_id` - MLB team ID
4. `away_team_id` - MLB team ID
5. `home_team_abbreviation` - Team abbreviation (e.g., LAD, CHC)
6. `away_team_abbreviation` - Team abbreviation
7. `home_team_display_name` - Full team name (e.g., Los Angeles Dodgers)
8. `away_team_display_name` - Full team name
9. `home_team_name` - Short team name (e.g., Dodgers)
10. `away_team_name` - Short team name

#### Season Information (8)
11. `home_postseason` - Postseason flag (0 for regular season)
12. `away_postseason` - Postseason flag
13. `home_season_type` - Season type (regular/postseason)
14. `away_season_type` - Season type
15. `home_season` - Season year (2025)
16. `away_season` - Season year
17. `home_gp` - Games played (cumulative)
18. `away_gp` - Games played (cumulative)

#### Batting Statistics (30)
Home team (`home_batting_*`) and Away team (`away_batting_*`):
- 19-20. `ab` - At bats
- 21-22. `r` - Runs
- 23-24. `h` - Hits
- 25-26. `2b` - Doubles
- 27-28. `3b` - Triples
- 29-30. `hr` - Home runs
- 31-32. `rbi` - Runs batted in
- 33-34. `tb` - Total bases
- 35-36. `bb` - Walks (base on balls)
- 37-38. `so` - Strikeouts
- 39-40. `sb` - Stolen bases
- 41-42. `avg` - Batting average
- 43-44. `obp` - On-base percentage
- 45-46. `slg` - Slugging percentage
- 47-48. `ops` - On-base plus slugging

#### Pitching Statistics (22)
Home team (`home_pitching_*`) and Away team (`away_pitching_*`):
- 49-50. `w` - Wins (1 for winner, 0 for loser)
- 51-52. `l` - Losses (1 for loser, 0 for winner)
- 53-54. `era` - Earned run average
- 55-56. `ip` - Innings pitched
- 57-58. `h` - Hits allowed
- 59-60. `er` - Earned runs
- 61-62. `hr` - Home runs allowed
- 63-64. `bb` - Walks allowed
- 65-66. `k` - Strikeouts
- 67-68. `oba` - Opponent batting average
- 69-70. `whip` - Walks plus hits per inning pitched

#### Fielding Statistics (2)
- 71. `home_fielding_e` - Errors
- 72. `away_fielding_e` - Errors

## Sample Data

### First Game (March 18, 2025)
```
Game ID: 778563
Date: 2025-03-18
Away: Los Angeles Dodgers (LAD) - ID: 119
Home: Chicago Cubs (CHC) - ID: 112
Score: 4-1

Away Batting: AB=34, R=4, H=7, 2B=2, HR=0, RBI=3, BB=8, SO=9, SB=0, AVG=.206
Home Batting: AB=30, R=1, H=3, 2B=1, HR=0, RBI=1, BB=1, SO=9, SB=1, AVG=.100

Away Pitching: W=1, L=0, ERA=1.00, IP=9.0, H=3, ER=1, BB=1, K=9, OBA=.100, WHIP=0.44
Home Pitching: W=0, L=1, ERA=3.00, IP=9.0, H=7, ER=3, BB=8, K=9, OBA=.205, WHIP=1.67

Fielding: Away E=0, Home E=2
```

## Data Source & Methodology

### MLB Stats API
- **Teams Endpoint:** `https://statsapi.mlb.com/api/v1/teams?sportId=1&season=2025`
  - Fetches team IDs, abbreviations, and names
- **Schedule Endpoint:** `https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=YYYY-MM-DD`
  - Finds games by date (filters for regular season only)
- **Boxscore Endpoint:** `https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore`
  - Retrieves complete team-level statistics

### Calculated Fields
- **Games Played (gp):** Incremented for each team as games are processed chronologically
- **Wins/Losses (w/l):** Derived from final score (1 for winner, 0 for loser)
- **Opponent Batting Average (oba):** Calculated as hits allowed / at bats faced

### Data Organization
- Files organized by date: `boxscores_YYYY-MM-DD.csv`
- Each file contains all games played on that date
- Multi-game dates have multiple rows (one per game)

## Usage Examples

### Load All March Games
```python
import pandas as pd
import glob

# Load all March box score files
files = glob.glob('data/bdl_data/boxscores/boxscores_2025-03-*.csv')
df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)

print(f"Total games: {len(df)}")
```

### Load Specific Date
```python
import pandas as pd

# Load Opening Day games
df = pd.read_csv('data/bdl_data/boxscores/boxscores_2025-03-27.csv')
print(f"Opening Day: {len(df)} games")
```

### Filter by Team
```python
import pandas as pd

df = pd.read_csv('data/bdl_data/boxscores/boxscores_2025-03-27.csv')

# Get Dodgers games
dodgers = df[(df['away_team_abbreviation'] == 'LAD') | 
             (df['home_team_abbreviation'] == 'LAD')]
```

### Calculate Team Statistics
```python
import pandas as pd
import glob

files = glob.glob('data/bdl_data/boxscores/boxscores_2025-03-*.csv')
df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)

# Calculate total runs per team
team_runs = {}
for _, row in df.iterrows():
    team_runs[row['away_team_abbreviation']] = team_runs.get(row['away_team_abbreviation'], 0) + row['away_batting_r']
    team_runs[row['home_team_abbreviation']] = team_runs.get(row['home_team_abbreviation'], 0) + row['home_batting_r']

# Sort by runs scored
sorted_teams = sorted(team_runs.items(), key=lambda x: x[1], reverse=True)
print("Top 5 Scoring Teams:")
for team, runs in sorted_teams[:5]:
    print(f"{team}: {runs} runs")
```

## Data Quality Notes

### Validation ✅
- All 67 games successfully fetched (100% success rate)
- All 72 required columns present in every file
- Team IDs and abbreviations verified against MLB API
- Games played (gp) counter working correctly
- Win/loss records calculated accurately

### Known Characteristics
- **Games Played Counter:** Increments chronologically, so teams that played in Tokyo (LAD, CHC) on March 18-19 show gp=3 on Opening Day (March 27) while other teams show gp=1
- **Pitching ERA/WHIP:** Season-to-date values from MLB API
- **Opponent Batting Average (oba):** Calculated per game as hits allowed / at bats faced
- **Season Type:** All games marked as "regular" (postseason=0)

## Next Steps

### Expand Dataset
To fetch the full 2025 regular season:
1. Update date range in `fetch_boxscores_by_date.py`
2. Process April through September
3. Combine all months into complete season dataset

### Integration Opportunities
This data can be combined with:
- Starting pitcher information
- Team standings/records
- Betting odds from Novig API
- Weather/venue data
- Historical performance metrics

### Analysis Ideas
- Team performance trends over time
- Home/away splits
- Pythagorean win expectancy
- Run differential analysis
- Pitching vs batting correlations
- Win probability models

## Script Information
**Script:** `fetch_boxscores_by_date.py`
- Fetches team information once at start
- Processes dates sequentially
- Tracks cumulative games played per team
- Organizes output by date
- Includes error handling and progress tracking
- Adds 0.5s delay between API calls

## Metadata
- **Created:** March 9, 2026
- **Data Period:** March 18-31, 2025
- **Games:** 67 regular season games
- **Teams:** All 30 MLB teams
- **API:** MLB Stats API v1
- **Schema Version:** 1.0 (72 columns)
