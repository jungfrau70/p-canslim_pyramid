# Stock Search

## Description

These scripts will automate the process of finding stocks worth investing in.
For details about how stocks are chosen please go to **INSERT MEDIUM ARTICLE LINK**

## Installation

You can install the necessary packages using your favorite package manager

Using PIP: `pip install -r requirements.txt`

Using Anaconda: `conda install --file requirements.txt`

I have not been able to download `yfinance` using Anaconda and if
you choose to use `conda install --file requirements.txt` it may not work.
In this case remove `yfinance==0.1.54` from the *requirements.txt* and then
download yfinance seperately using `pip install yfiannce`.

## Usage

You can run several options from your command-line interpreter.

To download data using API
- `python findStocks.py --stock_list "Example Stock List.csv" --key "YOURAPIKEY"`

To use data already downloaded
- `python findStocks.py --stock_list "Example Stock List.csv" --data_folder "Example Data"`

To get some help
- `python findStocks.py --help`

Data downloaded from Alpha Vantage's API is not perfect and there is often
data missing. The scripts are set up to copy recent data if it is missing.
The program can be set up to have the user input missing data. If you would
like to find the missing data from SEC.gov and input it manually add the
argument `--not_flexible`.

If the program is run successfully the following folders will be saved:
- **Results.csv* summarizing the Results
- **Processed.csv* keeps track of which stocks have already been processed
- *Data* folder includes data downloaded using Alpha Vantage API
- *Processed* folder includes condensed financial information that was used to determine which stocks are good

You can also look at the **Processed.csv* to find error messages indicating
which stocks were unable to be processed. Check out the docstring at the top of
`findStocksClasses.py` for more information about the error messages and how
to correct them.

## Support

Much more information is provided in this Medium article **INSERT MEDIUM ARTICLE LINK** or you can email *hart.sensr@gmail.com*

## Contributing

I am open to suggestions and contributions. Please email me at *hart.sensr@gmail.com*