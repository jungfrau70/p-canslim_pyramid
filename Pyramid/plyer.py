
import requests
import json
import pandas as pd
import time
import datetime as dt

from concurrent import futures
from dateutil.relativedelta import relativedelta
from pandas_datareader import data as pdr
from scipy.stats import gaussian_kde

import yfinance as yf
import pandas as pd
import talib
# from plyer import notification

""" datetime util """
now = dt.datetime.now()
lastday = now + relativedelta(months=0, days=-1)
firstday_of_this_month = dt.datetime(now.year, now.month, 1)
lastday_of_this_month = dt.datetime(now.year, now.month, 1) + relativedelta(months=1, days=-1)
firstday_of_last_month = dt.datetime(now.year, now.month, 1) + relativedelta(months=-1, days=0)
lastday_of_last_month = dt.datetime(now.year, now.month, 1) + relativedelta(months=0, days=-1)
one_month_ago = now + relativedelta(months=-1)


def get_stock_codes():
    # get all stock codes from yfinance
    stock_codes = yf.Tickers().tickers

    return stock_codes

def get_stock_data(stock_symbol, start_date, end_date):
    # Get stock data from an API
    stock_data = yf.download(stock_symbol, start=start_date, end=end_date)
    return stock_data
    
def send_notification(stock_symbol, pattern):
    # Send a notification
    # Send desktop notification
    notification.notify(
        title='Cup with Handle Pattern Found',
        message='The stock ticker ' + ticker + ' has a Cup with Handle pattern',
        timeout=10
    )

def check_pattern(stock_data, pattern):
    # Check if the pattern exists in the stock data
    # Calculate technical indicators using ta-lib
    stock_data['SMA20'] = talib.SMA(stock_data['Close'], timeperiod=20)
    stock_data['SMA50'] = talib.SMA(stock_data['Close'], timeperiod=50)
    
    # Look for instances of the "cup with handle" pattern
    if (pattern == "cup with handle"):
        for index, row in stock_data.iterrows():
            if row['Close'] > row['SMA20'] and row['Close'] < row['SMA50']:
                if index > one_month_ago:
                    print(index)
                    # if row['Close'] > row['SMA20'] and row['Close'] < row['SMA50']:
                    #     if pd.to_datetime(row['Date']) > pd.to_datetime(lastday_of_last_month):
                    #         # Send desktop notification
                    #         # send_notification(stock_symbol, pattern)
                    #         print(stock_symbol, pattern)
                    

if __name__ == "__main__":
    # The stock symbol to monitor
    stock_symbol = "AAPL"

    # The pattern to look for
    pattern = "cup with handle"

    # How many days ago to start looking for the pattern
    start_date = "2022-01-01"
    end_date = lastday.strftime('%Y-%m-%d')

    stock_data = get_stock_data(stock_symbol, start_date, end_date)
    if check_pattern(stock_data, pattern):
        send_notification(stock_symbol, pattern)

# while True:
#     stock_data = get_stock_data(stock_symbol, start_date, end_date)
#     if check_pattern(stock_data, pattern):
#         send_notification(stock_symbol, pattern)
#         break

#     # Wait for a day before checking again
#     time.sleep(60*60*24)
