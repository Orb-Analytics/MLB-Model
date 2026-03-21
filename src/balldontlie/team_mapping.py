"""
Team name mapping for Balldontlie API to current training set format
Handles discrepancies between API and current naming conventions
"""

# Balldontlie team ID to current abbreviation mapping
BALLDONTLIE_ID_TO_ABBREV = {
    1: "ARI",    # Arizona Diamondbacks
    20: "OAK",   # Oakland Athletics
    2: "ATL",    # Atlanta Braves
    3: "BAL",    # Baltimore Orioles
    4: "BOS",    # Boston Red Sox
    5: "CHC",    # Chicago Cubs
    6: "CWS",    # Chicago White Sox (Balldontlie uses CHW, we use CWS)
    7: "CIN",    # Cincinnati Reds
    8: "CLE",    # Cleveland Guardians
    9: "COL",    # Colorado Rockies
    10: "DET",   # Detroit Tigers
    11: "HOU",   # Houston Astros
    12: "KAN",   # Kansas City Royals (some sources use KC, we use KAN)
    13: "LAA",   # Los Angeles Angels
    14: "LAD",   # Los Angeles Dodgers
    15: "MIA",   # Miami Marlins
    16: "MIL",   # Milwaukee Brewers
    17: "MIN",   # Minnesota Twins
    18: "NYM",   # New York Mets
    19: "NYY",   # New York Yankees
    21: "PHI",   # Philadelphia Phillies
    22: "PIT",   # Pittsburgh Pirates
    23: "SD",    # San Diego Padres
    24: "SF",    # San Francisco Giants
    27: "SEA",   # Seattle Mariners
    25: "STL",   # St. Louis Cardinals
    26: "TB",    # Tampa Bay Rays
    28: "TEX",   # Texas Rangers
    29: "TOR",   # Toronto Blue Jays
    30: "WAS",   # Washington Nationals
}

# Balldontlie abbreviation to current abbreviation
# Handle the few cases where they differ
BALLDONTLIE_ABBREV_TO_CURRENT = {
    "ARI": "ARI",
    "OAK": "OAK",
    "ATL": "ATL",
    "BAL": "BAL",
    "BOS": "BOS",
    "CHC": "CHC",
    "CHW": "CWS",  # ⚠️ Key difference
    "CIN": "CIN",
    "CLE": "CLE",
    "COL": "COL",
    "DET": "DET",
    "HOU": "HOU",
    "KC": "KAN",   # ⚠️ Key difference (if Balldontlie uses KC)
    "KAN": "KAN",
    "LAA": "LAA",
    "LAD": "LAD",
    "MIA": "MIA",
    "MIL": "MIL",
    "MIN": "MIN",
    "NYM": "NYM",
    "NYY": "NYY",
    "PHI": "PHI",
    "PIT": "PIT",
    "SD": "SD",
    "SF": "SF",
    "SEA": "SEA",
    "STL": "STL",
    "TB": "TB",
    "TEX": "TEX",
    "TOR": "TOR",
    "WAS": "WAS",
}

# Current abbreviation to full name (for display)
CURRENT_ABBREV_TO_FULL_NAME = {
    "ARI": "Arizona Diamondbacks",
    "ATL": "Atlanta Braves",
    "BAL": "Baltimore Orioles",
    "BOS": "Boston Red Sox",
    "CHC": "Chicago Cubs",
    "CWS": "Chicago White Sox",
    "CIN": "Cincinnati Reds",
    "CLE": "Cleveland Guardians",
    "COL": "Colorado Rockies",
    "DET": "Detroit Tigers",
    "HOU": "Houston Astros",
    "KAN": "Kansas City Royals",
    "LAA": "Los Angeles Angels",
    "LAD": "Los Angeles Dodgers",
    "MIA": "Miami Marlins",
    "MIL": "Milwaukee Brewers",
    "MIN": "Minnesota Twins",
    "NYM": "New York Mets",
    "NYY": "New York Yankees",
    "OAK": "Oakland Athletics",
    "PHI": "Philadelphia Phillies",
    "PIT": "Pittsburgh Pirates",
    "SD": "San Diego Padres",
    "SF": "San Francisco Giants",
    "SEA": "Seattle Mariners",
    "STL": "St. Louis Cardinals",
    "TB": "Tampa Bay Rays",
    "TEX": "Texas Rangers",
    "TOR": "Toronto Blue Jays",
    "WAS": "Washington Nationals",
}

# Reverse mapping for lookups
FULL_NAME_TO_CURRENT_ABBREV = {v: k for k, v in CURRENT_ABBREV_TO_FULL_NAME.items()}


def normalize_team_from_api(team_data):
    """
    Convert Balldontlie team data to current abbreviation format
    
    Args:
        team_data: dict with 'id' and/or 'abbreviation' keys from Balldontlie API
        
    Returns:
        str: Current system abbreviation (e.g., "CWS", "KAN")
    """
    # Try ID mapping first (most reliable)
    if "id" in team_data and team_data["id"] in BALLDONTLIE_ID_TO_ABBREV:
        return BALLDONTLIE_ID_TO_ABBREV[team_data["id"]]
    
    # Fall back to abbreviation mapping
    if "abbreviation" in team_data:
        abbrev = team_data["abbreviation"]
        return BALLDONTLIE_ABBREV_TO_CURRENT.get(abbrev, abbrev)
    
    # Last resort: try display name or full name
    for name_field in ["display_name", "name", "full_name"]:
        if name_field in team_data:
            full_name = team_data[name_field]
            if full_name in FULL_NAME_TO_CURRENT_ABBREV:
                return FULL_NAME_TO_CURRENT_ABBREV[full_name]
    
    # If all else fails, return what we have
    return team_data.get("abbreviation", "UNKNOWN")


def get_full_name(abbrev):
    """Get full team name from current abbreviation"""
    return CURRENT_ABBREV_TO_FULL_NAME.get(abbrev, abbrev)


def validate_team_abbreviation(abbrev):
    """Check if abbreviation is valid in current system"""
    return abbrev in CURRENT_ABBREV_TO_FULL_NAME


# Example usage:
if __name__ == "__main__":
    # Test with some example API responses
    test_cases = [
        {"id": 6, "abbreviation": "CHW", "display_name": "Chicago White Sox"},
        {"id": 12, "abbreviation": "KC", "display_name": "Kansas City Royals"},
        {"id": 27, "abbreviation": "SEA", "display_name": "Seattle Mariners"},
    ]
    
    print("Testing team name normalization:")
    print("-" * 50)
    for team in test_cases:
        current_abbrev = normalize_team_from_api(team)
        full_name = get_full_name(current_abbrev)
        print(f"API: {team['abbreviation']:3} (ID: {team['id']:2}) → Current: {current_abbrev:3} ({full_name})")
    
    print("\n✅ All 30 teams in system:")
    for abbrev in sorted(CURRENT_ABBREV_TO_FULL_NAME.keys()):
        print(f"  {abbrev}: {CURRENT_ABBREV_TO_FULL_NAME[abbrev]}")
