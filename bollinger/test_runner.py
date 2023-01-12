import unittest #import TestCase

from technical_indicators_calculator import set_technical_indicators, Company
from technical_indicators_chart_plotting import TechnicalIndicatorsChartPlotter
import yfinance as yf

class TestTechnicalIndicator(unittest.TestCase):

    def test_tech_indicator(self):
        company = Company('FNGD')
        config = {}
        company.prices = yf.Ticker(company.symbol).history(period='1y')['Close']
        set_technical_indicators(config, company)

        tacp = TechnicalIndicatorsChartPlotter()
        tacp.plot_macd(company)
        tacp.plot_rsi(company)
        tacp.plot_bollinger_bands(company)

if __name__ == "__main__":
    unittest.main()        