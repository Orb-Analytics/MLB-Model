# Test Summary: Team Box Score Reconstruction from Plate Appearances

## Test Case
- **Game**: First regular season MLB game of 2025 (March 18, 2025)
- **Matchup**: Los Angeles Dodgers (LAD) @ Chicago Cubs (CHC)
- **Venue**: Tokyo Dome
- **Final Score**: LAD 4, CHC 1

## Data Sources
- **Games API**: `/mlb/v1/games` (date filter)
- **Game Detail API**: `/mlb/v1/games/{id}`
- **Plate Appearances API**: `/mlb/v1/plate_appearances?game_id={id}`

## Key Findings

### ✅ Successfully Derived
1. **Batting Stats** (from PA results):
   - At-bats (AB)
   - Hits (H)
   - Doubles (2B)
   - Triples (3B)
   - Home Runs (HR)
   - Walks (BB)
   - Strikeouts (SO)
   - Batting average (AVG)
   - On-base percentage (OBP)
   - Slugging percentage (SLG)
   - OPS

2. **Pitching Stats** (from opponent batting):
   - Innings pitched (IP) - calculated from outs
   - Hits allowed (H)
   - Home runs allowed (HR)
   - Walks allowed (BB)
   - Strikeouts (K)
   - Opponent batting average (OBA)
   - WHIP

3. **Team Mapping**:
   - Successfully mapped batters to home/away teams using `half_inning` field
   - Top of inning = away team bats
   - Bottom of inning = home team bats

### ⚠️ Cannot Be Derived from PA Data Alone
1. **Runs (R)**: 
   - Requires tracking runner advancement and scoring plays
   - PA data shows runner positions but not when they score
   
2. **RBI**:
   - Requires attribution of which PAs drove in runs
   
3. **Earned Runs (ER)**:
   - Requires distinguishing earned vs unearned runs
   
4. **Stolen Bases (SB)**:
   - Not tracked in PA data
   
5. **Fielding Errors (E)**:
   - Not available in PA endpoint
   
6. **Wins/Losses (W/L)**:
   - Requires game context beyond single game

### Validation Results

**Hits Comparison:**
```
Source         | CHC Hits | LAD Hits
---------------|----------|----------
Game API       |    3     |    7
PA Aggregation |    3     |    7     ✓ Perfect Match!
```

**Doubles Comparison:**
```
CHC: 1 double (PA result: "Double")
LAD: 2 doubles (PA results: "Double" x2)
✓ Matches actual game outcomes
```

**Plate Appearance Results Observed:**
- Single: 7
- Double: 3
- Strikeout: 18
- Walk: 9
- Groundout: 16
- Flyout: 8
- Pop Out: 6
- Lineout: 5
- Hit By Pitch: 1
- Forceout: 1

**Total PAs**: 74 (32 CHC, 42 LAD)

## Technical Implementation

### PA Result Parsing Logic
Created `parse_pa_result()` function that converts result strings into boolean flags:
- is_single, is_double, is_triple, is_home_run
- is_walk, is_strikeout
- is_hit, is_out, is_at_bat

### Team Mapping Logic
Created `map_batters_to_teams()` function:
- Uses `half_inning` field to determine batting team
- Adds `batting_team_id` column to PA DataFrame

### Rate Stat Calculations
- AVG = H / AB
- OBP = (H + BB) / (AB + BB)
- SLG = TB / AB where TB = 1B + 2×2B + 3×3B + 4×HR
- OPS = OBP + SLG
- OBA = opponent H / opponent AB
- WHIP = (H + BB) / IP
- ERA = 9 × ER / IP (but ER=0 since not derivable)

## Limitations & Recommendations

### For Full-Season Pipeline
1. **Use Game API for runs**: 
   - Game detail includes `home_team_data.runs` and `away_team_data.runs`
   - Don't try to calculate from PAs

2. **Use Game API for errors**:
   - Game detail includes `home_team_data.errors` and `away_team_data.errors`

3. **Batting stats CAN be aggregated from PAs**:
   - AB, H, 2B, 3B, HR, BB, SO are reliable
   - Rate stats (AVG, OBP, SLG, OPS) can be calculated

4. **Pitching stats mostly work**:
   - IP, H, HR, BB, K, OBA, WHIP are reliable
   - ERA will be 0.00 unless you track earned runs separately

5. **Consider hybrid approach**:
   - Use PA data for granular batting/pitching stats
   - Use Game API for runs, RBIs, errors, game outcomes
   - Combine both sources for complete box scores

## Files Generated
```
data/bdl_data/test_team_boxscore/
├── games_2025-03-18_raw.json              # All games on date
├── game_detail_1_raw.json                  # Full game detail
├── plate_appearances_1_raw.json            # All 74 PAs with pitch data
├── game_detail_1_flattened.csv            # Flattened game metadata
├── plate_appearances_1_flattened.csv      # Flattened PA data
├── team_boxscore_test_1.csv               # Aggregated box score (72 columns)
└── TEST_SUMMARY.md                         # This file
```

## Next Steps
1. ✅ Verify PA-based aggregation works (COMPLETE)
2. ⚠️ Decide whether to accept missing runs/RBI or fetch from Game API  
3. 🔲 Expand to full-season backfill once approach is validated
4. 🔲 Compare with official MLB box scores for additional validation
5. 🔲 Consider adding runner tracking logic if RBI is critical

## Conclusion
✅ **PA data CAN reconstruct most team batting and pitching stats**
⚠️ **Some stats require game-level context (runs, RBI, errors)**
💡 **Recommend hybrid approach: PA data + Game API for complete picture**
