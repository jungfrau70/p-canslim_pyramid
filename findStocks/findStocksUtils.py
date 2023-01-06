#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Miscellaneous utilities."""
import pandas as pd
import numpy as np
from datetime import date
import os


def checkDataMatches(stockFile, dataFolder):
    """
    Check data matches from list of stocks and data folder.

    If the user has data already downloaded (not using API) then need to update
    the Downloaded column with respect to the downloaded data. This is a
    necessary step becasue scripts will only analyze stocks with a Download
    value of 1
    """
    df = pd.read_csv(stockFile)
    df['Downloaded'] = -1

    # Find symbols of all data already downloaded
    symbolsData = []
    files = os.listdir(dataFolder)
    for f in files:
        if f.endswith('.csv'):
            symbolsData.append(f.split(' ')[0])
    symbolsData = list(set(symbolsData))

    # Update downloaded column
    for s in symbolsData:
        i = df[df['Symbol'] == s].index.item()
        df.loc[i, 'Downloaded'] = 1

    df.to_csv(stockFile, index=False)


def getStockList(f):
    """Get stock symbols for downloaded stock data."""
    df = pd.read_csv(f)
    indeces = df[df['Downloaded'] == 1].index.tolist()
    return df[df.index.isin(indeces)]['Symbol'].tolist()


def findProcessed(f, s):
    """Get stock symbols for unprocessed stock data."""
    f = f.rstrip('.csv') + '_Processed.csv'

    # If processed file exists load it
    if os.path.exists(f):
        df = pd.read_csv(f)
        # If additional stocks data has been downloaded and is not part of
        # processed file then concatenate and save
        if len(df) != len(s):
            lastStock = df.iloc[-1, 0]
            startIndex = s.index(lastStock) + 1
            s = s[startIndex:]
            d = {'Symbol': s, 'Processed': ['not processed'] * len(s)}
            df2 = pd.DataFrame(data=d)
            df = pd.concat([df, df2], ignore_index=True)
            df.to_csv(f, index=False)

    # Else create a new processed file
    else:
        d = {'Symbol': s, 'Processed': ['not processed'] * len(s)}
        df = pd.DataFrame(data=d)
        df.to_csv(f, index=False)

    # Get list of symbols that have yet to be processed
    indeces = df[df['Processed'] == 'not processed'].index.tolist()
    symbols = df[df.index.isin(indeces)]['Symbol'].tolist()

    return symbols


def updateProcessed(f, s, error):
    """Update processed file."""
    f = f.rstrip('.csv') + '_Processed.csv'
    df = pd.read_csv(f)
    i = df[df['Symbol'] == s].index.item()
    df.loc[i, 'Processed'] = error.lstrip('_')
    df.to_csv(f, index=False)


def makeDirectory(dataFolder):
    """Make neccessary folders to run script."""
    for folder in ['Processed', dataFolder]:
        if not os.path.exists(folder):
            os.mkdir(folder)


def saveAll(record, columns):
    """Save test results after analyzing all stocks."""
    filename = date.today().strftime('%Y-%m-%d') + ' Results.csv'

    # If an *Results.csv exists append to it
    if os.path.exists(filename):
        exists = True
        df2 = pd.read_csv(filename)
    else:
        exists = False

    record = np.array(record)

    # Search through *Results.csv and find and replace rows of stock data
    # if they are in the dataframe
    if exists:
        i = 0
        while i < record.shape[0]:
            if record[i, 0] in df2['stock'].tolist():
                index = df2[df2['stock'] == record[i, 0]].index.item()
                df2.loc[index, :] = record[i, :]
                record = np.delete(record, i, 0)
            i += 1

    df = pd.DataFrame(record, columns=columns)

    if exists:
        df = pd.concat([df2, df], ignore_index=True)

    df.to_csv(filename, index=False)
