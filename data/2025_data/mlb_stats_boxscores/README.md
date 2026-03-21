# MLB Box Scores - March 2025

## Overview
Complete team box score data for all regular season MLB games from March 2025, fetched from the official MLB Stats API.

## Data Summary
- **Total Games:** 67
- **Date Range:** March 18 - March 31, 2025
- **Teams:** All 30 MLB teams
- **Success Rate:** 100%

## Files Created

### Master CSV
- **File:** `march_2025_master.csv`
- **Size:** 20KB
- **Rows:** 67 games
- **Columns:** 85 statistics per game

### Individual Game Files
- **Directory:** `march_2025/`
- **Format:** `game_<game_pk>.csv`
- **Count:** 67 files (one per game)
- **Example:** `game_778563.csv` (LAD @ CHC on 2025-03-18)

## Column Categories

### Game Information (5 columns)
- `game_pk` - MLB game ID
- `date` - Game date (YYYY-MM-DD)
- `venue` - Stadium name
- `away_team` - Away team name
- `home_team` - Home team name

### Batting Statistics (21 columns per team = 42 total)
**Away team:** `away_*` | **Home team:** `home_*`
- Runs, Hits, Doubles, Triples, Home Runs
- RBI, Walks, Strikeouts
- Stolen Bases, Caught Stealing, Hit By Pitch
- At Bats, OBP, SLG, OPS, AVG
- Left On Base, Sac Bunts, Sac Flies
- Ground Into Double Play, Total Bases

### Pitching Statistics (13 columns per team = 26 total)
**Away team:** `away_*` | **Home team:** `home_*`
- Innings Pitched, Earned Runs
- Strikeouts, Walks, Hits, Home Runs
- ERA, WHIP
- Hit Batters, Wild Pitches, Balks
- Pitches Thrown, Strikes

### Fielding Statistics (6 columns per team = 12 total)
**Away team:** `away_*` | **Home team:** `home_*`
- Errors, Putouts, Assists
- Chances, Passed Balls, Double Plays

## Sample Statistics (March 2025)

### Overall Stats
- **Runs per game:** 8.9
- **Hits per game:** 15.7
- **Home runs per game:** 2.5
- **Errors per game:** 0.9

### Top 5 Highest Scoring Games
1. **Mar 29:** MIL 9 @ NYY 20 (29 total runs)
2. **Mar 31:** CHC 18 @ OAK 3 (21 total runs)
3. **Mar 29:** PHI 11 @ WSH 6 (17 total runs)
4. **Mar 31:** TEX 3 @ CIN 14 (17 total runs)
5. **Mar 27:** CHC 10 @ ARI 6 (16 total runs)

## Data Source
**API:** MLB Stats API (https://statsapi.mlb.com)
- **Schedule Endpoint:** `/api/v1/schedule?sportId=1&date=YYYY-MM-DD`
- **Boxscore Endpoint:** `/api/v1/game/{game_pk}/boxscore`

## Features
✅ **Complete** - All 85 team-level statistics  
✅ **Official** - Direct from MLB's authoritative API  
✅ **Free** - No API key required  
✅ **Reliable** - 100% fetch success rate  
✅ **Structured** - CSV format ready for analysis  

## Usage Examples

### Load Master CSV
```python
import pandas as pd

# Load all March games
df = pd.read_csv('march_2025_master.csv')

# Filter by team
dodgers_games = df[(df['away_team'] == 'Los Angeles Dodgers') | (df['home_team'] == 'Los Angeles Dodgers')]

# Calculate total runs by team
team_runs = {}
for _, row in df.iterrows():
    team_runs[row['away_team']] = team_runs.get(row['away_team'], 0) + row['away_runs']
    team_runs[row['home_team']] = team_runs.get(row['home_team'], 0) + row['home_runs']
```

### Load Individual Game
```python
# Load specific game (LAD @ CHC on 3/18)
game = pd.read_csv('march_2025/game_778563.csv')
print(f"Score: {game['away_runs'][0]}-{game['home_runs'][0]}")
```

## Next Steps

### Expand to Full Season
To fetch April-September 2025 games:
1. Modify `START_DATE` and `END_DATE` in `fetch_march_2025_boxscores.py`
2. Update `OUTPUT_DIR` to `april_2025`, `may_2025`, etc.
3. Run script for each month

### Combine with Other Data
This box score data can be joined with:
- Starting pitcher data
- Team standings
- Betting odds
- Weather data

### Analysis Ideas
- Team performance trends over season
- Home/away splits
- Batting/pitching correlations
- Win probability models
- Run differential analysis

## Script Used
**File:** `fetch_march_2025_boxscores.py`
- Loops through all dates in March 2025
- Fetches gameIDs from schedule endpoint
- Fetches boxscore for each game
- Extracts 85 team statistics
- Saves individual CSVs + master CSV
- Includes error handling and progress tracking

## Validation
✅ All 67 games successfully fetched  
✅ Data matches official MLB box scores  
✅ All statistics present (no missing values)  
✅ Validated against test game (778563) from previous exploration  

---

**Created:** March 9, 2026  
**Data Period:** March 18-31, 2025  
**API Version:** MLB Stats API v1  
