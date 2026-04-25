import pandas as pd
import glob
from datetime import datetime as dt
from zoneinfo import ZoneInfo

# Map MLB teams to their timezones
TEAM_TIMEZONES = {
    # Eastern Time
    'ATL': 'America/New_York',
    'BAL': 'America/New_York',
    'BOS': 'America/New_York',
    'CIN': 'America/New_York',
    'CLE': 'America/New_York',
    'DET': 'America/New_York',
    'MIA': 'America/New_York',
    'NYM': 'America/New_York',
    'NYY': 'America/New_York',
    'PHI': 'America/New_York',
    'PIT': 'America/New_York',
    'TB': 'America/New_York',
    'TOR': 'America/Toronto',
    'WSH': 'America/New_York',
    
    # Central Time
    'CHC': 'America/Chicago',
    'CHW': 'America/Chicago',
    'HOU': 'America/Chicago',
    'KC': 'America/Chicago',
    'MIL': 'America/Chicago',
    'MIN': 'America/Chicago',
    'STL': 'America/Chicago',
    'TEX': 'America/Chicago',
    
    # Mountain Time
    'AZ': 'America/Phoenix',  # Arizona doesn't observe DST
    'ARI': 'America/Phoenix',  # Alternative abbreviation
    'COL': 'America/Denver',
    
    # Pacific Time
    'LAA': 'America/Los_Angeles',
    'LAD': 'America/Los_Angeles',
    'OAK': 'America/Los_Angeles',
    'SD': 'America/Los_Angeles',
    'SF': 'America/Los_Angeles',
    'SEA': 'America/Los_Angeles',
}

def convert_utc_to_local_date(year):
    """Convert UTC timestamps to local dates for BDL game outlook files."""
    
    print(f"\n{'='*80}")
    print(f"Converting UTC timestamps to local dates for {year}")
    print('='*80)
    
    # Load all game outlook files
    outlook_files = sorted(glob.glob(f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook/*.csv'))
    
    if not outlook_files:
        print(f"No game outlook files found for {year}")
        return
    
    print(f"Loading {len(outlook_files)} files...")
    
    outlook_dfs = []
    for f in outlook_files:
        df = pd.read_csv(f)
        outlook_dfs.append(df)
    
    outlook = pd.concat(outlook_dfs, ignore_index=True)
    print(f"Total records loaded: {len(outlook)}")
    
    # Parse UTC timestamps
    outlook['utc_datetime'] = pd.to_datetime(outlook['date'])
    
    # Convert to local time based on home team timezone
    def get_local_date(row):
        utc_dt = row['utc_datetime']
        home_team = row['home_team_abbreviation']
        
        # Get timezone for home team
        tz_name = TEAM_TIMEZONES.get(home_team)
        if not tz_name:
            print(f"Warning: No timezone found for {home_team}, using UTC")
            return utc_dt.date()
        
        # Convert to local timezone (timestamps are already UTC-aware)
        try:
            local_tz = ZoneInfo(tz_name)
            # Use tz_convert since timestamp is already timezone-aware
            local_dt = utc_dt.tz_convert(local_tz)
            return local_dt.date()
        except Exception as e:
            print(f"Error converting {home_team} game: {e}")
            return utc_dt.date()
    
    print("\nConverting timestamps to local dates...")
    outlook['local_date'] = outlook.apply(get_local_date, axis=1)
    outlook['local_date_str'] = outlook['local_date'].astype(str)
    
    # Count date changes
    outlook['original_date'] = outlook['utc_datetime'].dt.date.astype(str)
    date_changes = (outlook['local_date_str'] != outlook['original_date']).sum()
    print(f"Games with date changes: {date_changes}/{len(outlook)}")
    
    # Show sample of changes
    changed = outlook[outlook['local_date_str'] != outlook['original_date']].head(10)
    if len(changed) > 0:
        print(f"\nSample date changes:")
        for _, row in changed.iterrows():
            print(f"  {row['home_team_abbreviation']} vs {row['away_team_abbreviation']}: "
                  f"{row['original_date']} (UTC) → {row['local_date_str']} (Local)")
    
    # Create backup
    import shutil
    import os
    
    backup_dir = f"data/{year}_data/mlb_data/raw/bdl_data/game_outlook_backup_{dt.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    print(f"\nCreating backup at: {backup_dir}")
    for f in outlook_files:
        shutil.copy2(f, backup_dir)
    
    # Remove old files
    print("Removing old files...")
    for f in outlook_files:
        os.remove(f)
    
    # Write new files grouped by local date
    print("Writing new files grouped by local date...")
    for local_date, group in outlook.groupby('local_date_str'):
        # Update the date column to match local date (keep ISO format with time set to midnight)
        group = group.copy()
        group['date'] = group['local_date_str'] + 'T00:00:00.000Z'
        
        # Drop helper columns
        output_df = group.drop(['utc_datetime', 'local_date', 'local_date_str', 'original_date'], axis=1)
        
        output_file = f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook/game_outlook_{local_date}.csv'
        output_df.to_csv(output_file, index=False)
    
    # Count new files
    new_files = glob.glob(f'data/{year}_data/mlb_data/raw/bdl_data/game_outlook/*.csv')
    print(f"\n✅ Success!")
    print(f"  Old files: {len(outlook_files)}")
    print(f"  New files: {len(new_files)}")
    print(f"  Backup: {backup_dir}")

if __name__ == "__main__":
    convert_utc_to_local_date(2010)
