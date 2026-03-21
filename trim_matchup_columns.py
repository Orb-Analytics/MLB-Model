"""
Trim matchup_data.csv to keep only basic game info and starting pitcher names
"""
import pandas as pd

def trim_columns():
    """Keep only columns up to and including starting pitcher names"""
    csv_path = "training-data/bdl-training-set/matchup_data.csv"
    
    print(f"Reading {csv_path}...")
    df = pd.read_csv(csv_path)
    
    print(f"Current columns: {len(df.columns)}")
    
    # Define the columns to keep (only fundamental game info + pitcher names)
    columns_to_keep = [
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
        "Favorite Starting Pitcher Name",
        "Underdog Starting Pitcher Name"
    ]
    
    # Keep only the specified columns
    df_trimmed = df[columns_to_keep].copy()
    
    # Save the trimmed CSV
    df_trimmed.to_csv(csv_path, index=False)
    
    print(f"\n✓ Trimmed to {len(df_trimmed.columns)} columns")
    print(f"✓ Saved to {csv_path}")
    
    # Show a sample game
    sample = df_trimmed[(df_trimmed['Date'] == '2025-08-16') & 
                        (df_trimmed['Away'] == 'SEA') & 
                        (df_trimmed['Home'] == 'NYM')]
    
    if not sample.empty:
        print(f"\nSample game (2025-08-16 SEA @ NYM):")
        for col in columns_to_keep:
            if col and col in sample.columns:
                val = sample.iloc[0][col]
                if pd.notna(val) and val != '':
                    print(f"  {col}: {val}")

if __name__ == "__main__":
    trim_columns()
