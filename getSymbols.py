import os
import glob
import datetime as dt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
yf.pdr_override() # <== that's all it takes :-)

from concurrent import futures
from dateutil.relativedelta import relativedelta
from pandas_datareader import data as pdr
from scipy.stats import gaussian_kde

""" datetime util """
now = dt.datetime.now()
lastday = now + relativedelta(months=0, days=-1)
firstday_of_this_month = dt.datetime(now.year, now.month, 1)
lastday_of_this_month = dt.datetime(now.year, now.month, 1) + relativedelta(months=1, days=-1)
firstday_of_last_month = dt.datetime(now.year, now.month, 1) + relativedelta(months=-1, days=0)
lastday_of_last_month = dt.datetime(now.year, now.month, 1) + relativedelta(months=0, days=-1)

""" set the download window """
start_date = "2017-01-01"
end_date = lastday.strftime('%Y-%m-%d')

""" set the data_dir """
data_dir = "./data"
os.makedirs(data_dir, exist_ok=True)

""" Download Tickers """
tables = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')

sp500_df = tables[0]
second_table = tables[1]
print(sp500_df.shape)

""" save symbols into csv file """
# rename symbol to escape symbol error
sp500_df["Symbol"] = sp500_df["Symbol"].map(lambda x: x.replace(".", "-"))
sp500_df.to_csv(f"{data_dir}/SP500_{end_date}.csv", index=False)
sp500_df = pd.read_csv(f"{data_dir}/SP500_{end_date}.csv")
print(sp500_df.shape)
sp500_tickers = list(sp500_df["Symbol"])
print(sp500_df.head())
#print(sp500_tickers)
