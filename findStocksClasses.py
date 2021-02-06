#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Classes for findStock scripts.

After running the script look through the *_Processed.csv and correct any errors
Errors that can be corrected:
    - data does not exist: This error occurrs when a user inputs 0 when asked
        for stock information and the data does not exist. In which case the
        rows of the Income Statement and Balance Sheet needs to be deleted.
    - data missing: This error occurrs when over half of the data of a specific
        type (netIncome, totalRevenue, etc...) is missing (i.e. 'None'). It is
        up to the user to find the missing data and save in Income Statement
        and Balance Sheet .csvs
    - processed_copied: This error occurrs when totalRevenue, netIncome, or
        totalShareholderEquity was copied from other data in financial reports.
        To correct this error find the missing data from sec.gov.
    - unaligned reports: This error occurs when either the annual or the
        quarterly Income Statement and Balance Sheet fiscalDateEnding columns
        align. This is usually a case of missing data/rows. Find the misaligned
        section of the financial reports and add the data from sec.gov

There are other conditions when a stock can fail. Scripts can be modified to
ignore these error messages:
    - foreign currency: If stocks are not in US dollars and error message will
        be saved and stock is not analyzed
    - slope failed: If the stock's price is not increasing over the last
        several months then save the error message and skip stock
    - negative net income: If the two most recent quarters and most recent year
        reported have negative net income skip the stock

After you correct the errors be sure to change error in Processed column to
"not processed" and rerun the script to process changes.
"""
import pandas as pd
import re
import os
import copy
import statistics
from datetime import datetime as dt
from datetime import timedelta as td
import yfinance as yf
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


class Stock():
    """Stock class."""

    def __init__(self, stock, dataFolder, flexible):
        """Initialize."""
        self.dataPath = dataFolder
        self.processPath = 'Processed'
        self.s = stock
        self.date = self.getDate()
        self.ab = self.read('Annual Balance Sheet')
        self.ai = self.read('Annual Income Statement')
        self.qb = self.read('Quarterly Balance Sheet')
        self.qi = self.read('Quarterly Income Statement')
        self.miss = {'a': None, 'q': None}
        self.nothingMissing = {'totalRevenue': [],
                               'netIncome': [],
                               'totalShareholderEquity': [],
                               'commonStockSharesOutstanding': []}
        self.record = {'stock': self.s, 'slope': 0, 'avgpc': 0, 'copied': 0,
                       'annualeps': 0, 'annualroe': 0, 'quarterlyeps': 0,
                       'quarterlyrevenue': 0, 'numfailed': 0}
        # If flexible, use data available in spreadsheets. If not flexible then
        # get user input to fill in missing data
        self.flex = flexible
        self.errorMessage = 'processed'
        self.daysClosed = [dt(2020, 1, 1), dt(2020, 1, 20), dt(2020, 2, 17),
                           dt(2020, 4, 10), dt(2020, 5, 25), dt(2020, 7, 3),
                           dt(2020, 9, 7), dt(2020, 11, 26), dt(2020, 12, 25),
                           dt(2021, 1, 1), dt(2021, 1, 18), dt(2021, 2, 15),
                           dt(2021, 4, 2), dt(2021, 5, 31), dt(2021, 7, 5),
                           dt(2021, 9, 6), dt(2021, 11, 25), dt(2021, 12, 24)]

    def getDate(self):
        """Get the date of the balance sheet and income statement."""
        regex = re.compile(r'\d\d\d\d-\d\d-\d\d')
        n = len(self.s)
        for f in os.listdir(self.dataPath):
            if self.s + ' ' == f[:n + 1]:
                return regex.search(f).group()

    def read(self, report):
        """Read in reports."""
        file = self.s + ' ' + self.date + ' ' + report + '.csv'
        path = os.path.join(self.dataPath, file)
        return pd.read_csv(path, parse_dates=['fiscalDateEnding'])

    def prelimTests(self):
        """Prepare reports and preform preliminary tests."""

        def removeExcess(b, i, rows, errorMessage='none'):
            """Remove excess rows."""
            minRows = len(b) if len(b) < rows else rows
            b = b.iloc[:minRows, :]
            i = i.iloc[:minRows, :]
            if not all(b['fiscalDateEnding'] == i['fiscalDateEnding']):
                return None, None, None, True
            return b, i, minRows, False

        def checkPercentNone(b, i, minRows, nonePercent=0.5):
            """Check the percentage of rows that are 'None'."""
            for c in ['totalShareholderEquity', 'commonStockSharesOutstanding']:
                numNone = b[b[c] == 'None'].index.size
                if numNone / minRows > nonePercent:
                    return True
            for c in ['netIncome', 'totalRevenue']:
                numNone = i[i[c] == 'None'].index.size
                if numNone / minRows > nonePercent:
                    return True
            return False

        def checkCurrency(report, foreign=False):
            """Check current of reports."""
            if not all(report['reportedCurrency'].to_numpy() == 'USD'):
                foreign = True
            return foreign

        # Remove excess number of rows
        self.ab, self.ai, minRowsA, unaligna = removeExcess(self.ab, self.ai, 4)
        self.qb, self.qi, minRowsQ, unalignq = removeExcess(self.qb, self.qi, 14)

        if unaligna or unalignq:
            self.errorMessage = 'unaligned reports'
            return

        # Check the percentage of rows that are missing data
        tooManyNoneA = checkPercentNone(self.ab, self.ai, minRowsA)
        tooManyNoneQ = checkPercentNone(self.qb, self.qi, minRowsQ)

        if tooManyNoneA or tooManyNoneQ:
            self.errorMessage = 'data missing'
            return

        # Check currency
        aiForeign = checkCurrency(self.ai)
        biForeign = checkCurrency(self.ab)
        if aiForeign or biForeign:
            self.errorMessage = 'foreign currency'
            return

    def checkSlope(self):
        """Check the modified average slope of the stock price."""
        def getBackYearMonth(y, m):
            """Get year and month by subtracting one month."""
            if m == 1:
                y -= 1
                m = 12
            else:
                m -= 1
            return dt(y, m, 1)

        # Get a list of days to use the stock price
        dates = []
        today = dt.now()
        year = today.year
        month = today.month

        # If the day of the month is greater than 10, calculate the slope of
        # the current month. Otherwise, calculate the slop from today to the
        # first day of the previous month
        if today.day > 10:
            dates.append(dt(year, month, 1))

        back = getBackYearMonth(year, month)
        dates.append(back)

        # Get six different date ranges, i.e. 6 months
        while len(dates) < 6:
            back = getBackYearMonth(back.year, back.month)
            dates.append(back)

        dates.sort()

        # Download ticker data
        df = yf.download(self.s, period='1y', interval='1d')
        # Get the most recent close price
        last = df.iloc[-1, 3]
        self.changes = []
        adjSlope = 0
        normalizer = 0
        # Example dates: [9/1/2020, 10/1/2020, 11/1/2020, 12/1/2020,
        #                 1/1/2021, 2/1/2021, 2/15/2021]
        for i in range(len(dates)):
            # Fist of the month might not be a day that the stock market is
            # open. If it is not then subtract one day until it is in df.index
            d = dates[i]
            while d not in df.index or d in self.daysClosed:
                d -= td(days=1)
            # Get close price
            price = df.loc[d, 'Close']
            # Calculate percent change
            pc = (last - price) / price
            # Weight increases each month. More weight is added to recent slopes
            weight = i + 1
            # Add to normalizer, this will normalize the cumulative slopes.
            normalizer += weight
            # Add to the cumulative slope
            adjSlope += pc * (weight)
            self.changes.append(pc)

        self.record['slope'] = round(adjSlope / normalizer, 3)

        if adjSlope < 0:
            self.errorMessage = 'slopefailed'

    def checkNegativeIncome(self):
        """Check if two recent quarters had negative incomes."""
        def getIncome(report, i, period):
            income = report.loc[i, 'netIncome']
            if income in ['None', '0', 0]:
                income = self.getInput(report, 'netIncome', i, period)
            return income

        self.qi.loc[0, 'netIncome'] = getIncome(self.qi, 0, 'quarterly')
        self.qi.loc[1, 'netIncome'] = getIncome(self.qi, 1, 'quarterly')
        self.ai.loc[0, 'netIncome'] = getIncome(self.ai, 0, 'annual')

        for income in [self.qi.loc[0, 'netIncome'],
                       self.qi.loc[1, 'netIncome'],
                       self.ai.loc[0, 'netIncome']]:
            # User can input 0 if the data does not exist. In which case
            # update the error message
            if income == 0:
                self.errorMessage = 'data does not exist'
                return
            if int(income) < 0:
                self.errorMessage = 'negative net income'
                return

    def reduceDF(self):
        """
        Combine balance sheet and income statements.

        Earnings per share (EPS) is calculated as a company's profit divided by
        the outstanding shares of its common stock

        Shareholder equity (SE) is the corporation's owners'residual claim on
        assets after debts have been paid.
        ...  Shareholders’ equity = total assets − total liabilities

        Return on equity (ROE) is a measure of financial performance calculated
        by dividing net income by shareholders' equity. Because shareholders'
        equity is equal to a company’s assets minus its debt, ROE is considered
        the return on net assets.
        """

        def reduce(i, b):
            """Reduce dataframe."""
            report = pd.concat([i['fiscalDateEnding'],
                                i['totalRevenue'],
                                i['netIncome'],
                                b['totalShareholderEquity'],
                                b['commonStockSharesOutstanding']],
                               axis=1, ignore_index=True)
            report.columns = ['fiscalDateEnding', 'totalRevenue',
                              'netIncome', 'totalShareholderEquity',
                              'commonStockSharesOutstanding']
            return report

        self.reports = {'a': reduce(self.ai, self.ab),
                        'q': reduce(self.qi, self.qb)}

    def identifyMissing(self, report):
        """Identify missing data."""
        miss = copy.deepcopy(self.nothingMissing)
        for c in miss:
            for i in range(len(report)):
                if report.loc[i, c] in ['None', '0', 0]:
                    miss[c].append(i)
        return miss

    def getData(self, report, miss):
        """Get missing data."""
        for c in miss:
            for i in miss[c]:
                report.loc[i, c] = self.getInput(report, c, i, 'annual')
        return report

    def getInput(self, report, metric, ind, period):
        """Get input for missing data."""
        date = report.loc[ind, 'fiscalDateEnding']
        print('>>> Find missing data from sec.gov or enter 0 if the data does'
              ' not exist')
        user = int(input('>>> Input ' + str(period) + ' ' + str(metric)
                         + ' for ' + date.strftime('%Y-%m-%d') + ': '))
        return user

    def copy(self, report, miss):
        """Copy recent data to rows with missing data."""
        saveError = False
        for m in miss:
            # If there is missing data
            if miss[m] != []:
                # If the last row is 'None' (included in miss[m]) copy the most
                # recent row with data to the last row.
                if miss[m][-1] == len(report) - 1:

                    for i in reversed(range(len(report))):
                        data = report.loc[i, m]
                        if data != 'None' and data != '0':
                            report.loc[len(report) - 1, m] = data
                            miss[m].pop(-1)
                            break

                # Process rest of missing rows and copy the next oldest row
                for i in reversed(miss[m]):
                    report.loc[i, m] = report.loc[i + 1, m]
                miss[m] = []

                if m != 'commonStockSharesOutstanding':
                    saveError = True

        # Only save the error meesage if data was compied from non-common
        # stock shares outstanding
        if saveError and 'copied' not in self.errorMessage:
            self.record['copied'] = 'TRUE'
            self.errorMessage += '_copied'
        else:
            self.record['copied'] = 'FALSE'
        return report, miss

    def checkType(self, report):
        """Check column types."""
        # Start from 1 to skip fiscalDateEnding column
        for c in range(1, len(report.columns)):
            if report.iloc[:, c].dtypes == 'O':
                report.iloc[:, c] = pd.to_numeric(report.iloc[:, c])
        return report

    def checkSmallShares(self, shares):
        """
        Check shares have the correct number of trailing zeros.

        E.g. change shares reported as 123456 to 123456000. Often API will
        download incorrect number of shares.
        """
        # Use the median number of digits to decide if shares should be
        # extended
        num = []
        for i in shares:
            num.append(len(str(i)))
        expected = statistics.median(num)
        for i in range(len(shares)):
            if len(str(shares[i])) < expected - 1:
                dif = expected - len(str(shares[i]))
                assert dif % 3 == 0
                newShares = int(shares[i] * 10 ** dif)
                print('>>> Shares were increased from', shares[i],
                      'to', newShares)
                shares[i] = newShares
        return shares

    def calculate(self, report):
        """Calculate ROE and EPS."""
        report['eps'] = report['netIncome'] / report['commonStockSharesOutstanding']
        report['roe'] = report['netIncome'] / report['totalShareholderEquity']
        return report

    def percentChange(self, t2, r):
        """Calculate percentage change of sales and EPS."""
        p = 4 if r == 'q' else 1
        t1 = t2.shift(periods=-p)
        for c in ['totalRevenue', 'netIncome', 'eps']:
            t2[c + 'PercentChange'] = (t2[c] - t1[c]) / t1[c].abs()
        return t2

    def roundReports(self, report):
        """Round columns in dataframes."""
        return report.round({'eps': 3,
                             'roe': 3,
                             'totalRevenuePercentChange': 3,
                             'netIncomePercentChange': 3,
                             'epsPercentChange': 3})

    def test(self, report, r, mineps=0.2, minrev=0.2, minroe=0.17):
        """
        Check if stocks pass percent change tests.

        1. Annual - EPS must increase by 20%
        2. Annual - ROE must be over 17%
        3. Quarterly - EPS must increase by 20%
        4. Quarterly - Sales must increase by 20%
        """
        m = 'annual' if r == 'a' else 'quarterly'
        if report.loc[0, 'epsPercentChange'] < mineps:
            self.record[m + 'eps'] = 1
            self.record['numfailed'] += 1
        if m == 'annual':
            if report.loc[0, 'roe'] < minroe:
                self.record['annualroe'] = 1
                self.record['numfailed'] += 1
        if m == 'quarterly':
            if report.loc[0, 'totalRevenuePercentChange'] < minrev:
                self.record['quarterlyrevenue'] = 1
                self.record['numfailed'] += 1

    def averagePercentChange(self, report):
        """Calculate the average of percent changes."""
        pcs = []
        pcs.extend(report.loc[:2, 'totalRevenuePercentChange'].tolist())
        pcs.extend(report.loc[:2, 'epsPercentChange'].tolist())
        self.record['avgpc'] = round(statistics.mean(pcs), 3)

    def save(self):
        """Save the combined quarterly and annual reports."""
        df = pd.concat([self.reports['q'], self.reports['a']], ignore_index=True)
        filename = self.s + '_' + self.date + '.csv'
        path = os.path.join(self.processPath, filename)
        df.to_csv(path, index=False)
