# Final Recommendation: Data Source for MLB Team Box Scores

## Question
Can we derive the missing stats (Runs, RBI, Errors, Stolen Bases) from an alternative API?

## Answer
**YES! ✅ The MLB Stats API has ALL the missing stats.**

---

## Summary of Findings

### What We Tested
1. **balldontlie Games API** - Basic game results (H, R, E only)
2. **balldontlie Plate Appearances API** - Detailed play-by-play (can derive most stats)
3. **MLB Stats API** - Official MLB statistics (COMPLETE)

### Results Table

| Stat | balldontlie Games | balldontlie PA | MLB Stats API |
|------|:----------------:|:--------------:|:-------------:|
| Runs (R) | ✅ | ❌ | ✅ |
| RBI | ❌ | ❌ | **✅** |
| Hits (H) | ✅ | ✅ | ✅ |
| Doubles (2B) | ❌ | ✅ | ✅ |
| Triples (3B) | ❌ | ✅ | ✅ |
| Home Runs (HR) | ❌ | ✅ | ✅ |
| Walks (BB) | ❌ | ✅ | ✅ |
| Strikeouts (SO) | ❌ | ✅ | ✅ |
| Stolen Bases (SB) | ❌ | ❌ | **✅** |
| Errors (E) | ✅ | ❌ | ✅ |
| AVG/OBP/SLG | ❌ | ✅ Calc | ✅ Direct |

---

## Validation: LAD @ CHC (March 18, 2025)

### All Three Sources Agree on Available Stats

**Los Angeles Dodgers:**
- Runs: 4 (✓ balldontlie Games, ✓ MLB Stats)
- Hits: 7 (✓ balldontlie Games, ✓ balldontlie PA, ✓ MLB Stats)
- RBI: 3 (✓ **MLB Stats ONLY**)
- SB: 0 (✓ **MLB Stats ONLY**)
- Errors: 0 (✓ balldontlie Games, ✓ MLB Stats)

**Chicago Cubs:**
- Runs: 1 (✓ balldontlie Games, ✓ MLB Stats)
- Hits: 3 (✓ balldontlie Games, ✓ balldontlie PA, ✓ MLB Stats)
- RBI: 1 (✓ **MLB Stats ONLY**)
- SB: 1 (✓ **MLB Stats ONLY**)
- Errors: 2 (✓ balldontlie Games, ✓ MLB Stats)

---

## The Winner: MLB Stats API 🏆

### Why MLB Stats API?

1. **✅ COMPLETE** - Has ALL stats in one call
2. **✅ SIMPLE** - One endpoint per game
3. **✅ OFFICIAL** - MLB's authoritative source
4. **✅ FREE** - No API key required
5. **✅ RELIABLE** - Used by MLB.com and other official apps

### Example Code

```python
import requests

# 1. Find games by date
schedule = requests.get(
    "https://statsapi.mlb.com/api/v1/schedule",
    params={"sportId": 1, "date": "2025-03-18"}
).json()

game_pk = schedule['dates'][0]['games'][0]['gamePk']

# 2. Get complete boxscore
boxscore = requests.get(
    f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
).json()

# 3. Extract stats
away_stats = boxscore['teams']['away']['teamStats']['batting']
home_stats = boxscore['teams']['home']['teamStats']['batting']

print(f"Runs: {away_stats['runs']}")
print(f"RBI:  {away_stats['rbi']}")
print(f"SB:   {away_stats['stolenBases']}")
```

**That's it!** All stats in 2 API calls.

---

## Comparison: Complexity vs Completeness

### Option 1: balldontlie Only
```
Complexity:  ⭐⭐⭐⭐ (High - must parse PAs, derive stats)
Completeness: ⭐⭐ (Low - missing RBI, SB)
API Calls:    3 per game (games + PA + parsing)
```

**NOT RECOMMENDED** - Missing critical stats

---

### Option 2: MLB Stats API Only ⭐ **RECOMMENDED**
```
Complexity:  ⭐ (Very Low - direct extraction)
Completeness: ⭐⭐⭐⭐⭐ (Perfect - has everything)
API Calls:    2 per game (schedule + boxscore)
```

**RECOMMENDED** - Simple, complete, official

---

### Option 3: Hybrid (balldontlie + MLB Stats)
```
Complexity:  ⭐⭐⭐⭐⭐ (Very High - two APIs to integrate)
Completeness: ⭐⭐⭐⭐⭐ (Perfect - has everything)
API Calls:    5 per game (bdl games + bdl PA + MLB boxscore)
```

**NOT RECOMMENDED** - More work for same result

---

## Implementation Plan

### Recommended Approach: Use MLB Stats API

**Step 1: Fetch Game IDs by Date**
```python
def get_game_ids(date):
    url = "https://statsapi.mlb.com/api/v1/schedule"
    params = {"sportId": 1, "date": date}
    response = requests.get(url, params=params)
    games = response.json()['dates'][0]['games']
    return [g['gamePk'] for g in games]
```

**Step 2: Get Boxscore for Each Game**
```python
def get_boxscore(game_pk):
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
    return requests.get(url).json()
```

**Step 3: Extract Team Stats**
```python
def extract_team_stats(boxscore):
    teams = boxscore['teams']
    return {
        'away_r': teams['away']['teamStats']['batting']['runs'],
        'away_rbi': teams['away']['teamStats']['batting']['rbi'],
        'away_sb': teams['away']['teamStats']['batting']['stolenBases'],
        'away_e': teams['away']['teamStats']['fielding']['errors'],
        'home_r': teams['home']['teamStats']['batting']['runs'],
        'home_rbi': teams['home']['teamStats']['batting']['rbi'],
        'home_sb': teams['home']['teamStats']['batting']['stolenBases'],
        'home_e': teams['home']['teamStats']['fielding']['errors'],
        # ... all other stats
    }
```

**Step 4: Process Full Season**
```python
from datetime import datetime, timedelta

start_date = datetime(2025, 3, 18)
end_date = datetime(2025, 9, 28)

all_boxscores = []

current = start_date
while current <= end_date:
    date_str = current.strftime("%Y-%m-%d")
    game_ids = get_game_ids(date_str)
    
    for game_pk in game_ids:
        boxscore = get_boxscore(game_pk)
        stats = extract_team_stats(boxscore)
        all_boxscores.append(stats)
    
    current += timedelta(days=1)

# Save to CSV
df = pd.DataFrame(all_boxscores)
df.to_csv('mlb_team_boxscores_2025.csv', index=False)
```

---

## Files Created

### Test Scripts
- `test_team_boxscore_from_pa.py` - Tests balldontlie PA derivation
- `explore_mlb_stats_api.py` - Explores MLB Stats API
- `mlb_stats_api_example.py` - Simple working example

### Results
- `mlb_stats_team_boxscore_example.csv` - Complete boxscore (55 columns)
- `mlb_stats_boxscore_778563.json` - Full API response
- `mlb_stats_playbyplay_778563.json` - Play-by-play data

### Documentation
- `DATA_SOURCE_COMPARISON.md` - Detailed comparison
- `FINAL_RECOMMENDATION.md` - This file

---

## Next Steps

1. ✅ **Decision Made**: Use MLB Stats API
2. 🔲 **Write ETL script** to fetch 2025 season boxscores
3. 🔲 **Map to your schema** (55 columns → your format)
4. 🔲 **Backfill historical data** if needed
5. 🔲 **Set up daily refresh** for ongoing season

---

## Conclusion

### Question Answered
> "For the stats that we couldn't derive, could we see if we can derive them from the MLB API?"

**YES! ✅**

The MLB Stats API provides:
- ✅ **Runs (R)** - Both team and player level
- ✅ **RBI** - Both team and player level  
- ✅ **Stolen Bases (SB)** - Both team and player level
- ✅ **Errors (E)** - Both team and player level
- ✅ **PLUS** earned runs, inherited runners, and 50+ other stats

### Final Recommendation

**Use MLB Stats API exclusively for team box scores.**

It's simpler, more complete, and official.

The balldontlie PA data is fascinating for granular analysis, but for standard box score stats, MLB Stats API is the clear winner.

---

## Contact & References

- MLB Stats API Docs: https://github.com/toddrob99/MLB-StatsAPI
- Test Results: See `data/bdl_data/test_team_boxscore/`
- Example Output: `mlb_stats_team_boxscore_example.csv`

