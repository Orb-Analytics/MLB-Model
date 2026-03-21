import pandas as pd
import re

def extract_metric_base(col):
    """Extract the base metric name without home/away prefix and rolling suffix."""
    # Remove home_ or away_ prefix
    if col.startswith('home_'):
        base = col[5:]
    elif col.startswith('away_'):
        base = col[5:]
    else:
        return None, None, None
    
    # Check for rolling suffix
    rolling_5_match = re.search(r'_rolling_5$', base)
    rolling_10_match = re.search(r'_rolling_10$', base)
    
    if rolling_5_match:
        metric_base = base[:rolling_5_match.start()]
        return metric_base, 'rolling_5', 'home' if col.startswith('home_') else 'away'
    elif rolling_10_match:
        metric_base = base[:rolling_10_match.start()]
        return metric_base, 'rolling_10', 'home' if col.startswith('home_') else 'away'
    else:
        return base, 'season', 'home' if col.startswith('home_') else 'away'

def group_metrics(columns, metadata_cols):
    """Group columns by metric with home/away alternating and rolling stats together."""
    # Separate metadata and metric columns
    metric_cols = [col for col in columns if col not in metadata_cols]
    
    # Parse all metric columns
    metric_info = {}
    for col in metric_cols:
        base, stat_type, team = extract_metric_base(col)
        if base is None:
            continue
        
        if base not in metric_info:
            metric_info[base] = {
                'home_season': None,
                'away_season': None,
                'home_rolling_5': None,
                'away_rolling_5': None,
                'home_rolling_10': None,
                'away_rolling_10': None,
                'order': len(metric_info)  # Preserve original order of first appearance
            }
        
        key = f"{team}_{stat_type}"
        metric_info[base][key] = col
    
    # Build ordered column list
    ordered_metrics = []
    for base in sorted(metric_info.keys(), key=lambda x: metric_info[x]['order']):
        info = metric_info[base]
        # Add in order: home_season, away_season, home_r5, away_r5, home_r10, away_r10
        for col_key in ['home_season', 'away_season', 'home_rolling_5', 'away_rolling_5', 'home_rolling_10', 'away_rolling_10']:
            if info[col_key]:
                ordered_metrics.append(info[col_key])
    
    return list(metadata_cols) + ordered_metrics

def reorder_team_stats():
    """Reorder team stats CSV."""
    print("\n=== Reordering team stats ===")
    df = pd.read_csv('/workspaces/MLB-Model/data/2025_dataset/joining/2025_team_stats.csv')
    
    # Define metadata columns
    metadata_cols = [
        'balldontlie_game_id', 'id', 'date',
        'home_team_id', 'away_team_id',
        'home_team_abbreviation', 'away_team_abbreviation',
        'home_team_display_name', 'away_team_display_name',
        'home_team_name', 'away_team_name',
        'home_postseason', 'away_postseason',
        'home_season_type', 'away_season_type',
        'home_season', 'away_season',
        'home_gp', 'away_gp'
    ]
    
    # Get new column order
    new_order = group_metrics(df.columns.tolist(), metadata_cols)
    
    # Reorder
    df_reordered = df[new_order]
    
    # Save
    df_reordered.to_csv('/workspaces/MLB-Model/data/2025_dataset/joining/2025_team_stats.csv', index=False)
    print(f"✓ Reordered {len(df_reordered)} rows × {len(df_reordered.columns)} columns")
    print(f"  First 10 metric columns: {new_order[len(metadata_cols):len(metadata_cols)+10]}")
    print(f"  Last 10 columns: {new_order[-10:]}")

def reorder_starting_pitchers():
    """Reorder starting pitchers CSV."""
    print("\n=== Reordering starting pitchers ===")
    df = pd.read_csv('/workspaces/MLB-Model/data/2025_dataset/joining/2025_starting_pitchers.csv')
    
    # Define metadata columns
    metadata_cols = [
        'balldontlie_game_id', 'id', 'date',
        'home_starter_id', 'away_starter_id',
        'home_starter_full_name', 'away_starter_full_name',
        'home_starter_team_id', 'away_starter_team_id',
        'home_starter_team_abbreviation', 'away_starter_team_abbreviation',
        'home_starter_season', 'away_starter_season',
        'home_starter_postseason', 'away_starter_postseason',
        'home_starter_season_type', 'away_starter_season_type',
        'home_starter_pitching_gp', 'away_starter_pitching_gp',
        'home_starter_pitching_gs', 'away_starter_pitching_gs'
    ]
    
    # Get new column order
    new_order = group_metrics(df.columns.tolist(), metadata_cols)
    
    # Reorder
    df_reordered = df[new_order]
    
    # Save
    df_reordered.to_csv('/workspaces/MLB-Model/data/2025_dataset/joining/2025_starting_pitchers.csv', index=False)
    print(f"✓ Reordered {len(df_reordered)} rows × {len(df_reordered.columns)} columns")
    print(f"  First 10 metric columns: {new_order[len(metadata_cols):len(metadata_cols)+10]}")
    print(f"  Last 10 columns: {new_order[-10:]}")

def reorder_bullpen_stats():
    """Reorder bullpen stats CSV."""
    print("\n=== Reordering bullpen stats ===")
    df = pd.read_csv('/workspaces/MLB-Model/data/2025_dataset/joining/2025_bullpen_stats.csv')
    
    # Define metadata columns
    metadata_cols = ['game_pk']
    
    # Get new column order
    new_order = group_metrics(df.columns.tolist(), metadata_cols)
    
    # Reorder
    df_reordered = df[new_order]
    
    # Save
    df_reordered.to_csv('/workspaces/MLB-Model/data/2025_dataset/joining/2025_bullpen_stats.csv', index=False)
    print(f"✓ Reordered {len(df_reordered)} rows × {len(df_reordered.columns)} columns")
    print(f"  First 10 metric columns: {new_order[len(metadata_cols):len(metadata_cols)+10]}")
    print(f"  Last 10 columns: {new_order[-10:]}")

if __name__ == '__main__':
    print("Reordering columns to group metrics with alternating home/away...")
    print("Pattern: home_metric, away_metric, home_metric_r5, away_metric_r5, home_metric_r10, away_metric_r10")
    
    reorder_team_stats()
    reorder_starting_pitchers()
    reorder_bullpen_stats()
    
    print("\n✓ All files reordered successfully!")
