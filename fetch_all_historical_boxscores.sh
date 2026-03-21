#!/bin/bash

# Fetch team boxscores for all historical seasons (2023 down to 2009)

echo "Starting historical boxscore collection"
echo "This will process 15 seasons: 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010, 2009"
echo ""

for year in 2023 2022 2021 2020 2019 2018 2017 2016 2015 2014 2013 2012 2011 2010 2009
do
    echo ""
    echo "=========================================="
    echo "Starting fetch for $year season"
    echo "=========================================="
    python /workspaces/MLB-Model/fetch_boxscores_by_year.py $year
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully completed $year"
    else
        echo "❌ Error processing $year"
    fi
    
    echo ""
    echo "Pausing 5 seconds before next year..."
    sleep 5
done

echo ""
echo "=========================================="
echo "🎉 All historical boxscores collected!"
echo "=========================================="
