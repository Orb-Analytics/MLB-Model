# Balldontlie API Limitation: Game ID Mismatch

## Problem Summary

The balldontlie.io MLB API has a fundamental limitation that prevents us from building truly cumulative (non-leaking) pitcher stats:

### Issue

1. **Stats Endpoint** (`/mlb/v1/stats`): Returns game-by-game pitcher stats with `game_id` field
   - Example: Pitcher ID 5439 (Max Fried) has stats for game_id: 24775, 49200, etc.

2. **Games Endpoint** (`/mlb/v1/games`): Should provide game details including dates
   - When querying with `game_ids[]` parameter, it **ignores** the parameter
   - Returns arbitrary games instead of the requested ones
   - Individual game lookup `/games/{id}` returns `null` for the date field

3. **Game Outlook Data**: Our fetched game data has different game IDs
   - Example: July 12, 2025 games have IDs like 32822, 32823, etc.
   - These don't match the game IDs in pitcher stats (24775, 49200, etc.)

### Impact

- **Cannot map game-level stats to dates**: Without dates, we cannot filter stats to "before game date"
- **Cannot prevent data leakage**: Unable to build cumulative stats up to each game
- **67% missing data**: Only 12 out of 30 pitchers had stats in our test

### What We Tried

1. ✅ Fetch stats by `player_ids[]` - **Works**, returns game stats
2. ❌ Map game_ids to dates using game outlook - **Fails**, different ID sets
3. ❌ Fetch dates from `/games` endpoint with `game_ids[]` - **Fails**, parameter ignored
4. ❌ Fetch individual game `/games/{id}` - **Fails**, returns null date

## Options Going Forward

### Option 1: Accept Full-Season Stats (with data leakage disclaimer)

**Pros:**
- Simple, works immediately
- All pitchers have data  
- balldontlie API supports this well

**Cons:**
- Model will have data leakage (uses end-of-season stats for mid-season predictions)
- Cannot be used for real-time predictions
- Less accurate than proper cumulative stats

**Implementation:**
- Use `/mlb/v1/season_stats` endpoint
- Accept that stats include future games
- Document limitation clearly

### Option 2: Switch to MLB Stats API

**Pros:**
- Official MLB data
- Has proper game-by-game and cumulative stats
- More reliable, better documented

**Cons:**
- Different game IDs (incompatible with our existing balldontlie game data)
- Would need to re-fetch ALL game outlook data
- More complex API (different data structure)

**Implementation:**
- Use MLB Stats API for everything (games + stats)
- Rebuild entire ETL pipeline
- Keep balldontlie as backup/comparison

### Option 3: Hybrid Approach (Complex)

Try to correlate games using:
- Team names
- Date ranges from our outlook data
- Opponent matching

**Pros:**
- Might work with existing data

**Cons:**
- Very complex, error-prone
- Still may not be accurate
- High development time

## Recommendation

**Go with Option 1 for now**, with these caveats:

1. **Document the limitation** clearly in training data
2. **Add a flag/column** indicating "stats_type: full_season" vs "cumulative"
3. **Plan to migrate** to MLB Stats API for production model
4. **Use current approach** for initial model development and feature selection

This lets us:
- ✅ Move forward with model development
- ✅ Understand which pitcher stats are actually predictive
- ✅ Have complete data for all pitchers
- ✅ Keep balldontlie for game/odds data (where it works well)
- ⚠️  Accept temporary data leakage for research phase
- 🔄 Plan proper migration for production deployment

## Code Changes Needed

If we proceed with Option 1:
1. Revert `fetch_starting_pitcher_stats.py` to use `/season_stats` endpoint
2. Add documentation about data leakage in output CSV
3. Focus on other ETL components (team stats, odds, etc.)
4. Revisit pitcher stats when ready for production

---

**Decision needed**: Which option should we pursue?
