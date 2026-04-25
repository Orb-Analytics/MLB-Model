"""
Build Player ID Mapping: Balldontlie -> MLB Stats API

This script builds a mapping file that translates balldontlie player IDs
to MLB Stats API player IDs so we can fetch stats from the MLB API.

Uses starting pitcher info files that already have names.
"""

import os
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
import time
import glob

# Load environment
load_dotenv()

# API endpoint
MLB_API_BASE = "https://statsapi.mlb.com/api/v1"

# Directories
STARTING_PITCHER_INFO_DIR = Path("data/bdl_data/starting_pitcher_info")
MAPPING_FILE = Path("data/player_id_mapping.csv")

def load_all_pitcher_info() -> pd.DataFrame:
    """
    Load all starting pitcher info files and extract unique pitcher IDs and names.
    
    Returns:
        DataFrame with columns: bdl_player_id, full_name
    """
    all_pitchers = []
    
    # Find all pitcher info files
    files = glob.glob(str(STARTING_PITCHER_INFO_DIR / "*.csv"))
    
    if not files:
        print("⚠ No starting pitcher info files found")
        return pd.DataFrame(columns=['bdl_player_id', 'full_name'])
    
    print(f"Loading pitcher info from {len(files)} files...")
    
    for file_path in files:
        try:
            df = pd.read_csv(file_path)
            
            # Extract home pitchers
            if 'home_starter_id' in df.columns and 'home_starter_name' in df.columns:
                home_pitchers = df[['home_starter_id', 'home_starter_name']].dropna()
                home_pitchers.columns = ['bdl_player_id', 'full_name']
                all_pitchers.append(home_pitchers)
            
            # Extract away pitchers
            if 'away_starter_id' in df.columns and 'away_starter_name' in df.columns:
                away_pitchers = df[['away_starter_id', 'away_starter_name']].dropna()
                away_pitchers.columns = ['bdl_player_id', 'full_name']
                all_pitchers.append(away_pitchers)
                
        except Exception as e:
            print(f"  ⚠ Error reading {file_path}: {e}")
            continue
    
    if not all_pitchers:
        return pd.DataFrame(columns=['bdl_player_id', 'full_name'])
    
    # Combine and deduplicate
    combined = pd.concat(all_pitchers, ignore_index=True)
    unique_pitchers = combined.drop_duplicates(subset=['bdl_player_id'])
    
    print(f"  ✓ Found {len(unique_pitchers)} unique pitchers")
    
    return unique_pitchers


def search_mlb_player_by_name(full_name: str, position: str = "P") -> int:
    """
    Search for MLB player ID by name.
    
    Args:
        full_name: Player's full name
        position: Player position (to help narrow search)
        
    Returns:
        MLB player ID if found, None otherwise
    """
    # Search endpoint
    url = f"{MLB_API_BASE}/sports/1/players"
    params = {"season": 2025}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            players = data.get("people", [])
            
            # Try exact match first
            for player in players:
                if player.get("fullName", "").lower() == full_name.lower():
                    return player.get("id")
            
            # Try fuzzy match (last name match)
            last_name = full_name.split()[-1].lower() if " " in full_name else full_name.lower()
            matches = []
            
            for player in players:
                player_full = player.get("fullName", "").lower()
                player_last = player_full.split()[-1] if " " in player_full else player_full
                
                if player_last == last_name:
                    matches.append(player)
            
            # If only one match, return it
            if len(matches) == 1:
                return matches[0].get("id")
            
            # If multiple matches and we have position info, try to filter
            if len(matches) > 1 and position:
                for player in matches:
                    player_pos = player.get("primaryPosition", {}).get("abbreviation", "")
                    if position in ["P", "SP", "RP"] and player_pos == "P":
                        return player.get("id")
            
            return None
            
    except Exception as e:
        print(f"  Error searching MLB for {full_name}: {e}")
        return None


def build_mapping(pitchers_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build mapping DataFrame from pitcher info.
    
    Args:
        pitchers_df: DataFrame with columns: bdl_player_id, full_name
    
    Returns:
        DataFrame with columns: balldontlie_id, mlb_id, full_name, status
    """
    mappings = []
    
    print(f"\n🔄 Building mapping for {len(pitchers_df)} pitchers...\n")
    
    for i, row in pitchers_df.iterrows():
        bdl_id = int(row['bdl_player_id'])
        full_name = row['full_name']
        
        print(f"  [{i+1}/{len(pitchers_df)}] {full_name} (BDL ID: {bdl_id})...")
        
        # Search for MLB ID
        mlb_id = search_mlb_player_by_name(full_name, position="P")
        
        if mlb_id:
            print(f"    ✓ Mapped to MLB ID: {mlb_id}")
            status = "success"
        else:
            print(f"    ⚠ No MLB match found")
            status = "no_mlb_match"
        
        mappings.append({
            "balldontlie_id": bdl_id,
            "mlb_id": mlb_id,
            "full_name": full_name,
            "status": status
        })
        
        time.sleep(0.6)  # Rate limiting
    
    return pd.DataFrame(mappings)


def main():
    """Main function to build player ID mapping."""
    print("=" * 80)
    print("BUILDING PLAYER ID MAPPING: Balldontlie -> MLB Stats API")
    print("=" * 80)
    
    # Load all pitcher info from files
    pitchers_df = load_all_pitcher_info()
    
    if pitchers_df.empty:
        print(f"\n⚠ No pitcher data found. Run fetch_starting_pitcher_info.py first.")
        return
    
    # Build mapping
    mapping_df = build_mapping(pitchers_df)
    
    # Report stats
    print("\n" + "=" * 80)
    print("MAPPING RESULTS")
    print("=" * 80)
    print(f"Total pitchers: {len(mapping_df)}")
    print(f"Successfully mapped: {len(mapping_df[mapping_df['status'] == 'success'])}")
    print(f"Failed to map: {len(mapping_df[mapping_df['status'] != 'success'])}")
    
    # Show failed mappings
    failed = mapping_df[mapping_df['status'] != 'success']
    if not failed.empty:
        print(f"\n⚠ Failed mappings ({len(failed)}):")
        for _, row in failed.iterrows():
            print(f"  - {row['full_name']} (BDL ID: {row['balldontlie_id']}, Status: {row['status']})")
    
    # Save mapping
    MAPPING_FILE.parent.mkdir(parents=True, exist_ok=True)
    mapping_df.to_csv(MAPPING_FILE, index=False)
    print(f"\n✅ Mapping saved to: {MAPPING_FILE}")
    
    # Save successful mappings only as a clean file
    success_df = mapping_df[mapping_df['status'] == 'success'][['balldontlie_id', 'mlb_id', 'full_name']]
    clean_file = Path("data/player_id_mapping_clean.csv")
    success_df.to_csv(clean_file, index=False)
    print(f"✅ Clean mapping (success only) saved to: {clean_file}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
