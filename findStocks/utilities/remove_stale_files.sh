#!/bin/bash
echo "Cleaning up files so stock-search can run again.."

echo "Removing processed symbol-states file.."
rm -f ./data/*_Processed.csv
rm -f ./data/Processed

echo "Removing results file.."
date=$(date '+%Y-%m-%d')
rm -f f"report/${date} Financial Analysis Results.csv" 



