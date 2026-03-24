#!/bin/bash
# Fetch boxscores for years 2010-2015 sequentially

echo "==================================================="
echo "Fetching MLB Team Boxscores for 2010-2015"
echo "==================================================="
echo ""

# Wait for 2009 to finish
echo "Checking if 2009 collection is complete..."
while pgrep -f "fetch_boxscores_by_year.py 2009" > /dev/null; do
    file_count=$(ls /workspaces/MLB-Model/data/2009_data/mlb_data/raw/boxscores/ | wc -l)
    echo "  2009 still running... ($file_count files so far)"
    sleep 30
done

file_count=$(ls /workspaces/MLB-Model/data/2009_data/mlb_data/raw/boxscores/ | wc -l)
echo "✅ 2009 collection complete! ($file_count files)"
echo ""

# Run each year sequentially
for year in 2010 2011 2012 2013 2014 2015; do
    echo "---------------------------------------------------"
    echo "Starting year: $year"
    echo "---------------------------------------------------"
    python /workspaces/MLB-Model/fetch_boxscores_by_year.py $year
    
    file_count=$(ls /workspaces/MLB-Model/data/${year}_data/mlb_data/raw/boxscores/ | wc -l)
    echo ""
    echo "✅ Completed $year: $file_count files"
    echo ""
    sleep 5
done

echo "==================================================="
echo "All years (2010-2015) complete!"
echo "==================================================="
