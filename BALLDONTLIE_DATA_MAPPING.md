# Balldontlie API to Training Set Data Mapping

## Overview
This document maps the Balldontlie.io MLB API data structure to the current training set schema. Use this as a reference when building ETL scripts to replace the current data sources.

---

## Current Training Set Structure

The training set consists of 4 main data components merged horizontally:

1. **Matchups** - Game information, betting lines, scores
2. **Starting Pitchers** - Starting pitcher stats + bullpen stats
3. **Team Pitching** - Team-level pitching statistics
4. **Team Batting** - Team-level batting statistics

All data is organized with **favorite/underdog perspective** (not home/away), though home/away fields are also included.

---

## 1. MATCHUPS DATA

### Current Schema (18 fields)
```
Date, Fav Team, Dog Team, Away, Home, Fav Home?, Spread, Fav Spread Odds, 
Dog Spread Odds, Fav Score, Dog Score, Fav/Dog +/-, Fav Cover?, Fav Win?, 
Away Spread Odds, Home Spread Odds, Away Score, Home Score, Home/Away +/-
```

### Balldontlie API Sources

#### Primary: `/mlb/v1/games` endpoint
```json
{
  "id": 21383,
  "home_team_name": "San Diego Padres",
  "away_team_name": "Pittsburgh Pirates",
  "home_team": {"id": 23, "abbreviation": "SD", ...},
  "away_team": {"id": 22, "abbreviation": "PIT", ...},
  "season": 2025,
  "date": "2025-06-01T01:40:00.000Z",
  "home_team_data": {"hits": 2, "runs": 0, "errors": 0},
  "away_team_data": {"hits": 12, "runs": 5, "errors": 0},
  "status": "STATUS_FINAL"
}
```

#### Secondary: `/mlb/v1/odds` endpoint (for betting lines)
```json
{
  "game_id": 21383,
  "home_team": {...},
  "away_team": {...},
  "bookmakers": [
    {
      "key": "draftkings",
      "markets": [
        {
          "key": "spreads",
          "outcomes": [
            {"name": "San Diego Padres", "price": -110, "point": -1.5},
            {"name": "Pittsburgh Pirates", "price": -110, "point": 1.5}
          ]
        }
      ]
    }
  ]
}
```

### Mapping Logic

| Current Field | Balldontlie Source | Transformation Logic |
|--------------|-------------------|---------------------|
| `Date` | `games.date` | Convert ISO timestamp to YYYY-MM-DD |
| `Fav Team` | `odds` + `games` | Determine favorite from odds (smaller spread point) |
| `Dog Team` | `odds` + `games` | Determine underdog from odds (larger spread point) |
| `Away` | `games.away_team.abbreviation` | Direct mapping |
| `Home` | `games.home_team.abbreviation` | Direct mapping |
| `Fav Home?` | *Derived* | `1` if Fav Team == Home, else `0` |
| `Spread` | `odds.markets[spreads].outcomes[favorite].point` | Absolute value of spread |
| `Fav Spread Odds` | `odds.markets[spreads].outcomes[favorite].price` | Convert decimal to American if needed |
| `Dog Spread Odds` | `odds.markets[spreads].outcomes[underdog].price` | Convert decimal to American if needed |
| `Fav Score` | `games.home_team_data.runs` or `away_team_data.runs` | Based on Fav Home? |
| `Dog Score` | `games.home_team_data.runs` or `away_team_data.runs` | Based on Fav Home? |
| `Fav/Dog +/-` | *Calculated* | `Fav Score - Dog Score` |
| `Fav Cover?` | *Calculated* | `1` if `Fav/Dog +/-` > `Spread`, else `0` |
| `Fav Win?` | *Calculated* | `1` if `Fav Score` > `Dog Score`, else `0` |
| `Away Score` | `games.away_team_data.runs` | Direct mapping |
| `Home Score` | `games.home_team_data.runs` | Direct mapping |
| `Home/Away +/-` | *Calculated* | `Home Score - Away Score` |
| `Away Spread Odds` | `odds` | Odds for away team from spreads market |
| `Home Spread Odds` | `odds` | Odds for home team from spreads market |

---

## 2. STARTING PITCHERS DATA

### Current Schema (22 fields)
```
Fav SP, Dog SP, Fav SP Era, Dog SP ERA, Fav SP WHIP, Dog SP WHIP, 
Fav SP IP, Dog SP IP, Fav SP AB/IP, Dog SP AB/IP, Fav SP SO, Dog SP SO, 
Fav SP SO/AB, Dog SP SO/AB, Fav SP AVG, Dog SP AVG, Fav SP AB, Dog SP AB,
Fav BP ERA, Dog BP ERA, Fav BP WHIP, Dog BP WHIP, Fav BP IP, Dog BP IP, 
Fav BP AB/IP, Dog BP AB/IP, Fav BP SO, Dog BP SO, Fav BP SO/AB, 
Dog BP SO/AB, Fav BP AB, Dog BP AB
```

### Balldontlie API Sources

#### Starting Pitcher: `/mlb/v1/season_stats?player_id={}&season=2025`
```json
{
  "player": {"id": 123, "full_name": "George Kirby", ...},
  "season": 2025,
  "games": 18,
  "games_started": 18,
  "pitching_era": 4.50,
  "pitching_whip": 1.15,
  "pitching_ip": 66.0,
  "pitching_ab": 247,
  "pitching_so": 68,
  "pitching_avg": 0.243,
  ...
}
```

#### Bullpen Stats: `/mlb/v1/teams/season_stats?season=2025`
```json
{
  "team": {"id": 27, "abbreviation": "SEA", ...},
  "season": 2025,
  "pitching_era": 3.85,
  "pitching_whip": 1.27,
  "pitching_ip": 920.2,
  "pitching_so": 851,
  "pitching_ab": 3482,
  ...
}
```

### Mapping Logic

**Challenge**: Balldontlie doesn't have a direct "today's starting pitchers" endpoint. Options:
1. Use `/mlb/v1/games/{id}` if it includes probable pitchers
2. Use `/mlb/v1/plays` or `/mlb/v1/plate_appearances` to identify the first pitcher
3. Maintain a separate data source for probable pitchers

| Current Field | Balldontlie Source | Notes |
|--------------|-------------------|-------|
| `Fav SP` / `Dog SP` | **TBD** - Need to identify starting pitcher | May need external source |
| `Fav/Dog SP ERA` | `season_stats.pitching_era` | Filter for starting pitcher |
| `Fav/Dog SP WHIP` | `season_stats.pitching_whip` | Direct mapping |
| `Fav/Dog SP IP` | `season_stats.pitching_ip` | Direct mapping |
| `Fav/Dog SP SO` | `season_stats.pitching_so` | Direct mapping |
| `Fav/Dog SP AVG` | `season_stats.pitching_avg` | Direct mapping |
| `Fav/Dog SP AB` | `season_stats.pitching_ab` | Direct mapping |
| `Fav/Dog SP AB/IP` | *Calculated* | `AB / IP` |
| `Fav/Dog SP SO/AB` | *Calculated* | `SO / AB` |
| `Fav/Dog BP ERA` | `teams/season_stats.pitching_era` | Subtract starter's contribution |
| `Fav/Dog BP WHIP` | `teams/season_stats.pitching_whip` | Subtract starter's contribution |
| `Fav/Dog BP IP` | `teams/season_stats.pitching_ip` | Subtract starter's IP |
| `Fav/Dog BP SO` | `teams/season_stats.pitching_so` | Subtract starter's SO |
| `Fav/Dog BP AB` | `teams/season_stats.pitching_ab` | Subtract starter's AB |
| `Fav/Dog BP AB/IP` | *Calculated* | `BP AB / BP IP` |
| `Fav/Dog BP SO/AB` | *Calculated* | `BP SO / BP AB` |

---

## 3. TEAM PITCHING DATA

### Current Schema (56 fields)
All prefixed with `Fav P` or `Dog P`:
```
runs, runs/AB, doubles, doubles/AB, triples, triples/AB, homeRuns, homeruns/AB,
strikeOuts, Strikeouts/AB, baseOnBalls, baseonballs/AB, hits, avg, atBats, obp,
slg, ops, era, inningsPitched, earnedRuns, earnedruns/AB, whip, battersFaced,
totalBases, pitchesPerInning, gamesFinished, strikeoutWalkRatio, strikeoutsPer9Inn,
walksPer9Inn, hitsPer9Inn, runsScoredPer9, homeRunsPer9
```

### Balldontlie API Source

#### `/mlb/v1/teams/season_stats?season=2025`
```json
{
  "team": {"abbreviation": "CHW", ...},
  "season": 2025,
  "pitching_w": 60,
  "pitching_l": 102,
  "pitching_era": 4.27,
  "pitching_ip": 1416,
  "pitching_h": 1337,
  "pitching_er": 672,
  "pitching_hr": 189,
  "pitching_bb": 595,
  "pitching_k": 1286,
  "pitching_oba": 0.247,
  "pitching_whip": 1.36,
  ...
}
```

### Field Mapping

| Current Field | Balldontlie Field | Calculation |
|--------------|------------------|-------------|
| `runs` | ❌ Not available | Use `pitching_er` (earned runs) as proxy |
| `runs/AB` | *Calculated* | `earnedRuns / atBats` |
| `doubles` | ❌ Not available | **GAP** |
| `triples` | ❌ Not available | **GAP** |
| `homeRuns` | `pitching_hr` | Direct mapping |
| `homeruns/AB` | *Calculated* | `pitching_hr / atBats` |
| `strikeOuts` | `pitching_k` | Direct mapping |
| `Strikeouts/AB` | *Calculated* | `pitching_k / atBats` |
| `baseOnBalls` | `pitching_bb` | Direct mapping |
| `baseonballs/AB` | *Calculated* | `pitching_bb / atBats` |
| `hits` | `pitching_h` | Direct mapping |
| `avg` | `pitching_oba` | Opponent batting average |
| `atBats` | *Calculated* | Derive from IP and oba |
| `obp` | ❌ Not available | **Can calculate**: `(H + BB) / (AB + BB)` |
| `slg` | ❌ Not available | **Can calculate** from totalBases/AB |
| `ops` | ❌ Not available | `obp + slg` |
| `era` | `pitching_era` | Direct mapping |
| `inningsPitched` | `pitching_ip` | Direct mapping |
| `earnedRuns` | `pitching_er` | Direct mapping |
| `whip` | `pitching_whip` | Direct mapping |
| `battersFaced` | ❌ Not available | **Estimate**: `AB + BB + HBP` |
| `totalBases` | ❌ Not available | **Calculate**: `H + 2B + 2*3B + 3*HR` |
| `pitchesPerInning` | ❌ Not available | **GAP** |
| `gamesFinished` | ❌ Not available | **GAP** |
| `strikeoutWalkRatio` | *Calculated* | `pitching_k / pitching_bb` |
| `strikeoutsPer9Inn` | *Calculated* | `(pitching_k / pitching_ip) * 9` |
| `walksPer9Inn` | *Calculated* | `(pitching_bb / pitching_ip) * 9` |
| `hitsPer9Inn` | *Calculated* | `(pitching_h / pitching_ip) * 9` |
| `runsScoredPer9` | *Calculated* | `(pitching_er / pitching_ip) * 9` |
| `homeRunsPer9` | *Calculated* | `(pitching_hr / pitching_ip) * 9` |

---

## 4. TEAM BATTING DATA

### Current Schema (44 fields)
All prefixed with `Fav B` or `Dog B`:
```
runs, runs/AB, doubles, doubles/AB, triples, triples/AB, homeRuns, homeruns/AB,
strikeOuts, Strikeouts/AB, baseOnBalls, BB/AB, hits, avg, atBats, obp, slg, ops,
stolenBases, totalBases, rbi, rbi/AB
```

### Balldontlie API Source

#### `/mlb/v1/teams/season_stats?season=2025`
```json
{
  "team": {"abbreviation": "SEA", ...},
  "season": 2025,
  "batting_ab": 3730,
  "batting_r": 492,
  "batting_h": 912,
  "batting_2b": 148,
  "batting_3b": 5,
  "batting_hr": 152,
  "batting_rbi": 474,
  "batting_bb": 366,
  "batting_so": 966,
  "batting_sb": 104,
  "batting_avg": 0.245,
  "batting_obp": 0.320,
  "batting_slg": 0.409,
  "batting_ops": 0.729,
  "batting_tb": 1526,
  ...
}
```

### Field Mapping

| Current Field | Balldontlie Field | Calculation |
|--------------|------------------|-------------|
| `runs` | `batting_r` | ✅ Direct mapping |
| `runs/AB` | *Calculated* | `batting_r / batting_ab` |
| `doubles` | `batting_2b` | ✅ Direct mapping |
| `doubles/AB` | *Calculated* | `batting_2b / batting_ab` |
| `triples` | `batting_3b` | ✅ Direct mapping |
| `triples/AB` | *Calculated* | `batting_3b / batting_ab` |
| `homeRuns` | `batting_hr` | ✅ Direct mapping |
| `homeruns/AB` | *Calculated* | `batting_hr / batting_ab` |
| `strikeOuts` | `batting_so` | ✅ Direct mapping |
| `Strikeouts/AB` | *Calculated* | `batting_so / batting_ab` |
| `baseOnBalls` | `batting_bb` | ✅ Direct mapping |
| `BB/AB` | *Calculated* | `batting_bb / batting_ab` |
| `hits` | `batting_h` | ✅ Direct mapping |
| `avg` | `batting_avg` | ✅ Direct mapping |
| `atBats` | `batting_ab` | ✅ Direct mapping |
| `obp` | `batting_obp` | ✅ Direct mapping |
| `slg` | `batting_slg` | ✅ Direct mapping |
| `ops` | `batting_ops` | ✅ Direct mapping |
| `stolenBases` | `batting_sb` | ✅ Direct mapping |
| `totalBases` | `batting_tb` | ✅ Direct mapping |
| `rbi` | `batting_rbi` | ✅ Direct mapping |
| `rbi/AB` | *Calculated* | `batting_rbi / batting_ab` |

---

## Team Name Mapping

### Current Abbreviations (used in training set)
```
ARI, ATL, BAL, BOS, CHC, CWS, CIN, CLE, COL, DET, HOU, KAN, LAA, LAD,
MIA, MIL, MIN, NYM, NYY, OAK, PHI, PIT, SD, SF, SEA, STL, TB, TEX, TOR, WAS
```

### Balldontlie Abbreviations
```json
{
  "ARI": "Arizona Diamondbacks",
  "OAK": "Oakland Athletics", 
  "ATL": "Atlanta Braves",
  "BAL": "Baltimore Orioles",
  "BOS": "Boston Red Sox",
  "CHC": "Chicago Cubs",
  "CHW": "Chicago White Sox",  // Note: Different from CWS
  "CIN": "Cincinnati Reds",
  // ... etc
}
```

**⚠️ IMPORTANT**: Balldontlie uses `CHW` for Chicago White Sox, but current system uses `CWS`. Need mapping logic.

---

## Data Collection Strategy

### Phase 1: Core Game Data
1. **Daily games** → `/mlb/v1/games?dates[]={date}`
2. **Team season stats** → `/mlb/v1/teams/season_stats?season={year}`
3. **Betting odds** → `/mlb/v1/odds?dates[]={date}`

### Phase 2: Starting Pitchers
**Challenge**: No direct "probable pitchers" endpoint
- **Option A**: Check if game endpoint includes probable pitchers
- **Option B**: Parse play-by-play data to identify first pitcher
- **Option C**: Keep current scraping method for this one component
- **Option D**: Use `/mlb/v1/players/active` + game date to infer starters

Get individual pitcher stats: `/mlb/v1/season_stats?player_id={id}&season={year}`

### Phase 3: Historical Backfill
- Use date ranges to backfill historical data
- `/mlb/v1/games?start_date={start}&end_date={end}`

---

## Key Gaps & Considerations

### ✅ Available with No Changes
- Team batting stats (nearly perfect match)
- Core game results
- Team pitching ERA, WHIP, K, BB, IP

### ⚠️ Requires Calculation
- All per-AB rate stats (calculated from totals)
- Bullpen stats (team stats - starter stats)
- Fav/Dog perspective transformation

### ❌ Not Available (Gaps)
1. **Starting Pitchers identification** - No direct "probable pitchers" endpoint
2. **Pitching doubles/triples allowed** - Not in team stats
3. **Pitches per inning** - Not available
4. **Games finished** - Not available

### 🔄 Name Mapping Issues
- `CWS` (current) vs `CHW` (Balldontlie) for Chicago White Sox
- Need to verify all 30 team abbreviations match

---

## Recommended Implementation Order

1. **Team Batting ETL** - Easiest, perfect data match
2. **Team Pitching ETL** - Good match, some calculations needed
3. **Games/Matchups ETL** - Core functionality, combine games + odds
4. **Starting Pitchers** - Most complex, may need hybrid approach

---

## Next Steps

1. ✅ Create test scripts for each endpoint
2. ⬜ Build team name mapping dictionary
3. ⬜ Implement Team Batting ETL
4. ⬜ Implement Team Pitching ETL
5. ⬜ Implement Games/Matchups ETL
6. ⬜ Solve Starting Pitchers challenge
7. ⬜ Test data quality and completeness
8. ⬜ Create validation script (compare old vs new data)
9. ⬜ Update GitHub Actions workflows
10. ⬜ Backfill historical data

---

## API Rate Limits & Best Practices

- **Check Balldontlie documentation** for rate limits
- Cache team-level season stats (changes infrequently)
- Use batch date queries where possible
- Implement retry logic with exponential backoff
- Store raw API responses for debugging

---

*Last Updated: March 2, 2026*
