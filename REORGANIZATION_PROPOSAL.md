# MLB-Model Repository Reorganization Proposal

## Current Issues
- **82 Python scripts** scattered in the root directory
- Difficult to find specific scripts
- No clear organization by function
- Hard to onboard new contributors

## Proposed New Structure

```
MLB-Model/
├── .github/
│   └── workflows/              # ✅ Already organized
│
├── scripts/                    # 🆕 NEW: Move all root .py files here
│   ├── etl/                   # ETL and data processing scripts
│   │   ├── fetch/            # All fetch_*.py scripts
│   │   ├── compute/          # All compute_*.py scripts
│   │   ├── consolidate/      # All consolidate_*.py scripts
│   │   ├── join/             # All join_*.py and merge_*.py scripts
│   │   └── build/            # All build_*.py and create_*.py scripts
│   ├── exploration/           # explore_*.py, test_*.py, validate_*.py
│   └── utilities/             # One-off utility scripts
│
├── src/                        # ✅ Core library code (already organized)
│   ├── backtesting/
│   ├── balldontlie/
│   └── etl/
│
├── modeling/                   # ✅ Model code (already organized)
│   └── mlb_xgb_ml/
│       ├── mlb_xgb_ml.py
│       ├── send_predictions.py
│       ├── update_previous_predictions.py
│       └── predictions/
│
├── data/                       # ✅ Data storage (already organized)
│   ├── 2026_data/
│   └── [other years]/
│
├── training-data/              # ✅ Training datasets (keep as-is)
│   ├── training-set/
│   └── bdl-training-set/
│
├── notebooks/                  # ✅ Jupyter notebooks
├── docs/                       # ✅ Documentation
│
├── etl.py                      # ⚠️ KEEP in root (main entry point)
└── README.md
```

## Scripts to Reorganize (by category)

### ETL/Fetch Scripts (→ scripts/etl/fetch/)
- fetch_2009_game_outlook.py
- fetch_2024_boxscores.py
- fetch_2024_starting_pitcher_boxscores.py
- fetch_2026_odds.py
- fetch_all_starting_pitcher_boxscores.py
- fetch_boxscores_by_date.py
- fetch_boxscores_by_year.py
- fetch_game_odds.py
- fetch_historical_game_outlook.py
- fetch_march_2025_boxscores.py
- fetch_missing_games.py
- fetch_missing_pitcher_boxscores.py
- fetch_missing_specific_pitchers.py
- fetch_pitcher_game_stats.py
- fetch_pitcher_season_stats.py
- fetch_specific_missing_games.py
- fetch_starting_pitcher_boxscores_by_year.py
- fetch_starting_pitchers.py
- fetch_team_season_stats.py

### ETL/Compute Scripts (→ scripts/etl/compute/)
- compute_daily_rolling_stats.py
- compute_daily_season_to_date_stats.py
- compute_divisional_records_from_scores.py
- compute_historical_starting_pitcher_rolling_stats.py
- compute_historical_team_bullpen_boxscores.py
- compute_historical_team_bullpen_rolling_stats.py
- compute_historical_team_rolling_stats.py
- compute_historical_team_season_standings.py
- compute_pitcher_derived_stats.py
- compute_rolling_averages.py
- compute_season_to_date_starting_pitcher_stats.py
- compute_season_to_date_team_bullpen_stats.py
- compute_season_to_date_team_stats.py
- compute_starting_pitcher_era_whip.py
- compute_starting_pitcher_features.py
- compute_starting_pitcher_rolling_stats.py
- compute_team_bullpen_boxscores.py
- compute_team_bullpen_rolling_stats.py
- compute_team_bullpen_season_to_date_stats.py
- compute_team_derived_stats.py
- compute_team_rolling_stats.py
- compute_team_season_features.py
- compute_team_standings.py

### ETL/Consolidate Scripts (→ scripts/etl/consolidate/)
- consolidate_2024_starting_pitcher_stats.py
- consolidate_2024_team_bullpen_stats.py
- consolidate_2024_team_stats.py
- consolidate_boxscores.py
- consolidate_datasets.py
- consolidate_year_stats.py

### ETL/Join & Merge Scripts (→ scripts/etl/join/)
- join_bullpen_data.py
- join_starting_pitcher_data.py
- join_team_data.py
- merge_bullpen_custom_order.py
- merge_bullpen_stats.py
- merge_datasets.py
- merge_pitcher_stats_to_dataset.py

### ETL/Build Scripts (→ scripts/etl/build/)
- build_2026_dataset.py
- build_player_id_mapping.py
- create_aligned_outlook.py
- create_complete_dataset_from_mlb.py
- create_final_dataset.py

### ETL/Alignment Scripts (→ scripts/etl/alignment/)
- add_balldontlie_ids.py
- add_balldontlie_ids_keep_all.py
- add_balldontlie_ids_v2.py
- add_bdl_scores_to_dataset.py
- align_all_5_datasets.py
- clean_and_align_all_5.py
- complete_dataset.py

### ETL/Rebuild Scripts (→ scripts/etl/rebuild/)
- rebuild_2025_processed.py
- rebuild_dataset.py
- rebuild_outlook_from_scratch.py
- rebuild_yearly_datasets.py
- recreate_aligned_datasets.py
- reorganize_bullpen_season_to_date_by_game.py

### Exploration/Testing Scripts (→ scripts/exploration/)
- explore_balldontlie_mlb.py
- explore_games_api.py
- test_balldontlie_api.py
- validate_balldontlie_mapping.py
- scrape_comprehensive_games.py

### Utility Scripts (→ scripts/utilities/)
- convert_bdl_utc_to_local.py
- extract_starting_pitcher_game_stats.py
- fix_balldontlie_ids.py

## Files/Paths That Need Updating

### Python Scripts
1. **etl.py** - Update subprocess calls to new script paths
2. **modeling/mlb_xgb_ml/mlb_xgb_ml.py** - ✅ No changes needed (uses relative paths)
3. **modeling/mlb_xgb_ml/update_previous_predictions.py** - ✅ No changes needed
4. **src/** files - May need updates if they import root scripts

### GitHub Workflows
1. **.github/workflows/run-etl.yml** - ✅ Only calls etl.py (no changes)
2. **.github/workflows/run-predictions.yml** - ✅ Uses modeling/ paths (no changes)
3. **.github/workflows/send-picks-to-graphics.yml** - ✅ Uses modeling/ paths (no changes)

### Data Paths (NO CHANGES NEEDED)
- `data/2026_data/` - ✅ Keep as-is
- `training-set/` - ✅ Keep as-is
- `modeling/mlb_xgb_ml/predictions/` - ✅ Keep as-is

## Migration Steps

1. ✅ Create new directory structure
2. ✅ Copy (don't move yet) files to new locations
3. ✅ Update any imports or path references in moved files
4. ✅ Update etl.py to call scripts from new locations
5. ✅ Test that etl.py still works
6. ✅ Test that prediction workflow still works
7. ✅ Remove old files from root
8. ✅ Commit changes

## Benefits
- **Clear organization** - Easy to find scripts by function
- **Maintainability** - New scripts go in obvious locations
- **Scalability** - Can add more categories as needed
- **Clean root** - Only essential files in root directory

## Risk Mitigation
- Keep etl.py in root (it's the main entry point)
- Test all workflows before deleting old files
- Use git to easily revert if needed
- Update paths incrementally

---

**Next Steps:** 
1. Review this proposal
2. Make any adjustments to structure
3. Execute the migration with automated path updates
