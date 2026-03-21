#!/bin/bash

# Fetch team boxscores for remaining historical seasons (2014 down to 2009)

echo "Starting historical boxscore collection from 2014 to 2009"
echo "This will process 6 seasons: 2014, 2013, 2012, 2011, 2010, 2009"
echo ""

for year in 2014 2013 2012 2011 2010 2009
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
echo "🎉 All 2014-2009 boxscores collected!"
echo "=========================================="
