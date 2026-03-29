# Missing Season-to-Date Statistics for Historical Years (2009-2024)

This document identifies which season-to-date derived statistics still need to be computed for historical years.

## STATUS SUMMARY

### ✓ COMPLETE
- **Starting Pitcher Rolling Stats** (derived_stats/)
- **Team Rolling Stats** (derived_stats/)
- **Team Bullpen Rolling Stats** (derived_stats/)
- **Team Bullpen Season-to-Date Derived Stats**

### ❌ INCOMPLETE
- **Starting Pitcher Season-to-Date Derived Stats** (7 metrics)
- **Team Season-to-Date Derived Stats** (11 metrics)

---

## 1. STARTING PITCHER STATS

### What We Have (2024):
**Season-to-Date RAW Stats:**
- `home_starter_pitching_gp, gs, qs, w, l, era, sv, hld, ip, h, er, hr, bb, whip, k, k_per_9, war`

**Rolling Stats (COMPLETE):**
- `era_rolling_5, era_rolling_10`
- `whip_rolling_5, whip_rolling_10`
- `k_per_9_rolling_5, k_per_9_rolling_10`
- `k_bb_ratio_rolling_5, k_bb_ratio_rolling_10`
- `ip_per_gs_rolling_5`
- `hr_per_9_rolling_10`
- `bb_per_9_rolling_5`

### ❌ MISSING Season-to-Date Derived Stats:
These appear in 2025 but NOT in 2024 season-to-date files:

1. **k_bb_ratio** = K / BB
2. **qs_rate** = QS / GS (Quality Start Rate)
3. **ip_per_gs** = IP / GS (Innings Per Game Started)
4. **hr_per_9** = (HR * 9) / IP
5. **bb_per_9** = (BB * 9) / IP
6. **h_per_9** = (H * 9) / IP
7. **win_pct** = W / (W + L)

**Impact:** These need to be added to each starting_pitcher_stats_YYYY-MM-DD.csv file for all years 2009-2024.

---

## 2. TEAM STATS

### What We Have (2024):
**Season-to-Date RAW Stats:**
- **Batting:** `ab, r, h, 2b, 3b, hr, rbi, tb, bb, so, sb, avg, obp, slg, ops`
- **Pitching:** `w, l, era, sv, cg, sho, qs, ip, h, er, hr, bb, k, oba, whip`
- **Fielding:** `e, fp, tc, po, a`

**Rolling Stats (COMPLETE):**
- `batting_avg_rolling_10`
- `batting_obp_rolling_5, batting_obp_rolling_10`
- `batting_slg_rolling_5`
- `batting_ops_rolling_5, batting_ops_rolling_10`
- `batting_r_per_g_rolling_5, batting_r_per_g_rolling_10`
- `batting_hr_per_g_rolling_5`
- `batting_k_pct_rolling_10`
- `batting_bb_per_g_rolling_10`
- `pitching_era_rolling_5, pitching_era_rolling_10`
- `pitching_whip_rolling_5, pitching_whip_rolling_10`
- `pitching_k_bb_ratio_rolling_10`
- `pitching_hr_per_9_rolling_10`
- `pitching_qs_rate_rolling_10`
- `fielding_e_per_g_rolling_10`

### ❌ MISSING Season-to-Date Derived Stats:
These appear in 2025 but NOT in 2024 season-to-date files:

**Batting (5 metrics):**
1. **batting_r_per_g** = R / GP (Runs Per Game)
2. **batting_hr_per_g** = HR / GP (Home Runs Per Game)
3. **batting_k_pct** = SO / AB (Strikeout Percentage)
4. **batting_bb_per_g** = BB / GP (Walks Per Game)
5. **batting_sb_per_g** = SB / GP (Stolen Bases Per Game)

**Pitching (5 metrics):**
6. **pitching_k_per_9** = (K * 9) / IP (Strikeouts Per 9 Innings)
7. **pitching_k_bb_ratio** = K / BB (Strikeout to Walk Ratio)
8. **pitching_hr_per_9** = (HR * 9) / IP (Home Runs Per 9 Innings)
9. **pitching_bb_per_9** = (BB * 9) / IP (Walks Per 9 Innings)
10. **pitching_qs_rate** = QS / GP (Quality Start Rate)

**Fielding (1 metric):**
11. **fielding_e_per_g** = E / GP (Errors Per Game)

**Impact:** These need to be added to each team_season_stats_YYYY-MM-DD.csv file for all years 2009-2024.

---

## 3. TEAM BULLPEN STATS

### ✓ ALL COMPLETE!

**Season-to-Date RAW Stats:**
- `total_ip, total_hits, total_earned_runs, total_walks, total_strikeouts, total_homeruns`
- Plus per-inning rates: `hits_per_ip, earned_runs_per_ip, walks_per_ip, strikeouts_per_ip, homeruns_per_ip`

**Season-to-Date DERIVED Stats (✓ COMPLETE):**
- `era, whip, k_per_9, k_bb_ratio, hr_per_9, bb_per_9`

**Rolling Stats (✓ COMPLETE):**
- `bp_era_rolling_5, bp_era_rolling_10`
- `bp_whip_rolling_5, bp_whip_rolling_10`
- `bp_k_per_9_rolling_5, bp_k_per_9_rolling_10`
- `bp_k_bb_ratio_rolling_5, bp_k_bb_ratio_rolling_10`
- `bp_hr_per_9_rolling_10`
- `bp_bb_per_9_rolling_5`

---

## IMPLEMENTATION PLAN

### Step 1: Create Compute Scripts
Need to create 2 new scripts:
1. `add_starting_pitcher_derived_stats.py` - Add 7 derived metrics to starting pitcher season-to-date files
2. `add_team_derived_stats.py` - Add 11 derived metrics to team season-to-date files

### Step 2: Process All Years
Run each script for all years 2009-2024 (16 years total)

### Step 3: Validation
Verify that:
- All date files have the new columns added
- Values are reasonable (spot-check mid-season games)
- No data leakage (only using season-to-date cumulative stats, not future games)

### File Counts
- **Starting Pitcher Files:** ~180-184 files per year × 16 years = ~2,944 files to update
- **Team Stats Files:** ~180-184 files per year × 16 years = ~2,944 files to update
- **Total Updates:** ~5,888 files

---

## NOTES

### Why Rolling Stats Don't Need Updates
Rolling stats are stored separately in `derived_stats/` directories and are already complete. They compute properly from raw boxscore data (which includes all statistics needed).

### Why Team Bullpen is Complete
Team bullpen season-to-date files already include the derived stats (era, whip, k_per_9, etc.) because they were computed during the initial data generation scripts.

### Data Integrity
All new derived stats will be computed from existing RAW stats in the same files, ensuring:
- No external data needed
- Deterministic calculations
- Easy to validate
- Can be recomputed if formula changes
