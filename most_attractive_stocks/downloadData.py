#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Download stock ticker data using Alpha Vantage."""
import json
from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime
import time
import sys
import os
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


def getData(s, folder, key):
    """Download data using API."""
    i = gather(s, 'INCOME_STATEMENT', key)
    b = gather(s, 'BALANCE_SHEET', key)
    time.sleep(0.5)

    assert 'Information' not in i.keys(), (
        'Max number of API calls reached for the day: 500 calls.')

    if (
            i == {}
            or b == {}
            or list(i.keys()) == ['Error Message']
            or list(b.keys()) == ['Error Message']
            or b['annualReports'] == []
            or i['annualReports'] == []
            ):
        return 'API failed'

    dfIncomeQuarterly = pd.DataFrame.from_dict(i['quarterlyReports'])
    dfIncomeAnnual = pd.DataFrame.from_dict(i['annualReports'])
    dfBalanceQuarterly = pd.DataFrame.from_dict(b['quarterlyReports'])
    dfBalanceAnnual = pd.DataFrame.from_dict(b['annualReports'])

    dateq = dfIncomeQuarterly.iloc[0, 0]
    datea = dfIncomeAnnual.iloc[0, 0]
    dateqdt = datetime.strptime(dateq, '%Y-%m-%d')
    dateadt = datetime.strptime(datea, '%Y-%m-%d')

    # Choose the more recent date for the filename
    date = dateq if dateqdt > dateadt else datea

    saveFile(s, date, 'Quarterly Income Statement', dfIncomeQuarterly, folder)
    saveFile(s, date, 'Annual Income Statement', dfIncomeAnnual, folder)
    saveFile(s, date, 'Quarterly Balance Sheet', dfBalanceQuarterly, folder)
    saveFile(s, date, 'Annual Balance Sheet', dfBalanceAnnual, folder)

    return 'no issues'


def saveFile(s, date, fileType, df, folder):
    """Return path to save file."""
    f = s + ' ' + date + ' ' + fileType + '.csv'
    path = os.path.join(folder, f)
    df.to_csv(path, index=False)


def reset():
    """Reset the counter to wait for limited API use."""
    count = 0
    seconds = 60
    earlier = datetime.now()
    return count, seconds, earlier


def gather(s, reportType, key):
    """Parse HTML."""
    apikey = key
    baseurl = 'https://www.alphavantage.co/query?function='
    response = requests.get(baseurl + reportType + '&symbol=' + s + '&apikey=' + apikey)
    soup = BeautifulSoup(response.content, 'html.parser')
    return json.loads(str(soup))


def download(file, dataFolder, apikey):
    """Download stock ticker data using Alpha Vantage."""
    dfStocks = pd.read_csv(file)

    assert 'Symbol' in dfStocks.columns, 'Symbol column is not in stock list'

    assert type(dfStocks.loc[len(dfStocks) - 1, 'Symbol']) is str, (
        'The last row does not have a symbol. Make sure last row is not blank.')

    # If first time opening file, add column of all zeros
    if 'Downloaded' not in dfStocks.columns:
        dfStocks['Downloaded'] = 0

    if all(dfStocks['Downloaded'] != 0):
        print('All symbols in stock list have been downloaded, i.e. downloaded'
              ' column is all 1s or -1s')
        return

    count, seconds, earlier = reset()

    i = 0
    # Alpha Vantage API download limit of 500 files has been reached
    while i < len(dfStocks) and i < 500:
        # Check to see if already downloaded
        # 1: downloaded, -1: error downloading
        if dfStocks.loc[i, 'Downloaded'] in {-1, 1}:
            i += 1
            continue

        # Wait for API to allow download
        while count == 4 and (datetime.now() - earlier).seconds < 60:
            # Alpha Vantage has a limit as to how many API requests you can do
            # in a minute
            sys.stdout.write('\rWaiting for API to reset. Time remaining: '
                             + str(seconds) + 's')
            seconds -= 5
            time.sleep(5)

        # Reset the timer
        if count == 4:
            print()
            count, seconds, earlier = reset()
            dfStocks.to_csv(file, index=False)

        stock = dfStocks.loc[i, 'Symbol']
        print('Downloading ' + stock + '. Index: ' + str(i))

        # Get data ============================================================
        returned = getData(stock, dataFolder, apikey)

        if returned != 'no issues':
            print('Error message: ' + returned + '. Skipping')
            dfStocks.loc[i, 'Downloaded'] = '-1'
        else:
            dfStocks.loc[i, 'Downloaded'] = 1

        count += 2
        i += 1

    dfStocks.to_csv(file, index=False)
