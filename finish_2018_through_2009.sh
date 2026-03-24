#!/bin/bash
# Finish remaining starting pitcher boxscores for 2018-2009

echo "==================================================================="
echo "Finishing MLB Starting Pitcher Boxscores (2018-2009)"
echo "==================================================================="
echo ""

# Run each remaining year sequentially (2018 down to 2009)
for year in 2018 2017 2016 2015 2014 2013 2012 2011 2010 2009; do
    echo "-------------------------------------------------------------------"
    echo "Starting year: $year"
    echo "-------------------------------------------------------------------"
    
    python /workspaces/MLB-Model/fetch_starting_pitcher_boxscores_by_year.py $year
    
    file_count=$(ls /workspaces/MLB-Model/data/${year}_data/mlb_data/raw/starting_pitcher_boxscores/ 2>/dev/null | wc -l)
    expected=$(ls /workspaces/MLB-Model/data/${year}_data/mlb_data/raw/boxscores/ 2>/dev/null | wc -l)
    latest=$(ls /workspaces/MLB-Model/data/${year}_data/mlb_data/raw/starting_pitcher_boxscores/ 2>/dev/null | tail -1)
    echo ""
    echo "✅ Completed $year: $file_count / $expected files (latest: $latest)"
    echo ""
    sleep 3
done

echo "==================================================================="
echo "ALL STARTING PITCHER COLLECTIONS COMPLETE!"
echo "==================================================================="
echo ""
echo "Final Summary (All Years 2009-2023):"
for year in {2009..2023}; do
  count=$(ls /workspaces/MLB-Model/data/${year}_data/mlb_data/raw/starting_pitcher_boxscores/ 2>/dev/null | wc -l)
  expected=$(ls /workspaces/MLB-Model/data/${year}_data/mlb_data/raw/boxscores/ 2>/dev/null | wc -l)
  if [ $count -eq $expected ]; then
    echo "  ✅ $year: $count / $expected files"
  else
    echo "  ⚠️  $year: $count / $expected files"
  fi
done
echo ""
total=$(find /workspaces/MLB-Model/data/*/mlb_data/raw/starting_pitcher_boxscores/ -name "*.csv" 2>/dev/null | wc -l)
echo "Total starting pitcher files: $total"
