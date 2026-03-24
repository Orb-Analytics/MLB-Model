import pandas as pd
import glob

# Check 2011 boxscores
box_files = glob.glob('data/2011_data/mlb_data/raw/boxscores/boxscores_*.csv')
box_count = sum(len(pd.read_csv(f)) for f in box_files)

# Check 2011 pitcher boxscores  
pitch_files = glob.glob('data/2011_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_*.csv')
pitch_count = sum(len(pd.read_csv(f)) for f in pitch_files)

print(f"2011 Boxscores: {box_count} games")
print(f"2011 Starting Pitcher: {pitch_count} games")
print(f"Match: {box_count == pitch_count}")
