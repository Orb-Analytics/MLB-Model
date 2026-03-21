"""
Fix the pitcher assignments for the 2025-08-16 SEA @ NYM game
Bryan Woo (SEA) should be Underdog SP
Nolan McLean (NYM) should be Favorite SP
"""
import pandas as pd

def fix_pitcher_assignments():
    csv_path = "training-data/bdl-training-set/matchup_data.csv"
    df = pd.read_csv(csv_path)
    
    # Find the game
    game_row_idx = df[(df['Date'] == '2025-08-16') & 
                      (df['Away'] == 'SEA') & 
                      (df['Home'] == 'NYM')].index[0]
    
    print(f"Fixing game at row {game_row_idx}")
    print(f"Favorite Team: NYM, Underdog Team: SEA")
    print(f"Current assignments are BACKWARDS - swapping...")
    
    # Swap the pitcher names
    df.at[game_row_idx, 'Favorite Starting Pitcher Name'] = 'Nolan McLean'
    df.at[game_row_idx, 'Underdog Starting Pitcher Name'] = 'Bryan Woo'
    
    # Get all pitcher stat columns
    fav_cols = [col for col in df.columns if col.startswith('Favorite Starting Pitcher') and col != 'Favorite Starting Pitcher Name']
    dog_cols = [col for col in df.columns if col.startswith('Underdog Starting Pitcher') and col != 'Underdog Starting Pitcher Name']
    
    # Swap all the stats
    for fav_col, dog_col in zip(fav_cols, dog_cols):
        fav_val = df.at[game_row_idx, fav_col]
        dog_val = df.at[game_row_idx, dog_col]
        
        df.at[game_row_idx, fav_col] = dog_val
        df.at[game_row_idx, dog_col] = fav_val
    
    # Save
    df.to_csv(csv_path, index=False)
    
    print(f"\n✓ Fixed pitcher assignments")
    print(f"  Favorite SP (NYM): Nolan McLean - No prior stats (season debut)")
    print(f"  Underdog SP (SEA): Bryan Woo - 28 GS, 3.21 ERA, 1.006 WHIP")

if __name__ == "__main__":
    fix_pitcher_assignments()
