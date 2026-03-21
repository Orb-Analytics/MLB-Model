#!/bin/bash

# Fetch starting pitcher boxscores for all historical seasons (2023 down to 2009)

echo "Starting historical starting pitcher boxscore collection"
echo "This will process 15 seasons: 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010, 2009"
echo ""

for year in 2023 2022 2021 2020 2019 2018 2017 2016 2015 2014 2013 2012 2011 2010 2009
do
    echo ""
    echo "=========================================="
    echo "Starting fetch for $year starting pitchers"
    echo "=========================================="
    python /workspaces/MLB-Model/fetch_starting_pitcher_boxscores_by_year.py $year
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully completed $year starting pitchers"
    else
        echo "❌ Error processing $year starting pitchers"
    fi
    
    echo ""
    echo "Pausing 5 seconds before next year..."
    sleep 5
done

echo ""
echo "=========================================="
echo "🎉 All historical starting pitcher boxscores collected!"
echo "=========================================="
