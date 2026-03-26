# Derived Stats Strategy (2009-2024)

## Executive Summary

We need to compute **rolling average derived statistics** for all historical years (2009-2024) to match the structure created for 2025. This will generate **432 total files** (27 metrics × 16 years) across three categories: team stats, starting pitcher stats, and team bullpen stats.

---

## Current State

### 2025 Derived Stats (Already Complete)
```
data/2025_data/mlb_data/derived_stats/
├── team_derived_stats/              (14 files)
│   ├── batting_avg_rolling.csv
│   ├── batting_bb_per_g_rolling.csv
│   ├── batting_hr_per_g_rolling.csv
│   ├── batting_k_pct_rolling.csv
│   ├── batting_obp_rolling.csv
│   ├── batting_ops_rolling.csv
│   ├── batting_r_per_g_rolling.csv
│   ├── batting_slg_rolling.csv
│   ├── fielding_e_per_g_rolling.csv
│   ├── pitching_era_rolling.csv
│   ├── pitching_hr_per_9_rolling.csv
│   ├── pitching_k_bb_ratio_rolling.csv
│   ├── pitching_qs_rate_rolling.csv
│   └── pitching_whip_rolling.csv
│
├── starting_pitcher_derived_stats/  (7 files)
│   ├── bb_per_9_rolling.csv
│   ├── era_rolling.csv
│   ├── hr_per_9_rolling.csv
│   ├── ip_per_gs_rolling.csv
│   ├── k_bb_ratio_rolling.csv
│   ├── k_per_9_rolling.csv
│   └── whip_rolling.csv
│
└── team_bullpen_derived_stats/     (6 files)
    ├── bp_bb_per_9_rolling.csv
    ├── bp_era_rolling.csv
    ├── bp_hr_per_9_rolling.csv
    ├── bp_k_bb_ratio_rolling.csv
    ├── bp_k_per_9_rolling.csv
    └── bp_whip_rolling.csv
```

### Historical Years Structure (2009-2024)
```
data/YYYY_data/mlb_data/
├── raw/
│   ├── boxscores/                           (~184 files per year)
│   ├── starting_pitcher_boxscores/          (~184 files per year)
│   └── team_bullpen_boxscores/              (~184 files per year)
│
└── season_to_date_stats/
    ├── team_stats/
    │   └── derived_stats/                   (EMPTY - needs 14 files)
    ├── starting_pitcher_stats/
    │   └── derived_stats/                   (EMPTY - needs 7 files)
    └── team_bullpen_stats/
        └── derived_stats/                   (EMPTY - needs 6 files)
```

---

## Data Sources

### Input: Raw Boxscores
- **Team Boxscores**: `data/YYYY_data/mlb_data/raw/boxscores/*.csv`
  - Individual game stats by date
  - ~184 files per year
  
- **Starting Pitcher Boxscores**: `data/YYYY_data/mlb_data/raw/starting_pitcher_boxscores/*.csv`
  - Individual pitcher performance by date
  - ~184 files per year
  
- **Team Bullpen Boxscores**: `data/YYYY_data/mlb_data/raw/team_bullpen_boxscores/*.csv`
  - Team bullpen stats by date (excluding starters)
  - ~184 files per year

### Output: Derived Stats
- **Team Derived**: `data/YYYY_data/mlb_data/season_to_date_stats/team_stats/derived_stats/`
- **Pitcher Derived**: `data/YYYY_data/mlb_data/season_to_date_stats/starting_pitcher_stats/derived_stats/`
- **Bullpen Derived**: `data/YYYY_data/mlb_data/season_to_date_stats/team_bullpen_stats/derived_stats/`

---

## Existing Scripts to Adapt

### 1. Team Rolling Stats
**Script**: `compute_team_rolling_stats.py`
- **Current Input**: `data/mlb_data/team_boxscores_all.csv` (consolidated)
- **Current Output**: `data/mlb_data/derived_stats/team_derived_stats/`
- **Metrics**: 14 files
  - Batting: AVG, OBP, SLG, OPS, R/G, HR/G, K%, BB/G
  - Pitching: ERA, WHIP, K/BB, HR/9, QS Rate  
  - Fielding: E/G
- **Rolling Windows**: 10-game

### 2. Starting Pitcher Rolling Stats
**Script**: `compute_starting_pitcher_rolling_stats.py`
- **Current Input**: `data/mlb_data/starting_pitcher_boxscores_all.csv`
- **Current Output**: `data/mlb_data/derived_stats/starting_pitcher_derived_stats/`
- **Metrics**: 7 files
  - ERA, WHIP, K/9, K/BB, IP/GS, HR/9, BB/9
- **Rolling Windows**: 5-game and 10-game

### 3. Team Bullpen Rolling Stats
**Script**: `compute_team_bullpen_rolling_stats.py`
- **Current Input**: `data/mlb_data/team_bullpen_boxscores_all.csv`
- **Current Output**: `data/mlb_data/derived_stats/team_bullpen_derived_stats/`
- **Metrics**: 6 files
  - ERA, WHIP, K/9, BB/9, HR/9, K/BB
- **Rolling Windows**: 5-game and 10-game

---

## Implementation Strategy

### Approach: Create Historical Versions

For each script above, create a historical version that:
1. **Accepts year parameter(s)**: `python script.py 2024` or `python script.py 2009 2010 2011`
2. **Loads from year-specific raw folders**: Consolidate ~184 date files into single DataFrame
3. **Computes rolling stats**: Use same logic as existing scripts
4. **Outputs to year-specific derived_stats folders**: Maintain same file structure as 2025

### New Scripts to Create

1. **`compute_historical_team_rolling_stats.py`**
   - Load: `data/YYYY_data/mlb_data/raw/boxscores/*.csv`
   - Process: Compute 14 team rolling metrics
   - Save: `data/YYYY_data/mlb_data/season_to_date_stats/team_stats/derived_stats/`

2. **`compute_historical_starting_pitcher_rolling_stats.py`**
   - Load: `data/YYYY_data/mlb_data/raw/starting_pitcher_boxscores/*.csv`
   - Process: Compute 7 pitcher rolling metrics
   - Save: `data/YYYY_data/mlb_data/season_to_date_stats/starting_pitcher_stats/derived_stats/`

3. **`compute_historical_team_bullpen_rolling_stats.py`**
   - Load: `data/YYYY_data/mlb_data/raw/team_bullpen_boxscores/*.csv`
   - Process: Compute 6 bullpen rolling metrics
   - Save: `data/YYYY_data/mlb_data/season_to_date_stats/team_bullpen_stats/derived_stats/`

---

## Key Modifications Required

### Input Handling
```python
# OLD (2025 scripts):
df = pd.read_csv("data/mlb_data/team_boxscores_all.csv")

# NEW (historical scripts):
import sys
year = sys.argv[1]
boxscore_files = glob.glob(f"data/{year}_data/mlb_data/raw/boxscores/*.csv")
df = pd.concat([pd.read_csv(f) for f in boxscore_files], ignore_index=True)
```

### Output Path
```python
# OLD:
OUTPUT_DIR = Path("data/mlb_data/derived_stats/team_derived_stats")

# NEW:
OUTPUT_DIR = Path(f"data/{year}_data/mlb_data/season_to_date_stats/team_stats/derived_stats")
```

### Multi-Year Support
```python
# Process multiple years in one run
import sys
years = sys.argv[1:]  # e.g., python script.py 2009 2010 2011

for year in years:
    print(f"Processing {year}...")
    # Load, process, save for this year
```

---

## Expected Output

### File Count
- **Per Year**: 27 files (14 + 7 + 6)
- **Total Years**: 16 (2009-2024)
- **Grand Total**: **432 derived stat files**

### File Structure (Example for 2024)
```
data/2024_data/mlb_data/season_to_date_stats/
├── team_stats/derived_stats/
│   ├── batting_avg_rolling.csv
│   ├── batting_bb_per_g_rolling.csv
│   └── ... (14 total files)
│
├── starting_pitcher_stats/derived_stats/
│   ├── era_rolling.csv
│   ├── whip_rolling.csv
│   └── ... (7 total files)
│
└── team_bullpen_stats/derived_stats/
    ├── bp_era_rolling.csv
    ├── bp_whip_rolling.csv
    └── ... (6 total files)
```

---

## Execution Plan

### Phase 1: Team Derived Stats (14 files × 16 years = 224 files)
```bash
python compute_historical_team_rolling_stats.py 2009 2010 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024
```

### Phase 2: Starting Pitcher Derived Stats (7 files × 16 years = 112 files)
```bash
python compute_historical_starting_pitcher_rolling_stats.py 2009 2010 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024
```

### Phase 3: Team Bullpen Derived Stats (6 files × 16 years = 96 files)
```bash
python compute_historical_team_bullpen_rolling_stats.py 2009 2010 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024
```

**Total**: 432 files

---

## Benefits

1. **Consistency**: Same derived stats structure across all years (2009-2025)
2. **Modularity**: Separate files per metric for easy loading/analysis
3. **Predictive Features**: Rolling averages capture recent form/trends
4. **Alignment**: Perfectly aligned with season-to-date stats by game_pk

---

## File Format Examples

### Team Stats (batting_avg_rolling.csv)
```csv
game_pk,home_batting_avg_rolling_10,away_batting_avg_rolling_10
746857,0.228,0.259
746858,0.231,0.255
...
```

### Starting Pitcher Stats (era_rolling.csv)
```csv
game_pk,date,home_era_rolling_5,away_era_rolling_5,home_era_rolling_10,away_era_rolling_10
746857,2024-07-04,3.09,2.44,3.15,2.50
746858,2024-07-04,2.95,2.60,3.02,2.55
...
```

### Bullpen Stats (bp_era_rolling.csv)
```csv
game_pk,home_bp_era_rolling_5,away_bp_era_rolling_5,home_bp_era_rolling_10,away_bp_era_rolling_10
746857,4.09,3.26,4.15,3.30
746858,3.95,3.40,4.05,3.45
...
```

---

## Next Steps

1. **Review Strategy**: Confirm approach and file structure
2. **Create Scripts**: Build the 3 historical computation scripts
3. **Test on Single Year**: Validate with 2024 before batch processing
4. **Batch Process**: Run all 16 years (2009-2024)
5. **Validate Output**: Check file counts, structure, and sample data
6. **Commit**: Save all 432 derived stat files to repository

---

## Timeline Estimate

- **Script Creation**: ~2-3 hours (modify existing scripts)
- **Testing**: ~30 minutes (validate one year)
- **Batch Processing**: ~1-2 hours (all 16 years)
- **Validation**: ~30 minutes (check outputs)

**Total**: ~4-6 hours of work
