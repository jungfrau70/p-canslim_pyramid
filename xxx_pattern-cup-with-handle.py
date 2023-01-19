
import os
import requests
import json
import pandas as pd
import time
import datetime as dt

from os.path import exists
from concurrent import futures
from dateutil.relativedelta import relativedelta
from pandas_datareader import data as pdr
from scipy.stats import gaussian_kde

import yfinance as yf
import pandas as pd
import talib
# from plyer import notification

""" set output directory """
data_dir = "./data"
os.makedirs(data_dir, exist_ok=True)

""" datetime util """
now = dt.datetime.now()
lastday = now + relativedelta(months=0, days=-1)
firstday_of_this_month = dt.datetime(now.year, now.month, 1)
lastday_of_this_month = dt.datetime(now.year, now.month, 1) + relativedelta(months=1, days=-1)
firstday_of_last_month = dt.datetime(now.year, now.month, 1) + relativedelta(months=-1, days=0)
lastday_of_last_month = dt.datetime(now.year, now.month, 1) + relativedelta(months=0, days=-1)
one_month_ago = now + relativedelta(months=-1)
start_date = "2022-01-01"
end_date = lastday.strftime('%Y-%m-%d')

from utils import gmail

def get_stock_codes(end_date):

    if exists(f"{data_dir}/SP500_{end_date}.csv"):
        sp500_df = pd.read_csv(f"{data_dir}/SP500_{end_date}.csv")
        sp500_tickers = list(sp500_df["Symbol"])
    else:
        tables = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')       
        sp500_df = tables[0]
        second_table = tables[1]

        # rename symbol to escape symbol error
        sp500_df["Symbol"] = sp500_df["Symbol"].map(lambda x: x.replace(".", "-"))
        sp500_df.to_csv(f"{data_dir}/SP500_{end_date}.csv", index=False)
        sp500_df = pd.read_csv(f"{data_dir}/SP500_{end_date}.csv")

    return sp500_df

def get_stock_data(stock_symbol, start_date, end_date):
    filename = f"{data_dir}/{stock_symbol}_{end_date}.csv"
    if exists(filename):
        stock_data = pd.read_csv(filename)
        stock_data['Date'] = stock_data['Date'].apply(lambda x: dt.datetime.strptime(x, '%Y-%m-%d'))
        stock_data['Date'] = pd.to_datetime(stock_data['Date']).apply(lambda x: pd.to_datetime(x))        
        stock_data = stock_data.set_index('Date')
    else:        
        # Get stock data from an API
        stock_data = yf.download(stock_symbol, start=start_date, end=end_date)
        stock_data.reset_index(inplace=True)
        stock_data = stock_data.rename(columns = {'index':'Date'})
        stock_data.to_csv(filename, index=False)
    return stock_data
    
def send_notification(stock_symbol, pattern):
    # Send a notification
    # Send desktop notification
    # notification.notify(
    #     title='Cup with Handle Pattern Found',
    #     message='The stock ticker ' + ticker + ' has a Cup with Handle pattern',
    #     timeout=10
    # )
    print(stock_symbol, pattern, datetime)


def check_pattern(stock_symbol, stock_data, pattern):
    # Check if the pattern exists in the stock data
    # Calculate technical indicators using ta-lib
    try:
        stock_data['SMA20'] = talib.SMA(stock_data['Close'], timeperiod=20)
        stock_data['SMA50'] = talib.SMA(stock_data['Close'], timeperiod=50)

        # Look for instances of the "cup with handle" pattern
        if (pattern == "cup with handle"):
            for index, row in stock_data.iterrows():
                if row['Close'] > row['SMA20'] and row['Close'] < row['SMA50']:
                    if index > pd.Timestamp(one_month_ago):
                        findings.append({ "stock_symbol": stock_symbol, "timestamp": index, "pattern": pattern })
                        # if row['Close'] > row['SMA20'] and row['Close'] < row['SMA50']:
                        #     if pd.to_datetime(row['Date']) > pd.to_datetime(lastday_of_last_month):
                        #         # Send desktop notification
                        #         # send_notification(stock_symbol, pattern)
                        #         print(stock_symbol, pattern)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    
    findings = []
    
    # The stock symbol to monitor
    stock_symbols = get_stock_codes(end_date)['Symbol']

    # The pattern to look for
    pattern = "cup with handle"

    for stock_symbol in stock_symbols:
        stock_data = get_stock_data(stock_symbol, start_date, end_date)
        check_pattern(stock_symbol, stock_data, pattern)
           
    # Save findings to csv
    df_findings = pd.DataFrame(findings)
    df_findings.rename(columns={'timestamp':'Date'}, inplace=True)
    df_findings = df_findings.set_index('Date')
    filename = f"{end_date}_findings.csv"
    df_findings.to_csv(filename)
    
    # Send_email_notificatioin   
    fromaddr = "inhwan.jung@gmail.com"
    toaddr = "9368265@ict-companion.com"

    # open the file to be sent 
    filename = f"{end_date}_findings.csv"

    if exists(filename):
        gmail.send(filename, fromaddr, toaddr)
    else:
        print("Not exists")
        
# while True:
#     stock_data = get_stock_data(stock_symbol, start_date, end_date)
#     if check_pattern(stock_data, pattern):
#         send_notification(stock_symbol, pattern)
#         break

#     # Wait for a day before checking again
#     time.sleep(60*60*24)
