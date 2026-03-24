#!/bin/bash
# Complete boxscore collection for remaining years

echo "==================================================="
echo "Completing Boxscore Collection for 2011-2015"
echo "==================================================="
echo ""

# Years to complete: 2011 (partial), 2012 (not started), 2013 (partial), 2015 (partial)
for year in 2011 2012 2013 2015; do
    existing_count=$(ls /workspaces/MLB-Model/data/${year}_data/mlb_data/raw/boxscores/ 2>/dev/null | wc -l)
    echo "---------------------------------------------------"
    echo "Year $year: Starting (currently $existing_count files)"
    echo "---------------------------------------------------"
    
    python /workspaces/MLB-Model/fetch_boxscores_by_year.py $year
    
    final_count=$(ls /workspaces/MLB-Model/data/${year}_data/mlb_data/raw/boxscores/ 2>/dev/null | wc -l)
    latest=$(ls /workspaces/MLB-Model/data/${year}_data/mlb_data/raw/boxscores/ | tail -1)
    echo ""
    echo "✅ Completed $year: $final_count files (latest: $latest)"
    echo ""
    sleep 5
done

echo "==================================================="
echo "All remaining years complete!"
echo "==================================================="
echo ""
echo "Final Summary:"
for year in 2009 2010 2011 2012 2013 2014 2015; do
  count=$(ls /workspaces/MLB-Model/data/${year}_data/mlb_data/raw/boxscores/ 2>/dev/null | wc -l)
  latest=$(ls /workspaces/MLB-Model/data/${year}_data/mlb_data/raw/boxscores/ 2>/dev/null | tail -1)
  echo "  $year: $count files (latest: $latest)"
done
