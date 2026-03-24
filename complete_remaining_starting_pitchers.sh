#!/bin/bash
# Complete remaining starting pitcher boxscores for 2021 and 2020-2009

echo "==================================================================="
echo "Completing Remaining MLB Starting Pitcher Boxscores"
echo "==================================================================="
echo ""

# Run each remaining year sequentially (2021 down to 2009)
for year in 2021 2020 2019 2018 2017 2016 2015 2014 2013 2012 2011 2010 2009; do
    echo "-------------------------------------------------------------------"
    echo "Starting year: $year"
    echo "-------------------------------------------------------------------"
    
    python /workspaces/MLB-Model/fetch_starting_pitcher_boxscores_by_year.py $year
    
    file_count=$(ls /workspaces/MLB-Model/data/${year}_data/mlb_data/raw/starting_pitcher_boxscores/ 2>/dev/null | wc -l)
    latest=$(ls /workspaces/MLB-Model/data/${year}_data/mlb_data/raw/starting_pitcher_boxscores/ 2>/dev/null | tail -1)
    echo ""
    echo "✅ Completed $year: $file_count files (latest: $latest)"
    echo ""
    sleep 3
done

echo "==================================================================="
echo "All remaining years complete!"
echo "==================================================================="
echo ""
echo "Final Summary:"
for year in {2009..2023}; do
  count=$(ls /workspaces/MLB-Model/data/${year}_data/mlb_data/raw/starting_pitcher_boxscores/ 2>/dev/null | wc -l)
  if [ $count -gt 0 ]; then
    echo "  $year: $count files"
  else
    echo "  $year: 0 files"
  fi
done
