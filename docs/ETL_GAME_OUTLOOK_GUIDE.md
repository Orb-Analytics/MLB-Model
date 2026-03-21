# Game Outlook ETL Script - Quick Reference Guide

## Overview
The `fetch_game_outlook.py` script collects MLB regular season game data from the balldontlie API and creates one CSV file per date.

**Location**: `src/etl/fetch_game_outlook.py`  
**Output Directory**: `data/bdl_data/game_outlook/`  
**File Format**: `game_outlook_YYYY-MM-DD.csv`

---

## Features ✨
- ✅ Fetches regular season games only (filters out postseason automatically)
- ✅ Handles API pagination automatically
- ✅ Backfills date ranges
- ✅ Flattens nested home_team and away_team objects
- ✅ Maintains consistent 32-column schema
- ✅ Skips dates with no games gracefully
- ✅ Overwrite protection (with optional --overwrite flag)
- ✅ Clear logging for each date processed
- ✅ Error handling for failed API requests

---

## CSV Schema (32 columns)

### Top-Level Game Fields (8 columns)
1. `id` - Game ID
2. `season` - Season year
3. `date` - Game date/time (ISO format)
4. `postseason` - Boolean (always False for regular season)
5. `season_type` - "regular" for regular season games
6. `status` - Game status (e.g., STATUS_FINAL)
7. `venue` - Stadium name
8. `conference_play` - Conference play indicator

### Home Team Fields (9 columns)
9. `home_team_id`
10. `home_team_slug`
11. `home_team_abbreviation` (e.g., "NYY")
12. `home_team_display_name` (e.g., "New York Yankees")
13. `home_team_short_display_name` (e.g., "Yankees")
14. `home_team_name` (e.g., "Yankees")
15. `home_team_location` (e.g., "New York")
16. `home_team_league` (e.g., "AL")
17. `home_team_division` (e.g., "East")

### Away Team Fields (9 columns)
18. `away_team_id`
19. `away_team_slug`
20. `away_team_abbreviation`
21. `away_team_display_name`
22. `away_team_short_display_name`
23. `away_team_name`
24. `away_team_location`
25. `away_team_league`
26. `away_team_division`

### Favorite/Underdog Fields (6 columns) - **BLANK FOR NOW**
27. `favorite_id` (null)
28. `underdog_id` (null)
29. `favorite_abbreviation` (null)
30. `underdog_abbreviation` (null)
31. `favorite_display_name` (null)
32. `underdog_display_name` (null)

---

## Usage Examples

### 1️⃣ Fetch a Single Day
```bash
python src/etl/fetch_game_outlook.py --start_date 2025-08-15 --end_date 2025-08-15
```

### 2️⃣ Fetch a Week
```bash
python src/etl/fetch_game_outlook.py --start_date 2025-08-01 --end_date 2025-08-07
```

### 3️⃣ Fetch a Month
```bash
python src/etl/fetch_game_outlook.py --start_date 2025-06-01 --end_date 2025-06-30
```

### 4️⃣ Fetch Entire 2025 Regular Season
```bash
python src/etl/fetch_game_outlook.py --start_date 2025-03-27 --end_date 2025-09-28
```

### 5️⃣ Overwrite Existing Files
```bash
python src/etl/fetch_game_outlook.py --start_date 2025-08-01 --end_date 2025-08-31 --overwrite
```

---

## 2025 MLB Regular Season Dates
- **Opening Day**: March 27, 2025
- **All-Star Break**: July 14-16, 2025 (approximate)
- **Regular Season End**: September 28, 2025

To fetch the entire regular season:
```bash
python src/etl/fetch_game_outlook.py --start_date 2025-03-27 --end_date 2025-09-28
```

---

## Expected Output

### Console Output Example
```
================================================================================
MLB Game Outlook ETL Script
================================================================================
✓ API key validated
✓ Date range: 2025-08-13 to 2025-08-16 (4 days)

📅 Processing 2025-08-13...
  ✓ Fetched 18 total games
  ✓ Filtered to 18 regular season games
  ✓ Saved to game_outlook_2025-08-13.csv

📅 Processing 2025-08-14...
  ✓ Fetched 8 total games
  ✓ Filtered to 8 regular season games
  ✓ Saved to game_outlook_2025-08-14.csv

================================================================================
✓ ETL script completed!
================================================================================
```

### File Output Example
```
data/bdl_data/game_outlook/
├── game_outlook_2025-03-27.csv
├── game_outlook_2025-03-28.csv
├── game_outlook_2025-03-29.csv
...
├── game_outlook_2025-09-28.csv
```

---

## Error Handling

### No Games on a Date
```
📅 Processing 2025-07-15...
  ℹ No games found for 2025-07-15
```
*Script continues to next date*

### File Already Exists
```
📅 Processing 2025-08-15...
  ✓ Fetched 8 total games
  ✓ Filtered to 8 regular season games
  ⚠ File already exists: data/bdl_data/game_outlook/game_outlook_2025-08-15.csv (use --overwrite to replace)
```
*Script skips writing and continues*

### API Request Failed
```
📅 Processing 2025-08-16...
  ✗ API request failed for 2025-08-16 (page 1): Connection timeout
```
*Script logs error and continues to next date*

---

## Rate Limiting
- **Inter-page delay**: 0.3 seconds (for pagination)
- **Inter-date delay**: 0.5 seconds
- Built-in to prevent API rate limit issues

---

## Troubleshooting

### Missing API Key Error
```
ERROR: BALLDONTLIE_API_KEY not found in environment variables.
Please set it in your .env file or environment.
```
**Solution**: Ensure `BALLDONTLIE_API_KEY` is set in your `.env` file

### Missing Dependencies
```bash
pip install requests pandas python-dotenv
```

### Check CSV Structure
```bash
# View column count
python -c "import pandas as pd; df = pd.read_csv('data/bdl_data/game_outlook/game_outlook_2025-08-15.csv'); print(f'Columns: {len(df.columns)}'); print(f'Rows: {len(df)}')"

# View all column names
python -c "import pandas as pd; df = pd.read_csv('data/bdl_data/game_outlook/game_outlook_2025-08-15.csv'); print(list(df.columns))"

# View sample data
python -c "import pandas as pd; df = pd.read_csv('data/bdl_data/game_outlook/game_outlook_2025-08-15.csv'); print(df.head())"
```

---

## Next Steps

After running this script for the full 2025 season, you can:
1. **Populate favorite/underdog columns** using odds data
2. **Add starting pitcher information** from separate ETL
3. **Merge with team statistics** from other datasets
4. **Build training dataset** by joining multiple data sources

---

## Performance Estimates

For the full 2025 regular season (~186 days of games):
- **Estimated runtime**: 5-10 minutes
- **API calls**: ~200-250 calls
- **Output size**: ~150-180 CSV files (depending on off-days)
- **Total disk space**: ~1-2 MB

---

## Testing

The script has been tested and validated:
- ✅ August 13, 2025: 18 games fetched
- ✅ August 14, 2025: 8 games fetched
- ✅ August 15, 2025: 8 games fetched
- ✅ August 16, 2025: 19 games fetched
- ✅ All 32 columns present in correct order
- ✅ Favorite/underdog fields properly null
- ✅ Regular season filtering working
- ✅ Overwrite protection working
- ✅ Date range handling working

---

## Support

For issues or questions:
1. Check the console output for specific error messages
2. Verify API key is set correctly
3. Confirm date format is YYYY-MM-DD
4. Check network connectivity for API requests
