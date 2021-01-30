#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to find new stocks to invest in.

CAN SLIM Rules

Rules - Quarterly
1. Aim for EPS 25-30% growth
2. Earnings growth should accelerate sometime in the 10 quarters before
3. Sales should grow by at least 25% (grossProfit)

Rules - Annual
1. EPS increased in each of the last three years (25-50% from last year)
2. Return on equity of 17% or more.

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

import argparse
from downloadData import download
from findStocksUtils import (getStockList, findProcessed, saveResults,
                             updateProcessed, makeDirectory, checkDataMatches)
from findStocksClasses import Stock


def getInputs():
    """Parse arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--stock_list', type=str, required=True, help=(
        '.csv file with a column of stock symbols, e.g. Example Stock List.csv'))
    parser.add_argument('--key', type=str, help=(
        'API key for Alpha Vantage'))
    parser.add_argument('--data_folder', type=str, default='Data', help=(
        'Folder with data downloaded from Alpha Vantage'))
    parser.add_argument('--not_flexible', action='store_true', help=(
        'Add argument to manually input data from sec.gov if it is missing'))

    params = vars(parser.parse_args())
    stockFile = params['stock_list']
    apikey = params['key'] if 'key' in params else None
    dataFolder = params['data_folder']
    flexible = not params['not_flexible']
    return stockFile, dataFolder, apikey, flexible


def availableData(stockFile, dataFolder, apikey):
    """Download the data and/or get list of stocks ready for analysis."""
    # Create folders for script to work
    makeDirectory(dataFolder)

    # User can create their own data folder -assuming not using Alpha
    # Vantage- in which case need column of downloaded in stock list.csv
    if apikey is None:
        checkDataMatches(stockFile, dataFolder)
    else:
        download(stockFile, dataFolder, apikey)

    # Get stock symbols for downloaded stock data
    allSymbols = getStockList(stockFile)

    # Get stock symbols for unprocessed stock data
    symbols = findProcessed(stockFile, allSymbols)

    assert symbols != [], 'No stocks were found in *_Processed.csv file'

    # final list is used to collect test results
    record = []

    return symbols, record


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

    # Reduce income statement and balance sheet into on DF
    stock.reduceDF()


def manageMissingData(stock, r):
    """Manage missing data."""
    # Identify missing data
    stock.miss[r] = stock.identifyMissing(stock.reports[r])

    if not stock.flex:
        stock.reports[r] = stock.getData(stock.reports[r],
                                         stock.miss[r])
    else:
        # Copy recent data to missing data
        stock.reports[r], stock.miss[r] = stock.copy(stock.reports[r],
                                                     stock.miss[r])

    # Change column type to numeric if was object
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


def updateFiles(stock, s, stockFile, record):
    """Save results after processing stock."""
    # Save stock information
    stock.save()

    # Update the processed file
    updateProcessed(stockFile, s, stock.errorMessage)

    # Append record to later save
    record.append([x for x in stock.record.values()])
    return record


if __name__ == '__main__':

    stockFile, dataFolder, apikey, flexible = getInputs()
    symbols, record = availableData(stockFile, dataFolder, apikey)

    for s in symbols:
        print('>>>', s)
        stock = Stock(s, dataFolder, flexible)
        preliminaryTests(stock)

        # Skip stock if it failed preliminary tests
        if stock.errorMessage != 'processed':
            updateProcessed(stockFile, s, stock.errorMessage)
            continue

        for r in stock.reports:
            manageMissingData(stock, r)
            analyzeStock(stock, r)

        record = updateFiles(stock, s, stockFile, record)

    assert record != [], 'No procssed stocks to save to *Results.csv'

    # Save the test results
    columns = [x for x in stock.record.keys()]
    saveResults(record, columns)
