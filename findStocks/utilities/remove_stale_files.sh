#!/bin/bash
echo "Cleaning up files so stock-search can run again.."

echo "Removing processed symbol-states file.."
rm -f ./*_Processed.csv

echo "Removing results file.."
date=$(date '+%Y-%m-%d')
rm -f "${date} Results.csv" 



