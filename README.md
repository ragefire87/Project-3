My project would allow user to access stocks information listed on the Singapore Stock Exchange (SGX). Using this program, the user can pull out the full list of stocks listed in SGX, select the stock they are interested in through the search feature, to view relevant key financial metrics.

For each stock, the user can access the latest news associated with the stock in the program itself, to help him/her check out recent happenings that might explain the stock's price movement.

A Google Custom Search API key and CX ID is required to run this program. Keep this key in a secrets.py file.

There are three data sources used for this program:
1) Google Custom Search API 
(documentation: https://developers.google.com/custom-search/v1/using_rest)
2) Stock Codes from eoddata website (http://eoddata.com/stocklist/SGX.htm)
3) Share Investor webpage for stocks data using stock codes obtained from eoddata website (https://www.shareinvestor.com/fundamental/factsheet.htm)

Data obtained from these three data sources are all written into json cache. 

For Google Custom Search, the cache expiry is set to 30 minutes, in anticipation of latest news which require fresh data from the website.

For eoddata, the cache expiry is set to 15 days in anticipation of new stock listings through initial public offering (IPO). But since we do not expect to have IPOs happening every day, a 15 day refresh rate seems about right.

For Share Investor data, the cache expiry is set to 1 minute. This is because stock prices are moving constantly and a range of 1 - 10 minute seems about right. The timing can be adjusted easily within the codes by changing the "Max_Staleness" written in seconds.

These cache data are eventually written to SQL database which processes data query faster and efficiently.

Plotly is the presentation tool used to display the key financial metrics queried by the user. The user of this program will need to obtain a Plotly account and setup his credentials on his computer. The procedure to do so are available here: (https://plot.ly/python/getting-started/)

The program codes are structured into 6 segments:
1) Google Custom Search API and its cache functions - search_google()

2) Share Investor website scraping functions and its cache functions - stock_financials()

3) Eoddata website scraping and its cache functions - stockcode_scraping()

4) Dealing with SQLite - create_db(), insert_stuff(), add_portfolio(), assess_portfolio(), delete_from_portfolio(), assess_financials(), auto_update()

5) Presentation in plotly - plot_charts(), plot_price(), plot_eps(), plot_nav(), plot_pe(), plot_div_yield(), plot_price_cashflow(), plot_volume()

6) Interactive codes

User Guide
The interactive segment presents the user with 6 options:
0) Re-initialize database - for maintenance purpose by recreating SQLite database, re-inserting data into the tables and re-inserting user's portfolio of stocks from memory (cache)

1) Search for a stock - for user to search for any stock listed on the Singapore Stock Exchange. For example if user would like to query for stock called "VENTURE CORPORATION LIMITED", user can search using the non-exhaustive list such as  "VE", "VENTURE", "VENTURE COR", "LIMITED" etc... as long as the words inputted are within the strings of the stock name.
- adding and deleting of stocks to and from portfolio are sub-menus of this option
- obtaining latest news information of the searched stock is a sub-menu of this option

2) Access Stocks Portfolio - displays the list of stocks that have been added into the portfolio by the user prior to executing this option.
- analyzing stocks performance within the portfolio is a sub-menu of this option
- charting stocks metrics using Plotly is a sub-menu of this option

3) Help - the readme file can be accessed from the main menu and any sub-menus by inputting "Help"

4) Auto update portfolio stock prices - Share Investor provides historical stock data only for subscription users. Therefore for this program which scrapes data from the free site, key financial metrics can only be updated into the database by manually accessing the website using option 1). If there are 20 stocks in the portfolio, executing option 1) twenty times would be an inconvenience. This "auto update portfolio" option allows the user to perform this manual method, automatically.
