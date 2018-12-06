import unittest
from final_project import *

class TestDataAccess(unittest.TestCase):

    def get_returns_from_list(self, company, returns):
        for i in returns:
            if company in i:
                return True
        return False

    def get_key_from_dict(self, company, returns):
        for i in returns:
            if company in i['name']:
                return True
            else:
                pass
        return False

    def get_value_from_key(self, company, code, returns):
        for i in returns:
            if company in i['name']:
                if i['code'] == code:
                    return True
                else:
                    pass
        return False

    def test__search_googlecse(self):
        #Google Custom Search API will only return 10 results per query
        self.assertEqual(len((search_google("SGX Venture Corporation Limited latest news")[0])), 10)
        self.assertEqual(len((search_google("SGX United Overseas Bank Limited latest news")[1])), 10)
        self.assertTrue(self.get_returns_from_list('Singapore', search_google("SGX Singapore Exchange latest news")[0]))
        self.assertFalse(self.get_returns_from_list('Michigan Ann Arbor', search_google("SGX Singapore Exchange latest news")[0]))

    def test__scrape_shareinvestor_site(self):
        self.assertEqual(len(stock_financials("O39")),17)
        self.assertTrue(self.get_returns_from_list('OVERSEA-CHINESE BANKING CORP', stock_financials("O39")))
        self.assertFalse(self.get_returns_from_list('CHINA INTERNATIONAL HLDGS', stock_financials("O39")))
        self.assertTrue(self.get_returns_from_list('CHINA INTERNATIONAL HLDGS', stock_financials("BEH")))
        self.assertFalse(self.get_returns_from_list('SINGTEL', stock_financials("BEH")))

    def test_scrape_eoddata(self):
        self.assertEqual(len(stockcode_scraping()),1173) #there are 1173 listed companies in Singapore Stock Exchange
        self.assertTrue(self.get_key_from_dict('XIAOMI', stockcode_scraping()))
        self.assertFalse(self.get_key_from_dict('MICHIGAN', stockcode_scraping()))
        self.assertTrue(self.get_value_from_key('SINGAPORE TECH', 'S63', stockcode_scraping()))
        self.assertFalse(self.get_value_from_key('SINGAPORE TECH', 'O39', stockcode_scraping()))

class TestDatabase(unittest.TestCase):

    def test_stocks_table(self):
        conn = sqlite3.connect('Stocks_Database.sqlite')
        cur = conn.cursor()

        statement = 'SELECT Name FROM Stocks'
        cur.execute(statement)
        result = cur.fetchall()
        self.assertIn(('SINGAPORE EXCHANGE LIMITED',), result)

        statement = '''
            SELECT Name, Code FROM Stocks
        '''
        cur.execute(statement)
        result = cur.fetchall()
        self.assertEqual(result[2][1], "Z74")

        conn.close()

    def test_stock_financials_table(self):
        conn = sqlite3.connect('Stocks_Database.sqlite')
        cur = conn.cursor()

        statement = 'SELECT Name FROM Stocks'
        cur.execute(statement)
        result = cur.fetchall()
        self.assertIn(('SINGAPORE EXCHANGE LIMITED',), result)

        statement = '''
            SELECT Name, Code FROM Stocks
        '''
        cur.execute(statement)
        result = cur.fetchall()
        self.assertEqual(result[2][1], "Z74")

        conn.close()

    def test_joins(self):
        conn = sqlite3.connect('Stocks_Database.sqlite')
        cur = conn.cursor()

        statement = '''
        SELECT Stocks.Name, Stocks.Code, Stock_Financials.Date, Stock_Financials.Time_Recorded, Stock_Financials.Price, Stock_Financials.Day_Highest, Stock_Financials.Day_Lowest, Stock_Financials.Div_Yield, Stock_Financials.EPS, Stock_Financials.Buy_Vol, Stock_Financials.Sell_Vol, Stock_Financials.PE, Stock_Financials.NAV, Stock_Financials.Price_per_cashflow, Stock_Financials.Market_Cap FROM Stocks
        JOIN Stock_Financials
        ON Stocks.Id = Stock_Financials.Name_ID
        WHERE Stocks.Name = "DBS GROUP HOLDINGS LTD"
        '''
        cur.execute(statement)
        result = cur.fetchall()
        self.assertEqual(result[2][8], "1.68364")
        self.assertEqual(len(result[1]), 15)
        conn.close()


class TestPlotting(unittest.TestCase):

    def test_plot_financials(self):
        try:
            plot_charts("2")
        except:
            self.fail()

    def test_plot_price(self):
        try:
            plot_price("4")
        except:
            self.fail()

    def test_plot_eps(self):
        try:
            plot_eps("2")
        except:
            self.fail()

    def test_plot_nav(self):
        try:
            plot_nav("4")
        except:
            self.fail()

    def test_plot_pe(self):
        try:
            plot_pe("2")
        except:
            self.fail()

    def test_plot_div_yield(self):
        try:
            plot_div_yield("4")
        except:
            self.fail()

    def test_plot_price_cashflo(self):
        try:
            plot_price_cashflow("2")
        except:
            self.fail()

    def test_plot_volume(self):
        try:
            plot_volume("4")
        except:
            self.fail()
    
unittest.main()
