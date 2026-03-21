"""
Add starting pitcher stat columns to matchup_data.csv
"""
import pandas as pd

def add_pitcher_columns():
    """Add skeleton columns for starting pitcher stats"""
    csv_path = "training-data/bdl-training-set/matchup_data.csv"
    
    print(f"Reading {csv_path}...")
    df = pd.read_csv(csv_path)
    
    print(f"Current columns: {len(df.columns)}")
    
    # Define starting pitcher stat columns based on what's available from API
    pitcher_stat_columns = [
        # Basic counting stats
        "Favorite Starting Pitcher Games Started",
        "Underdog Starting Pitcher Games Started",
        "Favorite Starting Pitcher Innings Pitched",
        "Underdog Starting Pitcher Innings Pitched",
        "Favorite Starting Pitcher Wins",
        "Underdog Starting Pitcher Wins",
        "Favorite Starting Pitcher Losses",
        "Underdog Starting Pitcher Losses",
        
        # Core pitching metrics
        "Favorite Starting Pitcher ERA",
        "Underdog Starting Pitcher ERA",
        "Favorite Starting Pitcher WHIP",
        "Underdog Starting Pitcher WHIP",
        
        # Strikeouts and Walks
        "Favorite Starting Pitcher Strikeouts",
        "Underdog Starting Pitcher Strikeouts",
        "Favorite Starting Pitcher Walks",
        "Underdog Starting Pitcher Walks",
        "Favorite Starting Pitcher K/9",
        "Underdog Starting Pitcher K/9",
        "Favorite Starting Pitcher BB/9",
        "Underdog Starting Pitcher BB/9",
        "Favorite Starting Pitcher H/9",
        "Underdog Starting Pitcher H/9",
        "Favorite Starting Pitcher K/BB Ratio",
        "Underdog Starting Pitcher K/BB Ratio",
        
        # Hits and Runs
        "Favorite Starting Pitcher Hits Allowed",
        "Underdog Starting Pitcher Hits Allowed",
        "Favorite Starting Pitcher Runs Allowed",
        "Underdog Starting Pitcher Runs Allowed",
        "Favorite Starting Pitcher Earned Runs",
        "Underdog Starting Pitcher Earned Runs",
        "Favorite Starting Pitcher Home Runs Allowed",
        "Underdog Starting Pitcher Home Runs Allowed",
        
        # Advanced metrics
        "Favorite Starting Pitcher Batters Faced",
        "Underdog Starting Pitcher Batters Faced",
        "Favorite Starting Pitcher Opponent Batting Average",
        "Underdog Starting Pitcher Opponent Batting Average",
        "Favorite Starting Pitcher Pitch Count",
        "Underdog Starting Pitcher Pitch Count",
        "Favorite Starting Pitcher Strikes",
        "Underdog Starting Pitcher Strikes",
        "Favorite Starting Pitcher Wild Pitches",
        "Underdog Starting Pitcher Wild Pitches",
    ]
    
    # Add empty columns for each stat
    for col in pitcher_stat_columns:
        df[col] = ""
    
    # Save the updated CSV
    df.to_csv(csv_path, index=False)
    
    print(f"\n✓ Added {len(pitcher_stat_columns)} pitcher stat columns")
    print(f"✓ Total columns now: {len(df.columns)}")
    print(f"✓ Saved to {csv_path}")
    
    print(f"\nColumns added:")
    print(f"  - Games Started, IP, W-L Record")
    print(f"  - ERA, WHIP")
    print(f"  - K, BB, K/9, BB/9, H/9, K/BB")
    print(f"  - Hits, Runs, ER, HR Allowed")
    print(f"  - Batters Faced, Opponent BA")
    print(f"  - Pitch Count, Strikes, Wild Pitches")
    
    return df

if __name__ == "__main__":
    add_pitcher_columns()
