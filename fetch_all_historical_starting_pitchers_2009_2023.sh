#!/bin/bash
# Fetch starting pitcher boxscores for years 2009-2023

echo "==================================================================="
echo "Fetching MLB Starting Pitcher Boxscores for 2009-2023"
echo "==================================================================="
echo ""

# Run each year sequentially (2023 down to 2009 for most recent first)
for year in 2023 2022 2021 2020 2019 2018 2017 2016 2015 2014 2013 2012 2011 2010 2009; do
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
echo "All years (2009-2023) complete!"
echo "==================================================================="
echo ""
echo "Final Summary:"
for year in {2009..2023}; do
  count=$(ls /workspaces/MLB-Model/data/${year}_data/mlb_data/raw/starting_pitcher_boxscores/ 2>/dev/null | wc -l)
  if [ $count -gt 0 ]; then
    latest=$(ls /workspaces/MLB-Model/data/${year}_data/mlb_data/raw/starting_pitcher_boxscores/ 2>/dev/null | tail -1)
    echo "  $year: $count files"
  else
    echo "  $year: 0 files"
  fi
done
