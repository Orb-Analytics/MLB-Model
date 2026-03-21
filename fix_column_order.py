"""
Fix the column order in matchup_data.csv to match the correct specification
"""
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

# Define the correct column order as specified by the user
CORRECT_COLUMNS = [
    "Date",
    "Fav Team",
    "Dog Team",
    "Away",
    "Home",
    "Fav Home?",
    "Fav Moneyline Odds",
    "Dog Moneyline Odds",
    "Spread",
    "Fav Spread Odds",
    "Dog Spread Odds",
    "Fav Score",
    "Dog Score",
    "Fav/Dog +/-",
    "Fav Cover?",
    "Fav Win?",
    "Away Spread Odds",
    "Home Spread Odds",
    "Away Score",
    "Home Score",
    "Home/Away +/-",
    "",  # Empty column
    "Underdog Starting Pitcher Name",
    "Favorite Starting Pitcher Earned Run Average",
    "Underdog Starting Pitcher Earned Run Average",
    "Favorite Starting Pitcher Walks and Hits per Inning Pitched",
    "Underdog Starting Pitcher Walks and Hits per Inning Pitched",
    "Favorite Starting Pitcher Innings Pitched",
    "Underdog Starting Pitcher Innings Pitched",
    "Favorite Starting Pitcher At Bats Faced per Inning",
    "Underdog Starting Pitcher At Bats Faced per Inning",
    "Favorite Starting Pitcher Strikeouts",
    "Underdog Starting Pitcher Strikeouts",
    "Favorite Starting Pitcher Strikeouts per At Bat Faced",
    "Underdog Starting Pitcher Strikeouts per At Bat Faced",
    "Opponent Batting Average vs Favorite Starting Pitcher",
    "Opponent Batting Average vs Underdog Starting Pitcher",
    "Favorite Starting Pitcher At Bats Against",
    "Underdog Starting Pitcher At Bats Against",
    "Favorite Bullpen Earned Run Average",
    "Underdog Bullpen Earned Run Average",
    "Favorite Bullpen Walks and Hits per Inning Pitched",
    "Underdog Bullpen Walks and Hits per Inning Pitched",
    "Favorite Bullpen Innings Pitched",
    "Underdog Bullpen Innings Pitched",
    "Favorite Bullpen At Bats Faced per Inning",
    "Underdog Bullpen At Bats Faced per Inning",
    "Favorite Bullpen Strikeouts",
    "Underdog Bullpen Strikeouts",
    "Favorite Bullpen Strikeouts per At Bat Faced",
    "Underdog Bullpen Strikeouts per At Bat Faced",
    "Favorite Bullpen At Bats Against",
    "Underdog Bullpen At Bats Against",
    "Favorite Team Runs Allowed",
    "Underdog Team Runs Allowed",
    "Favorite Team Runs Allowed per At Bat",
    "Underdog Team Runs Allowed per At Bat",
    "Favorite Team Doubles Allowed",
    "Underdog Team Doubles Allowed",
    "Favorite Team Doubles Allowed per At Bat",
    "Underdog Team Doubles Allowed per At Bat",
    "Favorite Team Triples Allowed",
    "Underdog Team Triples Allowed",
    "Favorite Team Triples Allowed per At Bat",
    "Underdog Team Triples Allowed per At Bat",
    "Favorite Team Home Runs Allowed",
    "Underdog Team Home Runs Allowed",
    "Favorite Team Home Runs Allowed per At Bat",
    "Underdog Team Home Runs Allowed per At Bat",
    "Favorite Team Strikeouts",
    "Underdog Team Strikeouts",
    "Favorite Team Strikeouts per At Bat",
    "Underdog Team Strikeouts per At Bat",
    "Favorite Team Walks Issued",
    "Underdog Team Walks Issued",
    "Favorite Team Walks Issued per At Bat",
    "Underdog Team Walks Issued per At Bat",
    "Favorite Team Hits Allowed",
    "Underdog Team Hits Allowed",
    "Opponent Batting Average Allowed by Favorite Team",
    "Opponent Batting Average Allowed by Underdog Team",
    "Favorite Team At Bats Against",
    "Underdog Team At Bats Against",
    "Favorite Team On Base Percentage Allowed",
    "Underdog Team On Base Percentage Allowed",
    "Favorite Team Slugging Percentage Allowed",
    "Underdog Team Slugging Percentage Allowed",
    "Favorite Team On Base Plus Slugging Allowed",
    "Underdog Team On Base Plus Slugging Allowed",
    "Favorite Team Earned Run Average",
    "Underdog Team Earned Run Average",
    "Favorite Team Innings Pitched",
    "Underdog Team Innings Pitched",
    "Favorite Team Earned Runs Allowed",
    "Underdog Team Earned Runs Allowed",
    "Favorite Team Earned Runs Allowed per At Bat",
    "Underdog Team Earned Runs Allowed per At Bat",
    "Favorite Team Walks and Hits per Inning Pitched",
    "Underdog Team Walks and Hits per Inning Pitched",
    "Favorite Team Batters Faced",
    "Underdog Team Batters Faced",
    "Favorite Team Total Bases Allowed",
    "Underdog Team Total Bases Allowed",
    "Favorite Team Pitches per Inning",
    "Underdog Team Pitches per Inning",
    "Favorite Team Games Finished",
    "Underdog Team Games Finished",
    "Favorite Team Strikeout to Walk Ratio",
    "Underdog Team Strikeout to Walk Ratio",
    "Favorite Team Strikeouts per 9 Innings",
    "Underdog Team Strikeouts per 9 Innings",
    "Favorite Team Walks per 9 Innings",
    "Underdog Team Walks per 9 Innings",
    "Favorite Team Hits Allowed per 9 Innings",
    "Underdog Team Hits Allowed per 9 Innings",
    "Favorite Team Runs Allowed per 9 Innings",
    "Underdog Team Runs Allowed per 9 Innings",
    "Favorite Team Home Runs Allowed per 9 Innings",
    "Underdog Team Home Runs Allowed per 9 Innings",
    "Favorite Team Runs Scored",
    "Underdog Team Runs Scored",
    "Favorite Team Runs Scored per At Bat",
    "Underdog Team Runs Scored per At Bat",
    "Favorite Team Doubles",
    "Underdog Team Doubles",
    "Favorite Team Doubles per At Bat",
    "Underdog Team Doubles per At Bat",
    "Favorite Team Triples",
    "Underdog Team Triples",
    "Favorite Team Triples per At Bat",
    "Underdog Team Triples per At Bat",
    "Favorite Team Home Runs",
    "Underdog Team Home Runs",
    "Favorite Team Home Runs per At Bat",
    "Underdog Team Home Runs per At Bat",
    "Favorite Team Batting Strikeouts",
    "Underdog Team Batting Strikeouts",
    "Favorite Team Batting Strikeouts per At Bat",
    "Underdog Team Batting Strikeouts per At Bat",
    "Favorite Team Walks Drawn",
    "Underdog Team Walks Drawn",
    "Favorite Team Walks Drawn per At Bat",
    "Underdog Team Walks Drawn per At Bat",
    "Favorite Team Hits",
    "Underdog Team Hits",
    "Favorite Team Batting Average",
    "Underdog Team Batting Average",
    "Favorite Team At Bats",
    "Underdog Team At Bats",
    "Favorite Team On Base Percentage",
    "Underdog Team On Base Percentage",
    "Favorite Team Slugging Percentage",
    "Underdog Team Slugging Percentage",
    "Favorite Team On Base Plus Slugging",
    "Underdog Team On Base Plus Slugging",
    "Favorite Team Stolen Bases",
    "Underdog Team Stolen Bases",
    "Favorite Team Total Bases",
    "Underdog Team Total Bases",
    "Favorite Team Runs Batted In",
    "Underdog Team Runs Batted In",
    "Favorite Team Runs Batted In per At Bat",
    "Underdog Team Runs Batted In per At Bat"
]

def fix_column_order():
    """Fix the column order in matchup_data.csv"""
    csv_path = "training-data/bdl-training-set/matchup_data.csv"
    
    print(f"Reading {csv_path}...")
    df = pd.read_csv(csv_path)
    
    print(f"Current columns: {len(df.columns)}")
    print(f"Expected columns: {len(CORRECT_COLUMNS)}")
    
    # Create a new dataframe with the correct column order
    new_df = pd.DataFrame()
    
    # Map old columns to new columns
    column_mapping = {
        "Date": "Date",
        "Fav Team": "Fav Team",
        "Dog Team": "Dog Team",
        "Away": "Away",
        "Home": "Home",
        "Fav Home?": "Fav Home?",
        "Fav Moneyline Odds": "Fav Moneyline Odds",
        "Dog Moneyline Odds": "Dog Moneyline Odds",
        "Spread": "Spread",
        "Fav Spread Odds": "Fav Spread Odds",
        "Dog Spread Odds": "Dog Spread Odds",
        "Fav Score": "Fav Score",
        "Dog Score": "Dog Score",
        "Fav/Dog +/-": "Fav/Dog +/-",
        "Fav Cover?": "Fav Cover?",
        "Fav Win?": "Fav Win?",
        "Away Spread Odds": "Away Spread Odds",
        "Home Spread Odds": "Home Spread Odds",
        "Away Score": "Away Score",
        "Home Score": "Home Score",
        "Home/Away +/-": "Home/Away +/-",
        # Note: Column 21 is empty - will be blank
        "Underdog Starting Pitcher Name": "Underdog Starting Pitcher Name",
        "Favorite Starting Pitcher Name": "Favorite Starting Pitcher Name",  # This was in wrong position
    }
    
    # Copy data for each correct column
    for col in CORRECT_COLUMNS:
        if col == "":
            # Empty column
            new_df[col] = ""
        elif col == "Favorite Starting Pitcher Name":
            # This column doesn't exist in user's spec - skip it
            continue
        elif col in df.columns:
            new_df[col] = df[col]
        else:
            # Column doesn't exist yet, create empty
            new_df[col] = ""
    
    # Save the fixed CSV
    new_df.to_csv(csv_path, index=False)
    print(f"\n✓ Fixed column order. CSV now has {len(new_df.columns)} columns")
    print(f"✓ Saved to {csv_path}")
    
    # Show the game we're interested in
    game_row = new_df[(new_df['Date'] == '2025-08-16') & 
                       (new_df['Away'] == 'SEA') & 
                       (new_df['Home'] == 'NYM')]
    
    if not game_row.empty:
        print(f"\n2025-08-16 SEA @ NYM game:")
        print(f"  Underdog Starting Pitcher: {game_row.iloc[0]['Underdog Starting Pitcher Name']}")
        non_empty = game_row.iloc[0].dropna()
        non_empty = non_empty[non_empty != '']
        print(f"  Populated fields: {len(non_empty)}/{len(CORRECT_COLUMNS)}")

if __name__ == "__main__":
    fix_column_order()
