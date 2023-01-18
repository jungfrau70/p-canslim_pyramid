#!/usr/bin/env python3
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

import argparse
from downloadData import download
from findStocksUtils import (getStockList, findProcessed, saveAll,
                             updateProcessed, makeDirectory, checkDataMatches)
from findStocksClasses import Stock
from concurrent import futures

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
    record = []
    return stockFile, dataFolder, apikey, flexible, record


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

    assert symbols != [], 'No stocks were found in *_Processed.csv file'

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

def testStock(s, dataFolder, flexible):
    print('>>>', s)
    
    try:
        # Initialize Stock object
        stock = Stock(s, dataFolder, flexible)

        # Run preliminary tests to check if stock is disqualified
        preliminaryTests(stock)

        # Skip stock if it failed preliminary tests. Update the *Processed.csv
        if stock.errorMessage != 'processed':
            updateProcessed(stockFile, s, stock.errorMessage)

        for r in stock.reports:
            # Manage missing data and other inconsistencies in data
            manageBadData(stock, r)

            # Calculate new metrics and run stock tests
            analyzeStock(stock, r)

        # Save data and update files
        record = saveResults(stock, s, stockFile, record)
        print("returned")
        return record
    except Exception as e:
        print(e)
        pass


if __name__ == '__main__':

    import time

    # Get user inputs
    stockFile, dataFolder, apikey, flexible, record = getInputs()

    apikey = "P6QVC3IFRGHVKGAN"
    dataFolder = "./data"

    # Get financial report data
    symbols = getData(stockFile, dataFolder, apikey)

    st = time.time()
    # Option1) MultiTreading
    # in case a smaller number of stocks than threads was passed in
    max_workers = 2
    workers = min(max_workers, len(symbols))

    # with futures.ThreadPoolExecutor(workers) as executor:
    #     for number, record in zip(symbols, executor.map(testStock, symbols, dataFolder, flexible)):
    #         print('%d is record: %s' % (number, record))
            
    # Option2) MultiProcessing
    with futures.ProcessPoolExecutor() as executor:
        for stock, record in zip(symbols, executor.map(testStock, symbols, dataFolder, flexible)):
            # Assert can occur when all stocks fail preliminary tests
            assert record != [], 'No procssed stocks to save to *Results.csv'

            # Save the test results for all stocks
            columns = [x for x in stock.record.keys()]            
            
    et = time.time() - st

    print(f'Time: {et}')
    # Assert can occur when all stocks fail preliminary tests

    

