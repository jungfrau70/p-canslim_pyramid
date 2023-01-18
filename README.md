# Stock Search
https://gitlab.com/hartr/stock-search-public

## Description

These scripts automate the process of finding stocks worth investing in.
For details about how to use this repository please go to
https://hartrockwell.medium.com/how-to-find-stocks-to-invest-in-using-python-87b5169190d5

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
data missing. The scripts are set up to copy recent data if data is missing.
The program can be set up to have the user input missing data. If you would
like to find the missing data from SEC.gov and input it manually add the
argument `--not_flexible`.

After running the program, the following files and folders will be saved:
- **Results.csv* summarizing the Results
- **Processed.csv* keeps track of processed stocks and error messages
- *Data* folder includes data downloaded using Alpha Vantage API
- *Processed* folder includes condensed financial data used to determine which stocks are good

You can look at the **Processed.csv* to find error messages indicating
which stocks were unable to be processed. Check out the docstring at the top of
`findStocksClasses.py` for more information about the error messages and how
to correct them.

## Re-running the program
A maintenance script has been included in the `utilities` folder to clear temporary files automatically so that the stock-search can be re-run. To run this:
- First enable the script to be executed via running `sudo chmod +x ./utilities/remove_stale_files.sh` from the root directory of this project. 
- Run `sudo ./utilities/remove_stale_files.sh` to clear your stale files
- Stock-search is ready to run again

## Support

Much more information is provided in this Medium article
https://hartrockwell.medium.com/how-to-find-stocks-to-invest-in-using-python-87b5169190d5
or you can email *hart.sensr@gmail.com* for support

## Contributing

I am open to suggestions and contributions. Please email me at *hart.sensr@gmail.com*


-----------------------------------------------------------------------------------------------------------------------------

# Introduction

- A Python scraping program to analyze & visualize stocks using the [CANSLIM](https://www.investopedia.com/terms/c/canslim.asp) method by William J.O'Neil, also includes a calculator to find entry points to add more positions to your portfolio (Pyramid Buying).

## Tech stack

- Python:
  - pandas, numpy, matplotlib
  - [python-fire](https://github.com/google/python-fire) to automatically generate command line interfaces.
  - [Beautiful Soup](https://beautiful-soup-4.readthedocs.io/en/latest/#) to scrap HTML data.

## Instructions

- Prefer video tutorial? Click [here](https://youtu.be/GDBEka9FVas).

1. `git clone https://github.com/KhoiUna/python-canslim.git && cd python_canslim`
2. `pip install -r requirements.txt` to install the required dependencies
3. `python CANSLIM/main.py analyze [TICKER] [TICKER]...` to analyze stocks using the CANSLIM method.
   - You can run `python CANSLIM/main.py -h` or `python CANSLIM/main.py analyze -h` to learn more about available command.
   - The program will return **-GOOD STOCKS-** that fit the CANSLIM criteria.
4. `python Pyramid_Profit_Calculator/main.py` to start the Pyramid Buying calculator GUI.

### Notes:

- Data are scraped from [Macrotrends](https://www.macrotrends.net/)