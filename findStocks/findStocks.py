#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to find new stocks to invest in.

Rules used in these scripts
1. Annual - EPS must increase by 20%
2. Annual - ROE must be over 17%
3. Quarterly - EPS must increase by 20%
4. Quarterly - Sales must increase by 20%
5. Stock price can not be decreasing recently

Additional rules that automatically disqualify stock
2. Foreign currency
3. Recent negative net income
4. Stock price has a decreasing trend
"""

import os
import argparse
import datetime as dt
import pandas as pd
from downloadData import download
from dateutil.relativedelta import relativedelta
from findStocksUtils import (getStockList, findProcessed, saveAll,
                             updateProcessed, makeDirectory, checkDataMatches)
from findStocksClasses import Stock


def last_working_day(given_date):
    while True:
        given_date -= dt.timedelta(days=1)
        if given_date.weekday() not in [5,6]:
            return given_date
        
""" datetime util """
now = dt.datetime.now()
lastday = now + relativedelta(months=0, days=-1)
end_date = last_working_day(now).strftime('%Y-%m-%d')

def getInputs():
    """Parse arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--stock_list', type=str, required=True, help=(
        '.csv file with a column of stock symbols, e.g. Example Stock List.csv'))
    parser.add_argument('--key', type=str, help=(
        'API key for Alpha Vantage'))
    parser.add_argument('--data_folder', type=str, default='Data', help=(
        'Folder with data downloaded from Alpha Vantage'))
    parser.add_argument('--report_folder', type=str, default='Report', help=(
        'Folder with report after processing')) 
    parser.add_argument('--not_flexible', action='store_true', help=(
        'Add argument to manually input data from sec.gov if it is missing'))

    params = vars(parser.parse_args())
    stockFile = params['stock_list']
    apikey = params['key'] if 'key' in params else None
    dataFolder = params['data_folder']
    reportFolder = params['report_folder']
    flexible = not params['not_flexible']
    record = []
    return stockFile, dataFolder, reportFolder, apikey, flexible, record


def getData(stockFile, dataFolder, apikey):
    """Download the data and/or get list of stocks ready for analysis."""
    # Create folders for script to work
    makeDirectory(dataFolder)

    # Use predownloaded data
    if apikey is None:
        checkDataMatches(stockFile, dataFolder)
    # Or download data from Alpha Vantage
    else:
        download(stockFile, dataFolder, apikey)

    # Get stock symbols for downloaded stock data
    allSymbols = getStockList(stockFile)

    # Get stock symbols for unprocessed stock data
    symbols = findProcessed(stockFile, allSymbols)
    
    if symbols != []:
        print('No stocks were found in *_Processed.csv file')

    # final list is used to collect test results
    record = []

    return symbols


def preliminaryTests(stock):
    """Run preliminary tests to see if stock failed and can be skipped."""
    # Perliminary tests to disqualify a stock
    stock.prelimTests()

    # Skip stock if it failed any of the preliminary tests
    if stock.errorMessage != 'processed':
        return

    # Check for negative income
    stock.checkNegativeIncome()

    # Skip stock if it has negative net income
    if stock.errorMessage != 'processed':
        return

    # Check if stock price has been decreasing recently
    stock.checkSlope()

    # Skip stock if it does not have increasing price change
    if stock.errorMessage != 'processed':
        return

    # Reduce income statement and balance sheet into one DF
    stock.reduceDF()


def manageBadData(stock, r):
    """Manage missing data."""
    # Identify missing data
    stock.miss[r] = stock.identifyMissing(stock.reports[r])

    # If user is not flexible, get user input when missing data is encountered
    if not stock.flex:
        stock.reports[r] = stock.getData(stock.reports[r],
                                         stock.miss[r])
    # Otherwise if user is flexible, copy recent data over to missing data
    else:
        stock.reports[r], stock.miss[r] = stock.copy(stock.reports[r],
                                                     stock.miss[r])

    # Change column type to numeric if is object
    stock.reports[r] = stock.checkType(stock.reports[r])

    # Check if shares are missing trailing zeros
    shares = 'commonStockSharesOutstanding'
    stock.reports[r][shares] = stock.checkSmallShares(stock.reports[r][shares])


def analyzeStock(stock, r):
    """Run important tests to determine if quality stock."""
    # Calculate ROE and EPS
    stock.reports[r] = stock.calculate(stock.reports[r])

    # Calculate the percentage change year over year
    stock.reports[r] = stock.percentChange(stock.reports[r], r)

    # Round DF for pretty saving
    stock.reports[r] = stock.roundReports(stock.reports[r])

    # Check the percentage change year over year
    stock.test(stock.reports[r], r)

    if r == 'q':
        # Calculate the average of the percent changes
        stock.averagePercentChange(stock.reports[r])


def saveResults(stock, s, stockFile, record):
    """Save results after processing stock."""
    # Save stock information
    stock.save()

    # Update the processed file
    updateProcessed(stockFile, s, stock.errorMessage)

    # Append record to later save
    record.append([x for x in stock.record.values()])

    return record
        

if __name__ == '__main__':

    # Get user inputs
    stockFile, dataFolder, reportFolder, apikey, flexible, record = getInputs()

    # Get financial report data
    symbols = getData(stockFile, dataFolder, apikey)
    if len(symbols) > 0:

        # Make the Processed directory
        processedDir = "data/Processed"
        if not os.path.exists(processedDir):
            makeDirectory(processedDir)
            
        # Loop through all stocks
        for s in symbols:
            print('>>>', s)

            # Initialize Stock object
            stock = Stock(s, dataFolder, flexible)

            # Run preliminary tests to check if stock is disqualified
            preliminaryTests(stock)

            # Skip stock if it failed preliminary tests. Update the *Processed.csv
            if stock.errorMessage != 'processed':
                updateProcessed(stockFile, s, stock.errorMessage)
                continue

            for r in stock.reports:
                try: 
                    # Manage missing data and other inconsistencies in data
                    manageBadData(stock, r)

                    # Calculate new metrics and run stock tests
                    analyzeStock(stock, r)
                except Exception as e:
                    print(e)                

            # Save data and update files
            record = saveResults(stock, s, stockFile, record)

        # Assert can occur when all stocks fail preliminary tests
        if record != []:
            print('No procssed stocks to save to *Results.csv')

        # Save the test results for all stocks
        columns = [x for x in stock.record.keys()]
        
        makeDirectory(reportFolder)
        saveAll(reportFolder, record, columns)
        
    # In addition, save most attractive stocks that passed the test below
    """
    Check if stocks pass percent change tests.

    1. Annual - EPS must increase by 20%
    2. Annual - ROE must be over 17%
    3. Quarterly - EPS must increase by 20%
    4. 
    Quarterly - Sales must increase by 20%
    """
    
    data_dir = "./data"
    input_file = f"{data_dir}/SP500_{end_date}_Processed.csv"

    """ Load from CSV """
    df = pd.read_csv(input_file)

    df_failed = df[df["Processed"] != "processed"]
    df_processed = df[df["Processed"].astype(str).str.contains("processed|processed_copied")] 

    report_dir = "./report"
    output_file = f"{report_dir}/{now.strftime('%Y-%m-%d')} Financial Analysis Results.csv"

    """ Load from CSV """
    df = pd.read_csv(output_file)

    df_candidates = df[df["numfailed"] < 1].sort_values(by=['slope'], ascending=False, axis=0)
    df_candidates = df_candidates[["stock", "slope", "avgpc" ]]
    df_candidates.to_csv(f"{report_dir}/most_attractives_{end_date}.csv", index=False)

    print(f"total: {len(df)} \n---------------------\nfailed: {len(df_failed)} \nprocessed: {len(df_processed)}")

    print("\n---------------------\nPlease find the report directory")
    print(f"total candidates: {len(df_candidates)}")
    df_candidates[["stock", "avgpc", "slope",]]
