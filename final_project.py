import requests
import sqlite3
import json
import pandas as pd
from bs4 import BeautifulSoup
import sys
import io
import webbrowser
import codecs
import plotly.plotly as py
import plotly.graph_objs as go
import pandas_datareader as web
from secrets import key
from secrets import cx
from datetime import datetime
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

# make a call to Google Custom Search to return latest news on a particular stock
def search_google(query):
    title = []
    link = []
    baseurl = "https://www.googleapis.com/customsearch/v1"
    params_diction = {'q':query, 'cr': 'Singapore', 'cx': cx, 'dateRestrict' : 'd[5]', 'key':key}
    results = make_request_using_cache(baseurl,params_diction)
    for a in results['items']:
        title.append(a['title'])
        link.append(a['link'])

    return title, link

CACHE_FNAME = 'searches.json'

try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()

except:
    CACHE_DICTION = {}


def params_unique_combination(baseurl, params_diction):
    alphabetized_keys = sorted(params_diction.keys())
    res = []
    for k in alphabetized_keys:
        res.append("{}-{}".format(k, params_diction[k]))
    return baseurl + "_" + "_".join(res)

def make_request_using_cache(baseurl, params_diction): #search_google
    unique_ident = params_unique_combination(baseurl, params_diction)
    if unique_ident in CACHE_DICTION:
        try:
            if is_fresh(CACHE_DICTION[unique_ident]):
                print("Fetching cached data...")
                return CACHE_DICTION[unique_ident]
        except:
            pass
    else:
        pass

    print("Making a request for new data...")
    resp = requests.get(baseurl, params_diction)
    CACHE_DICTION[unique_ident] = json.loads(resp.text)
    CACHE_DICTION[unique_ident]['cache_timestamp'] = datetime.now().timestamp()
    dumped_json_cache = json.dumps(CACHE_DICTION)
    fw = open(CACHE_FNAME,"w")
    fw.write(dumped_json_cache)
    fw.close()
    return CACHE_DICTION[unique_ident]

# 30 mins refresh rate is set to have a balance between making too many requests to Google API and getting latest news on a particular stock
def is_fresh(cache_entry):
    MAX_STALENESS = 1800 #1800 secs = 30 mins
    now = datetime.now().timestamp()
    staleness = now - cache_entry['cache_timestamp']
    return staleness < MAX_STALENESS

#shareinvestor.com uses a MMM month format which is not recognizable by sqlite
month_dict = {'Jan': '1', 'Feb': '2', 'Mar': '3', 'Apr': '4', 'May': '5', 'Jun': '6', 'Jul': '7', 'Aug': '8', 'Sep': '9', 'Oct': '10', 'Nov': '11', 'Dec': '12'}

def stock_financials(stockcode):
    try:
        baseurl = "https://www.shareinvestor.com/fundamental/factsheet.html?counter="+stockcode+".SI"
        page = request_using_cache1(baseurl)
        page_soup = BeautifulSoup(page, "html.parser")
        h1 = page_soup.find_all(id= "sic_stockQuote_companyInfo")
        name = h1[0].find(class_="sic_fullName")
        dateTime = h1[0].find(class_="sic_dateTime")
        share_price = h1[0].find(class_ = "sic_lastdone")
        td = h1[0].find_all('td')
        remarks = h1[0].find(class_="sic_remarks")
        table = page_soup.find(class_="sic_table sic_tableBigCell")
    except:
        return str("Invalid Stock Code.")

    try:
        with open('stocks.json', encoding ='utf-8') as f:
                stocks = json.load(f)
                stocks_dict = {}
    except:
        stocks=[]
        stocks_dict = {}

    try:
        with open('stock_financials.json', encoding ='utf-8') as g:
                stock_financials = json.load(g)
                stocks_dict1 = {}
    except:
        stock_financials=[]
        stocks_dict1 = {}

    if remarks.find('strong').text == "SUSP":
        print("Stock: " +name.text)
        print("Stock is suspended")
        return None

    elif remarks.find('strong').text == "-":
        stocks_dict["name"] = name.text
        stocks_dict["code"] = stockcode
        j=1
        for i in stocks:
            if name.text == i["name"]:
                j=0
                break
            else:
                j+=1
        if j>0:
            stocks.append(stocks_dict)
            with open("stocks.json","w") as fdesc:
                json.dump(stocks,fdesc)
        else:
            pass

        y= dateTime.text.split(" at ")[1] #date and time of update
        l=1 #using a counter to go through whole json database to check if there are any matching entries
        for i in stock_financials:
            if name.text == i["name"]:
                if (month_dict[y.split(' ')[1]]+"-"+y.split(' ')[0]+"-"+y.split(' ')[2]) == i["date"]:
                    if y.split(' ')[3]>i["time_recorded"]:
                        l+=1
                    else:
                        l=0
                        break
                else:
                    l+=1
            else:
                l+=1

        if l>0: #to check if there are any existing stock_financial entry for the same date and time. This section of code dictates what will be written into stock_financials table
            stocks_dict1["name"] = name.text
            stocks_dict1["date"] = month_dict[y.split(' ')[1]]+"-"+y.split(' ')[0]+"-"+y.split(' ')[2]
            stocks_dict1["time_recorded"] = y.split(' ')[3]
            stocks_dict1["price"] = share_price.find('strong').text
            stocks_dict1["day_highest"]= td[2].find('strong').text
            stocks_dict1["day_lowest"]= td[5].find('strong').text
            stocks_dict1["buying_volume"] = td[15].text
            stocks_dict1["sell_volume"] = td[17].text
            stocks_dict1["eps"] = table.find_all('strong')[0].text
            stocks_dict1["nav"] = table.find_all('strong')[2].text
            stocks_dict1["pe"] = table.find_all('strong')[3].text
            stocks_dict1["price_per_nav"] = table.find_all('strong')[5].text
            stocks_dict1["dps"] = table.find_all('strong')[6].text
            stocks_dict1["cps"] = table.find_all('strong')[7].text
            stocks_dict1["div_yield"] = table.find_all('strong')[9].text
            stocks_dict1["price_per_cashflow"] = table.find_all('strong')[10].text
            stocks_dict1["market_cap"] = table.find_all('strong')[14].text
            stock_financials.append(stocks_dict1)
            with open("stock_financials.json","w") as fdesc1:
                json.dump(stock_financials,fdesc1)
        else:
            pass

        date_time = dateTime.text.split(" at ")[1]
        date = month_dict[y.split(' ')[1]]+"-"+y.split(' ')[0]+"-"+y.split(' ')[2]
        stock_name = name.text
        current_shareprice = share_price.find('strong').text
        day_high = td[2].find('strong').text
        day_low = td[5].find('strong').text
        buy_volume = td[15].text
        sell_volume = td[17].text
        eps = table.find_all('strong')[0].text
        nav = table.find_all('strong')[2].text
        pe_ratio = table.find_all('strong')[3].text
        price_per_nav = table.find_all('strong')[5].text
        dps = table.find_all('strong')[6].text
        cash_in_hand_per_share = table.find_all('strong')[7].text
        div_yield = table.find_all('strong')[9].text
        price_per_cashflow = table.find_all('strong')[10].text
        market_cap = table.find_all('strong')[14].text

        return date_time, date, stock_name, current_shareprice, day_high, day_low, buy_volume, sell_volume, eps, nav, pe_ratio, price_per_nav, dps, cash_in_hand_per_share, div_yield, price_per_cashflow, market_cap

        #when a stock has special news information announced, the table data changes. Hence there is a need for else statement
    else:
        if remarks.find('strong').text == "CD":
            #print("\nDividends announced.")
            pass
        else:
            pass

        stocks_dict["name"] = name.text
        stocks_dict["code"] = stockcode
        j=1
        for i in stocks:
            if name.text == i["name"]:
                j=0
                break
            else:
                j +=1
        if j>0:
            stocks.append(stocks_dict)
            with open("stocks.json","w") as fdesc:
                json.dump(stocks,fdesc)
        else:
            pass

        y= dateTime.text.split(" at ")[1] #date and time of update
        l=1 #using a counter to go through whole json database to check if there are any matching entries
        for i in stock_financials:
            if name.text == i["name"]:
                if (month_dict[y.split(' ')[1]]+"-"+y.split(' ')[0]+"-"+y.split(' ')[2]) == i["date"]:
                    if y.split(' ')[3]>i["time_recorded"]:
                        l+=1
                    else:
                        l=0
                        break
                else:
                    l+=1
            else:
                l+=1

        if l>0: #to check if there are any existing stock_financial entry for the same date and time. This section of code dictates what will be written into stock_financials table
            stocks_dict1["name"] = name.text
            stocks_dict1["date"] = month_dict[y.split(' ')[1]]+"-"+y.split(' ')[0]+"-"+y.split(' ')[2]
            stocks_dict1["time_recorded"] = y.split(' ')[3]
            stocks_dict1["price"] = share_price.find('strong').text
            stocks_dict1["day_highest"]= td[2].find('strong').text
            stocks_dict1["day_lowest"]= td[61].find('strong').text
            stocks_dict1["buying_volume"]=td[71].text
            stocks_dict1["sell_volume"]=td[73].text
            stocks_dict1["eps"] = table.find_all('strong')[0].text
            stocks_dict1["nav"] = table.find_all('strong')[2].text
            stocks_dict1["pe"] = table.find_all('strong')[3].text
            stocks_dict1["price_per_nav"] = table.find_all('strong')[5].text
            stocks_dict1["dps"] = table.find_all('strong')[6].text
            stocks_dict1["cps"] = table.find_all('strong')[7].text
            stocks_dict1["div_yield"] = table.find_all('strong')[9].text
            stocks_dict1["price_per_cashflow"] = table.find_all('strong')[10].text
            stocks_dict1["market_cap"] = table.find_all('strong')[14].text
            stock_financials.append(stocks_dict1)
            with open("stock_financials.json","w") as fdesc1:
                json.dump(stock_financials,fdesc1)
        else:
            pass

        date_time = dateTime.text.split(" at ")[1]
        date = month_dict[y.split(' ')[1]]+"-"+y.split(' ')[0]+"-"+y.split(' ')[2]
        stock_name = name.text
        current_shareprice = share_price.find('strong').text
        day_high = td[2].find('strong').text
        day_low = td[61].find('strong').text
        buy_volume = td[71].text
        sell_volume = td[73].text
        eps = table.find_all('strong')[0].text
        nav = table.find_all('strong')[2].text
        pe_ratio = table.find_all('strong')[3].text
        price_per_nav = table.find_all('strong')[5].text
        dps = table.find_all('strong')[6].text
        cash_in_hand_per_share = table.find_all('strong')[7].text
        div_yield = table.find_all('strong')[9].text
        price_per_cashflow = table.find_all('strong')[10].text
        market_cap = table.find_all('strong')[14].text

        return date_time, date, stock_name, current_shareprice, day_high, day_low, buy_volume, sell_volume, eps, nav, pe_ratio, price_per_nav, dps, cash_in_hand_per_share, div_yield, price_per_cashflow, market_cap

CACHE_FNAME2 = 'shares.json'

try:
    cache_file2 = open(CACHE_FNAME2, 'r')
    cache_contents2 = cache_file2.read()
    CACHE_DICTION2 = json.loads(cache_contents2)
    cache_file2.close()

except:
    CACHE_DICTION2 = {}

def params_unique_combination2(baseurl, params="1"):
    res = []
    res.append(params)
    return baseurl + "_" + "_".join(res)

def request_using_cache1(baseurl): #shareinvestor scraping
    unique_ident = params_unique_combination2(baseurl)
    if baseurl in CACHE_DICTION2:
        try:
            if is_fresh2(CACHE_DICTION2[unique_ident]):
                #print("Fetching cached data...")
                return CACHE_DICTION2[baseurl]
        except:
            pass
    else:
        pass
    #print("Making a request for new data...")
    header = {'User-Agent': 'Chrome'}
    resp = requests.get(baseurl, headers = header)
    CACHE_DICTION2[baseurl] = resp.text
    CACHE_DICTION2[unique_ident] = datetime.now().timestamp() #doing separately because resp.text is a string. A nested dictionary cannot be done if the value is a string instead of dictionary
    dumped_json_cache = json.dumps(CACHE_DICTION2)
    fw = open(CACHE_FNAME2,"w")
    fw.write(dumped_json_cache)
    fw.close()
    return CACHE_DICTION2[baseurl]

def is_fresh2(cache_entry):
    MAX_STALENESS2 = 60 #set 1 min refresh rate
    now = datetime.now().timestamp()
    staleness = now - cache_entry
    return staleness < MAX_STALENESS2


# creating tables in database
def create_db():
    try:
        conn = sqlite3.connect('Stocks_Database.sqlite')

    except:
        print("Error. No database found.")
    cur = conn.cursor()

    # Drop tables
    statement = '''
        DROP TABLE IF EXISTS 'Stocks';
    '''
    cur.execute(statement)

    statement = '''
        DROP TABLE IF EXISTS 'Stocks_List';
    '''
    cur.execute(statement)

    statement = '''
        DROP TABLE IF EXISTS 'Stock_Financials';
    '''
    cur.execute(statement)
    conn.commit()


    statement = '''
        CREATE TABLE 'Stocks' (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                'Name' TEXT NOT NULL,
                'Code' TEXT NOT NULL
        );
    '''
    cur.execute(statement)

    statement = '''
        CREATE TABLE 'Stocks_List' (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                'Name' TEXT NOT NULL,
                'Code' TEXT NOT NULL
        );
    '''
    cur.execute(statement)

    statement = '''
        CREATE TABLE 'Stock_Financials' (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                'Name_ID' TEXT NOT NULL,
                'Date' TEXT NOT NULL,
                'Time_Recorded' TEXT NOT NULL,
                'Price' TEXT NOT NULL,
                'Day_Highest' TEXT NOT NULL,
                'Day_Lowest' TEXT NOT NULL,
                'Buy_Vol' TEXT NOT NULL,
                'Sell_Vol' TEXT NOT NULL,
                'EPS' TEXT NOT NULL,
                'NAV' TEXT NOT NULL,
                'PE' TEXT NOT NULL,
                'Price_per_NAV' TEXT NOT NULL,
                'DPS' TEXT NOT NULL,
                'CPS' TEXT NOT NULL,
                'Div_Yield' TEXT NOT NULL,
                'Price_per_cashflow' TEXT NOT NULL,
                'Market_Cap' TEXT NOT NULL
        );
    '''
    cur.execute(statement)
    conn.commit()
    conn.close()

#inserting cached data from json files into database
def insert_stuff():
    stock_info = []
    stock_info1= []
    conn = sqlite3.connect('Stocks_Database.sqlite')
    cur = conn.cursor()
    try:
        with open('stocks.json', encoding ='utf-8') as f:
            stocks = json.load(f)
        for i in stocks:
            insertion = (None, i['name'], i['code'])
            statement = 'INSERT INTO "Stocks" '
            statement += 'VALUES (?, ?, ?)'
            cur.execute(statement, insertion)
    except:
        pass
    conn.commit()
    conn.close()

    conn = sqlite3.connect('Stocks_Database.sqlite')
    cur = conn.cursor()
    try:
        with open('stocks_list.json', encoding ='utf-8') as f:
            stocks = json.load(f)
        for i in stocks:
            insertion = (None, i['name'], i['code'])
            statement = 'INSERT INTO "Stocks_List" '
            statement += 'VALUES (?, ?, ?)'
            cur.execute(statement, insertion)
        conn.commit()
        conn.close()
    except:
        stockcode_scraping()

    conn = sqlite3.connect('Stocks_Database.sqlite')
    cur = conn.cursor()
    try:
        with open('stock_financials.json', encoding = 'utf-8') as g:
            jsonReader = json.load(g)
            for i in jsonReader:
                stock_info.append(i)

        statement = 'SELECT Id, Name FROM Stocks'
        cur.execute(statement)
        results = cur.fetchall()
        for i in stock_info:
            for j in results:
                if i['name'] == j[1]:
                    stock_info1.append(j[0])
                else:
                    pass
        i=0
        for data in stock_info:
            insertion = (None, stock_info1[i], data['date'], data['time_recorded'], data['price'], data['day_highest'], data['day_lowest'], data['buying_volume'], data['sell_volume'],data['eps'],data['nav'],data['pe'],data['price_per_nav'],data['dps'],data['cps'],data['div_yield'],data['price_per_cashflow'],data['market_cap'])
            statement = 'INSERT INTO "Stock_Financials" '
            statement += 'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
            cur.execute(statement, insertion)
            i+=1
    except:
        pass
    conn.commit()
    conn.close()

# function allows user to add his/her stocks into the portfolio which will be stored in the database. portfolio table is created within the same function
def add_portfolio(stock_name=None, purchased_price=None, no_of_shares=None, date=None, test=0):
    if test==0:
        total_price = float(no_of_shares) * float(purchased_price)
        try:
            with open('stock_portfolio.json', encoding ='utf-8') as f:
                stock_portfolio = json.load(f)
                stock_portfolio_dict = {}
        except:
            stock_portfolio=[]
            stock_portfolio_dict = {}

        stock_portfolio_dict['name'] = stock_name
        stock_portfolio_dict['purchased_price'] = purchased_price
        stock_portfolio_dict['no_of_shares'] = no_of_shares
        stock_portfolio_dict['date'] = date
        stock_portfolio_dict['Total_Amount_Invested'] = str("%0.2f" %float(total_price))
        stock_portfolio.append(stock_portfolio_dict)

        with open("stock_portfolio.json","w") as gdesc1:
            json.dump(stock_portfolio ,gdesc1)
    else:
        pass

    stock_add = []
    stock_add1 = []
    conn = sqlite3.connect('Stocks_Database.sqlite')
    cur = conn.cursor()
    try:
        with open('stock_portfolio.json', encoding = 'utf-8') as g:
            jsonReader = json.load(g)
            for i in jsonReader:
                stock_add.append(i)
    except:
        stock_add = []

    statement = '''
        DROP TABLE IF EXISTS 'Portfolio';
    '''
    cur.execute(statement)
    conn.commit()

    statement = '''
        CREATE TABLE 'Portfolio' (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                'Stock' TEXT NOT NULL,
                'Purchased_Price' TEXT NOT NULL,
                'No_of_Shares' TEXT NOT NULL,
                'Date_Purchased' TEXT NOT NULL,
                'Total_Amount_Invested' TEXT NOT NULL
        );
    '''
    cur.execute(statement)

    statement = 'SELECT Id, Name FROM Stocks'
    cur.execute(statement)
    results = cur.fetchall()
    for i in stock_add:
        for j in results:
            if i['name'] == j[1]:
                stock_add1.append(j[0])
            else:
                pass

    k=0
    for data in stock_add:
        insertion = (None, stock_add1[k], data['purchased_price'], data['no_of_shares'], data['date'], data['Total_Amount_Invested'])
        statement = 'INSERT INTO "Portfolio" '
        statement += 'VALUES (?, ?, ?, ?, ?, ?)'
        cur.execute(statement, insertion)
        k+=1
    conn.commit()
    conn.close()

# function allows user to look at the stocks in his portfolio
def assess_portfolio(sort):
    conn = sqlite3.connect('Stocks_Database.sqlite')
    cur = conn.cursor()
    try:
        statement='''
            SELECT Stocks.Name, Stocks.Code, No_of_Shares, Purchased_Price, Date_Purchased, Total_Amount_Invested, Stock_Financials.Price FROM Portfolio
            JOIN Stocks
            ON Portfolio.Stock = Stocks.Id
            JOIN Stock_Financials
            ON Stocks.Id = Stock_Financials.Name_ID
            Group By {}
        '''.format(sort)
        cur.execute(statement)
        results = cur.fetchall()
        conn.close()
        return results
    except:
        print("Please ensure database is in the same folder before executing the program in future.\n")
        create_db()
        insert_stuff()
        add_portfolio(test=1)


# function allows user to delete the stocks in his portfolio
def delete_from_portfolio(index):
    stock_add = []
    stock_add1 = []
    conn = sqlite3.connect('Stocks_Database.sqlite')
    cur = conn.cursor()

    with open('stock_portfolio.json', encoding = 'utf-8') as f:
        Reader = json.load(f)

    j=0
    shortened_results=[]
    for i in Reader:
        if int(index)-1 != j:
            shortened_results.append(i)
            j+=1
        else:
            j+=1
            pass

    with open("stock_portfolio.json","w") as gdesc1:
        json.dump(shortened_results ,gdesc1)

    with open('stock_portfolio.json', encoding = 'utf-8') as g:
        jsonReader = json.load(g)
        for i in jsonReader:
            stock_add.append(i)

    statement = '''
        DROP TABLE IF EXISTS 'Portfolio';
    '''
    cur.execute(statement)
    conn.commit()

    statement = '''
        CREATE TABLE 'Portfolio' (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                'Stock' TEXT NOT NULL,
                'Purchased_Price' TEXT NOT NULL,
                'No_of_Shares' TEXT NOT NULL,
                'Date_Purchased' TEXT NOT NULL,
                'Total_Amount_Invested' TEXT NOT NULL
        );
    '''
    cur.execute(statement)

    statement = 'SELECT Id, Name FROM Stocks'
    cur.execute(statement)
    results = cur.fetchall()
    for i in stock_add:
        for j in results:
            if i['name'] == j[1]:
                stock_add1.append(j[0])
            else:
                pass

    k=0
    for data in stock_add:
        insertion = (None, stock_add1[k], data['purchased_price'], data['no_of_shares'], data['date'], data['Total_Amount_Invested'])
        statement = 'INSERT INTO "Portfolio" '
        statement += 'VALUES (?, ?, ?, ?, ?, ?)'
        cur.execute(statement, insertion)
        k+=1
    conn.commit()
    conn.close()

# function allows user to look at the stocks in his portfolio and the associated stock financials data
def assess_financials(stock_name,group=""):
    conn = sqlite3.connect('Stocks_Database.sqlite')
    cur = conn.cursor()
    insertion = (stock_name, )
    statement='''
        SELECT Stocks.Name, Stocks.Code, Stock_Financials.Date, Stock_Financials.Time_Recorded, Stock_Financials.Price, Stock_Financials.Day_Highest, Stock_Financials.Day_Lowest, Stock_Financials.Div_Yield, Stock_Financials.EPS, Stock_Financials.Buy_Vol, Stock_Financials.Sell_Vol, Stock_Financials.PE, Stock_Financials.NAV, Stock_Financials.Price_per_cashflow, Stock_Financials.Market_Cap FROM Stocks
        JOIN Stock_Financials
        ON Stocks.Id = Stock_Financials.Name_ID
        WHERE Stocks.Name = ?
        {}
    '''.format(group)
    cur.execute(statement, insertion)
    results = cur.fetchall()
    conn.close()
    return results

# function allows the user to automatically update all financials data in the stocks database with one execution
def auto_update():
    conn = sqlite3.connect('Stocks_Database.sqlite')
    cur = conn.cursor()
    statement='''
        SELECT Stocks.Code, Stocks.Name FROM Stocks
        JOIN Stock_Financials
        ON Stocks.Id = Stock_Financials.Name_ID
        Group BY Stock_Financials.Name_ID
    '''
    cur.execute(statement)
    results = cur.fetchall()
    conn.close()

    if len(results)!= 0:
        for i in results:
            stock_financials(i[0])
            create_db()
            insert_stuff()
        return str("**********Prices in portfolio successfully updated**********")
    else:
        return str("----------There are no stocks in the portfolio----------")

# function allows the user to have all the key financials of a stock plotted in 1 chart
def plot_charts(input8):
    date1 = []
    time_recorded1 = []
    price1 = []
    day_highest1 = []
    day_lowest1 = []
    div_yield1 = []
    eps1 = []
    buy_volume1 = []
    sell_volume1 = []
    pe1 = []
    nav1 = []
    price_per_cashflow1 = []
    market_cap1 = []
    for i in assess_financials(assess_portfolio("Stocks.Name")[int(input8)-1][0], group = "Group BY Stock_Financials.Date"):
        date1.append(i[2])
        time_recorded1.append(i[3])
        price1.append(i[4])
        day_highest1.append(i[5])
        day_lowest1.append(i[6])
        div_yield1.append(i[7])
        eps1.append(i[8])
        buy_volume1.append(i[9])
        sell_volume1.append(i[10])
        pe1.append(i[11])
        nav1.append(i[12])
        price_per_cashflow1.append(i[13])
        market_cap1.append(i[14])

    closing_price = go.Scatter(
                x = date1,
                y = price1, name = 'closing_price')

    div_yield = go.Scatter(
                x = date1,
                y = div_yield1, name = 'dividend yield')

    eps = go.Scatter(
                x = date1,
                y = eps1, name = 'earnings per share')

    pe = go.Scatter(
                x = date1,
                y = pe1, name = 'price per earning ratio')

    nav = go.Scatter(
                x = date1,
                y = nav1, name = 'net asset value')

    price_per_cashflow = go.Scatter(
                x = date1,
                y = price_per_cashflow1, name = 'price per cashflow')

    axis_template = dict(showgrid = True,
                    zeroline = True,
                    nticks=20,
                    showline = True,
                    title = 'Date',
                    mirror = 'all')

    axis_template1 = dict(showgrid = True,
                    zeroline = True,
                    nticks=20,
                    showline = True,
                    title = 'Price ($)',
                    mirror = 'all')

    layout = go.Layout(title = 'Stock Financials',xaxis = axis_template,
                    yaxis = axis_template1,)


    data=[closing_price, div_yield, eps, pe, nav, price_per_cashflow]
    fig = dict( data=data, layout=layout )
    py.plot(fig, filename='Financials Plot' )

# function allows the user to plot the price movement of a stock in 1 chart
def plot_price(input8):
    date1 = []
    price1 = []
    for i in assess_financials(assess_portfolio("Stocks.Name")[int(input8)-1][0], group = "Group BY Stock_Financials.Date"):
        date1.append(i[2])
        price1.append(i[4])

    closing_price = go.Scatter(
                x = date1,
                y = price1, name = 'closing_price')

    axis_template = dict(showgrid = True,
                    zeroline = True,
                    nticks=20,
                    showline = True,
                    title = 'Date',
                    mirror = 'all')

    axis_template1 = dict(showgrid = True,
                    zeroline = True,
                    nticks=20,
                    showline = True,
                    title = 'Price ($)',
                    mirror = 'all')

    layout = go.Layout(title = 'Stock Price Movement',xaxis = axis_template,
                    yaxis = axis_template1,)

    data=[closing_price]
    fig = dict( data=data, layout=layout )
    py.plot(fig, filename='Price Plot' )

    try:
        if float(price1[-1])<float(price1[-2]) and float(price1[-1])<float(price1[-3]):
            return str("Alert! Stock price has been on a decline for three consecutive data collection days.\n")
        else:
            return str("")
    except:
        return str("")

# function allows the user to plot the earnings per share ratio movement of a stock in 1 chart and alerts the user if the earnings per share ratio have been declining for 3 consecutive days
def plot_eps(input8):
    date1 = []
    eps1 = []

    for i in assess_financials(assess_portfolio("Stocks.Name")[int(input8)-1][0], group = "Group BY Stock_Financials.Date"):
        date1.append(i[2])
        eps1.append(i[8])

    eps = go.Scatter(
                x = date1,
                y = eps1, name = 'earnings per share')

    axis_template = dict(showgrid = True,
                    zeroline = True,
                    nticks=20,
                    showline = True,
                    title = 'Date',
                    mirror = 'all')

    axis_template1 = dict(showgrid = True,
                    zeroline = True,
                    nticks=20,
                    showline = True,
                    title = 'EPS',
                    mirror = 'all')

    layout = go.Layout(title = 'Earnings Per Share (EPS) Ratio Movement',xaxis = axis_template,
                    yaxis = axis_template1,)

    data=[eps]
    fig = dict( data=data, layout=layout )
    py.plot(fig, filename='Earnings Per Share Plot' )

    try:
        if float(eps1[-1])<float(eps1[-2]) and float(eps1[-1])<float(eps1[-3]):
            return str("Alert! Earnings per Share ratio has been on a decline for three consecutive data collection days.\n")
        else:
            return str("")
    except:
        return str("")

# function allows the user to plot the net asset value ratio movement of a stock in 1 chart and alerts the user if the net asset value ratio have been declining for 3 consecutive days
def plot_nav(input8):
    date1 = []
    nav1 = []

    for i in assess_financials(assess_portfolio("Stocks.Name")[int(input8)-1][0], group = "Group BY Stock_Financials.Date"):
        date1.append(i[2])
        nav1.append(i[12])

    nav = go.Scatter(
                x = date1,
                y = nav1, name = 'net asset value')

    axis_template = dict(showgrid = True,
                    zeroline = True,
                    nticks=20,
                    showline = True,
                    title = 'Date',
                    mirror = 'all')

    axis_template1 = dict(showgrid = True,
                    zeroline = True,
                    nticks=20,
                    showline = True,
                    title = 'NAV',
                    mirror = 'all')

    layout = go.Layout(title = 'Net Asset Value (NAV) Ratio Movement',xaxis = axis_template,
                    yaxis = axis_template1,)

    data=[nav]
    fig = dict( data=data, layout=layout )
    py.plot(fig, filename='Net Asset Value Plot' )

    try:
        if float(nav1[-1])<float(nav1[-2]) and float(nav1[-1])<float(nav1[-3]):
            return str("Alert! Net Asset Value has been on a decline for three consecutive data collection days.\n")
        else:
            return str("")
    except:
        return str("")

# function allows the user to plot the price-earnings ratio movement of a stock in 1 chart and alerts the user if the price-earnings ratio have been declining for 3 consecutive days
def plot_pe(input8):
    date1 = []
    pe1 = []
    price1 = []

    for i in assess_financials(assess_portfolio("Stocks.Name")[int(input8)-1][0], group = "Group BY Stock_Financials.Date"):
        date1.append(i[2])
        price1.append(i[4])
        pe1.append(i[11])

    pe = go.Scatter(
                x = date1,
                y = pe1, name = 'price earning ratio')

    current_price = go.Scatter(
                x = date1,
                y = price1, name = 'current_price')

    axis_template = dict(showgrid = True,
                    zeroline = True,
                    nticks=20,
                    showline = True,
                    title = 'Date',
                    mirror = 'all')

    axis_template1 = dict(showgrid = True,
                    zeroline = True,
                    nticks=20,
                    showline = True,
                    title = 'PE ratio',
                    mirror = 'all')

    layout = go.Layout(title = 'Price-Earnings Ratio Movement',xaxis = axis_template,
                    yaxis = axis_template1,)

    data=[pe, current_price]
    fig = dict( data=data, layout=layout )
    py.plot(fig, filename='Price Earning Ratio Plot' )

    try:
        if float(pe1[-1])<float(pe1[-2]) and float(pe1[-1])<float(pe1[-3]):
            return str("Alert! Price-Earning ratio has been on a decline for three consecutive data collection days.\n")
        else:
            return str("")
    except:
        return str("")

# function allows the user to plot the dividend yield percentage movement of a stock in 1 chart and alerts the user if the dividend yield percentage movement have been declining for 3 consecutive days
def plot_div_yield(input8):
    date1 = []
    div_yield1 = []

    for i in assess_financials(assess_portfolio("Stocks.Name")[int(input8)-1][0], group = "Group BY Stock_Financials.Date"):
        date1.append(i[2])
        div_yield1.append(i[7])

    div_yield = go.Scatter(
                x = date1,
                y = div_yield1, name = 'dividend yield')

    axis_template = dict(showgrid = True,
                    zeroline = True,
                    nticks=20,
                    showline = True,
                    title = 'Date',
                    mirror = 'all')

    axis_template1 = dict(showgrid = True,
                    zeroline = True,
                    nticks=20,
                    showline = True,
                    title = '%',
                    mirror = 'all')

    layout = go.Layout(title = 'Dividend Yield (%) Movement',xaxis = axis_template,
                    yaxis = axis_template1,)

    data=[div_yield]
    fig = dict( data=data, layout=layout )
    py.plot(fig, filename='Dividend Yield Plot' )

    try:
        if float(div_yield1[-1])<float(div_yield1[-2]) and float(div_yield1[-1])<float(div_yield1[-3]):
            return str("Alert! Dividend Yield has been on a decline for three consecutive data collection days.\n")
        else:
            return str("")
    except:
        return str("")

# function allows the user to plot the price per cashflow ratio movement and the price movement of a stock in 1 chart and alerts the user if the price per cashflo ratio have been declining for 3 consecutive days
def plot_price_cashflow(input8):
    date1 = []
    price_per_cashflow1 = []
    price1 = []

    for i in assess_financials(assess_portfolio("Stocks.Name")[int(input8)-1][0], group = "Group BY Stock_Financials.Date"):
        date1.append(i[2])
        price1.append(i[4])
        price_per_cashflow1.append(i[13])

    price_per_cashflow = go.Scatter(
                x = date1,
                y = price_per_cashflow1, name = 'price_per_cashflow')

    current_price = go.Scatter(
                x = date1,
                y = price1, name = 'current_price')

    axis_template = dict(showgrid = True,
                    zeroline = True,
                    nticks=20,
                    showline = True,
                    title = 'Date',
                    mirror = 'all')

    axis_template1 = dict(showgrid = True,
                    zeroline = True,
                    nticks=20,
                    showline = True,
                    title = 'Price per Cashflo Ratio',
                    mirror = 'all')

    layout = go.Layout(title = 'Price per Cashflow Movement and Current Stock Price comparison',xaxis = axis_template,
                    yaxis = axis_template1,)

    data=[price_per_cashflow, current_price]
    fig = dict( data=data, layout=layout )
    py.plot(fig, filename='Price-per-Cashflow Plot' )

    try:
        if float(price_per_cashflow1[-1])>float(price_per_cashflow1[-2]) and float(price_per_cashflow1[-1])>float(price_per_cashflow1[-3]):
            return str("Alert! Price per Cashflow has been on an increase for three consecutive data collection days.\n")
        else:
            return str("")
    except:
        return str("")

# function allows the user to plot the buy and  sell volume of a stock in 1 chart and alerts the user if the sell volume have been more than buy volume for 3 consecutive days
def plot_volume(input8):
    date1 = []
    buy_volume1 = []
    sell_volume1 = []

    for i in assess_financials(assess_portfolio("Stocks.Name")[int(input8)-1][0], group = "Group BY Stock_Financials.Date"):
        date1.append(i[2])
        buy_volume1.append(i[9])
        sell_volume1.append(i[10])

    buy_volume = go.Scatter(
                x = date1,
                y = buy_volume1, name = "buy volume ('000)")

    sell_volume = go.Scatter(
                x = date1,
                y = sell_volume1, name = "sell volume ('000)")

    axis_template = dict(showgrid = True,
                    zeroline = True,
                    nticks=20,
                    showline = True,
                    title = 'Date',
                    mirror = 'all')

    axis_template1 = dict(showgrid = True,
                    zeroline = True,
                    nticks=20,
                    showline = True,
                    title = "Volume ('000)",
                    mirror = 'all')

    layout = go.Layout(title = 'Stock Buy and Sell volume',xaxis = axis_template,
                    yaxis = axis_template1,)

    data=[buy_volume, sell_volume]
    fig = dict( data=data, layout=layout )
    py.plot(fig, filename='Daily Volume Plot' )

    try:
        if float(sell_volume1[-1]>buy_volume1[-1]) and float(sell_volume1[-2])>float(buy_volume1[-2]) and float(sell_volume1[-3])>float(buy_volume1[-3]):
            return str("Alert! Selling volume has been more than Buying volume for three consecutive data collection days.\n")
        else:
            return str("")
    except:
        return str("")

# function scrapes eoddata.com for the stock codes of each stock listed in the Singapore Stock Exchange. These stock codes are required to access shareinvestor.com which uses stock codes as its url
def stockcode_scraping():
    symbols_on_sgx = ['1','2','3','4','5','6','7','8','9','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
    stock_list1 = []
    for i in symbols_on_sgx:
        baseurl = 'http://eoddata.com/stocklist/SGX/'
        extendedurl = baseurl + i +'.htm'
        results1 = request_using_cache(extendedurl)
        searching = BeautifulSoup(results1, 'html.parser')
        quotes = searching.find_all(class_ = ["ro","re"])
        for j in quotes:
            stock_list = {}
            stock_list['name'] = j.find_all('td')[1].text.upper()
            stock_list['code'] = j.find_all('td')[0].text #print(j.find_all('td')[0].text) #prints symbols #print(j.find_all('td')[1].text) #prints stock names
            stock_list1.append(stock_list)
    with open("stocks_list.json","w") as gdesc1:
        json.dump(stock_list1 ,gdesc1)
    return stock_list1

CACHE_FNAME1 = 'symbols.json'
try:
    cache_file1 = open(CACHE_FNAME1, 'r')
    cache_contents1 = cache_file1.read()
    CACHE_DICTION1 = json.loads(cache_contents1)
    cache_file1.close()

except:
    CACHE_DICTION1 = {}

def params_unique_combination1(baseurl, params="1"):
    res = []
    res.append(params)
    return baseurl + "_" + "_".join(res)

def request_using_cache(extendedurl): #stockcode_scraping
    unique_ident = params_unique_combination1(extendedurl)
    if extendedurl in CACHE_DICTION1:
        try:
            if is_fresh1(CACHE_DICTION1[unique_ident]):
                #print("Fetching cached data...")
                return CACHE_DICTION1[extendedurl]
        except:
            pass
    else:
        pass
    #print("Making a request for new data...")
    resp = requests.get(extendedurl)
    CACHE_DICTION1[extendedurl] = resp.text
    CACHE_DICTION1[unique_ident] = datetime.now().timestamp() #doing separately because resp.text is a string. A nested dictionary cannot be done if the value is a string instead of dictionary
    dumped_json_cache = json.dumps(CACHE_DICTION1)
    fw = open(CACHE_FNAME1,"w")
    fw.write(dumped_json_cache)
    fw.close()
    return CACHE_DICTION1[extendedurl]

def is_fresh1(cache_entry):
    MAX_STALENESS1 = 1296000 #set 0.5 month refresh rate for any potential new IPO listing
    now = datetime.now().timestamp()
    staleness = now - cache_entry
    return staleness < MAX_STALENESS1

def extract_stockcodes(input2):
    extracted_stockcodes = []
    extracted_stocknames = []
    try:
        conn = sqlite3.connect('Stocks_Database.sqlite')
        cur = conn.cursor()
        statement='''
            SELECT Name, Code FROM Stocks_List
            WHERE Name LIKE "%{}%"
            GROUP BY Name
        '''.format(input2)
        cur.execute(statement)
        results = cur.fetchall()
        conn.close()
        for i in results:
            extracted_stockcodes.append(i[1])
            extracted_stocknames.append(i[0])
        return extracted_stockcodes, extracted_stocknames
    except:
        stockcode_scraping()
        create_db()
        insert_stuff()
        conn = sqlite3.connect('Stocks_Database.sqlite')
        cur = conn.cursor()
        statement='''
            SELECT Name, Code FROM Stocks_List
            WHERE Name LIKE "%{}%"
            GROUP BY Name
        '''.format(input2)
        cur.execute(statement)
        results = cur.fetchall()
        conn.close()
        for i in results:
            extracted_stockcodes.append(i[1])
            extracted_stocknames.append(i[0])
        return extracted_stockcodes, extracted_stocknames

# prints help texts when required by the user
def load_help_text():
    with open('help.txt') as f:
        return f.read()


if __name__ == "__main__":
    input1 = ""

    while str(input1)!="5":
        print("-"*50 + "Welcome to Stock Assistant (SG version)" + "-"*50+"\n")
        print("The following options are available for selection.")
        print("0 Re-initialize Database *for maintenance purpose*")
        print("1 Search for a stock")
        print("2 Access your stocks portfolio")
        print("3 Help")
        print("4 Auto update portfolio stocks prices")
        print("5 Exit program")
        print("You may input 'Help' at any time in the sub-menus to access the readme.\n")
        input1 = input("Please input a number from the above options: \n")
        if input1.isdigit():
            if input1 == "0":
                create_db()
                stockcode_scraping()
                insert_stuff()
                add_portfolio(test=1)
                print("Database re-initialized...\n")

            elif input1 == "1":
                input2 = str(input("Please enter the name of the stock to query: ")).upper()
                extracted_stockcodes, extracted_stocknames = extract_stockcodes(input2)
                a = 0
                if len(extracted_stockcodes)>1:
                    for i in extracted_stockcodes:
                        print(str(a+1) + " " + extracted_stocknames[a] + " " + "("+extracted_stockcodes[a]+")")
                        a+=1
                    print(str(a+1)+ " Back to previous menu")
                    print(str(a+2)+ " Exit program")
                elif len(extracted_stockcodes) == 0:
                    print("No stock found.\n")
                    continue
                else:
                    print ("1" + " " + extracted_stocknames[0] + " " + "("+extracted_stockcodes[0]+")")
                    print("2 Back to previous menu\n")

                print("You may input 'Help' at any time to access the readme.\n")
                input3 = input("Please enter the number associated with the stock you wish to query: \n")

                if input3.isdigit():
                    if int(input3)<=len(extracted_stockcodes) and int(input3)>0:
                        print("\nSelected stock is" + " " + extracted_stocknames[int(input3)-1] + " " + "(" + extracted_stockcodes[int(input3)-1] + ")\n")
                        try:
                            date_time, date, stock_name, current_shareprice, day_high, day_low, buy_volume, sell_volume, eps, nav, pe_ratio, price_per_nav, dps, cash_in_hand_per_share, div_yield, price_per_cashflow, market_cap = stock_financials(extracted_stockcodes[int(input3)-1])
                            print("Stock: "+ stock_name)
                            print("Share Price as of " + date+ " is $"+current_shareprice)
                            print("Highest Price reached on "+ date+ " is $" + day_high)
                            print("Lowest Price reached on "+ date+ " is $" + day_low)
                            print("Total buy volume on " + date + " is "+str(round(float(buy_volume.replace(",",""))*1000)))
                            print("Total sell volume on " + date + " is " + str(round(float(sell_volume.replace(",",""))*1000)))
                            print("Earning Per Share for "+ stock_name+ " is $" + eps)
                            print("Net Asset Value for "+ stock_name+ " is " + nav)
                            print("Price per Earning ratio for "+ stock_name+ " is " + pe_ratio)
                            print("Price per Net Asset Value for "+ stock_name+ " is " + price_per_nav)
                            print("Dividend per Share for "+ stock_name+ " is $" + dps)
                            print("Cash-in-hand per Share for "+ stock_name+ " is $" + cash_in_hand_per_share)
                            print("Dividend Yield for "+ stock_name+ " at current share price of "+ current_shareprice+ " is " + div_yield+"%")
                            print("Price per Cashflow for "+ stock_name+ " is $" + price_per_cashflow)
                            print("Market Capitalization for "+ stock_name+ " is ('000) " + market_cap +"\n")
                        except:
                            print(extracted_stocknames[int(input3)-1] + " is not traded on the open market. Please try another stock. Thank you.\n")
                            continue

                        input4 =""
                        while str(input4)!="5":
                            print("The following options are available for selection.\n")
                            print("1 Add this stock to portfolio")
                            print("2 Get latest news on this stock")
                            print("3 Access your stocks portfolio")
                            print("4 Back to previous menu")
                            print("5 Exit program\n")
                            print("You may input 'Help' at any time to access the readme.\n")
                            input4 = input("Please input a number from the above options: ")
                            if input4.isdigit():
                                if input4 == "1":
                                    input5 = input("Please input the purchase price without $: \n")
                                    try:
                                        purchased_price = float(input5)
                                    except:
                                        print("You have entered an invalid input. Please try again or type 'Help' for readme.\n")
                                        continue

                                    no_of_shares = input("Please input the number of shares purchased: \n")
                                    if no_of_shares.isdigit():
                                        print(str(no_of_shares) + " shares of " + stock_name + " purchased at $" + str(purchased_price) + " on " + date + " has been added to the portfolio.\n")
                                        add_portfolio(stock_name, purchased_price, no_of_shares, date)
                                    else:
                                        print("You have entered an invalid input. Please input only whole numbers. Kindly try again or type 'Help' for readme.\n")
                                        continue

                                elif input4 == "2":
                                    title, link = search_google("SGX " + stock_name + " latest news")
                                    j =1
                                    for i in title:
                                        print(str(j) + " "+i + " (" + link[j-1] + ")")
                                        j+=1
                                    print(str(j) + " Back to previous menu")
                                    print(str(j+1) + " Exit program")

                                    input7 = input("\nInput the number associated with the latest news of " + stock_name + " to view in your browser.\n")
                                    if input7.isdigit():
                                        if int(input7)<=len(title) and int(input7)>0:
                                            webbrowser.open(link[int(input7)-1])
                                        elif int(input7)==j:
                                            continue
                                        elif int(input7)==j+1:
                                            print("Bye")
                                            sys.exit()
                                        else:
                                            print("You have entered an input that was out of range. Please try again or type 'Help' for readme.\n")

                                    elif input7.lower() == 'help':
                                        print(load_help_text())
                                    else:
                                        print("Please enter a valid input.\n")

                                elif input4 == "3":
                                    if len(assess_portfolio("Portfolio.Id"))==0:
                                        print("There are no stocks in your portfolio.\n")
                                        continue

                                    else:
                                        print("Accessing your portfolio...\n")
                                        print("The stocks in your portfolio are: \n")
                                        j=1
                                        for i in assess_portfolio("Portfolio.Id"):
                                            print(str(j)+("." + i[0] + " (" + i[1] + ")" + " with " + i[2] + " shares purchased at $" + i[3] + " on " + i[4] + " at a total price of $" + i[5] + ". This stock is currently trading at $" + i[6] + ".\n"))
                                            j+=1

                                        input5=""
                                        while str(input5)!="4":
                                            print("The following options are available for selection.\n")
                                            print("1 Remove a stock from portfolio")
                                            print("2 Analyze portfolio stocks")
                                            print("3 Back to previous menu")
                                            print("4 Exit program")
                                            print("You may input 'Help' at any time to access the readme.\n")
                                            input5 = input("Please input a number from the above options: ")
                                            if input5.isdigit():
                                                if input5 == "1":
                                                    if len(assess_portfolio("Portfolio.Id"))==0:
                                                        print("There are no stocks in your portfolio.\n")
                                                        continue
                                                    else:
                                                        j=1
                                                        for i in assess_portfolio("Portfolio.Id"):
                                                            print(str(j)+("." + i[0] + " (" + i[1] + ")" + " with " + i[2] + " shares purchased at $" + i[3] + " on " + i[4] + " at a total price of $" + i[5] + ". This stock is currently trading at $" + i[6] + ".\n"))
                                                            j+=1

                                                        input6 = input("Please input the associated number from the options above to delete the stock: \n")
                                                        if input6.isdigit():
                                                            if int(input6)<=len(assess_portfolio("Portfolio.Id")) and int(input6)>0:
                                                                delete_from_portfolio(input6)
                                                                j=1
                                                                print("Refreshing portfolio...\n\n")
                                                                print("Your portfolio of stocks are listed below:\n")
                                                                for i in assess_portfolio("Portfolio.Id"):
                                                                    print(str(j)+("." + i[0] + " (" + i[1] + ")" + " with " + i[2] + " shares purchased at $" + i[3] + " on " + i[4] + " at a total price of $" + i[5] + ". This stock is currently trading at $" + i[6] + ".\n"))
                                                                    j+=1

                                                            else:
                                                                print("Please input a digit associated with the above options or type 'Help' for readme.\n")

                                                        elif input6.lower() == "help":
                                                            print(load_help_text())
                                                            continue

                                                        else:
                                                            print("Please input a digit associated with the above options or type 'Help' for readme.\n")
                                                            continue

                                                elif input5 == "2":
                                                    if len(assess_portfolio("Portfolio.Id"))==0:
                                                        print("There are no stocks in your portfolio.\n")
                                                        continue
                                                    else:
                                                        j=1
                                                        print ("The stocks in your portfolio are: \n")
                                                        for i in assess_portfolio("Stocks.Name"):
                                                            print(str(j)+ " " + i[0])
                                                            j+=1

                                                        print("\nGet the stock's latest news and its financials by inputting the associated number or choose " + str(j) + " to return or " + str(j+1) + " to exit the program.\n")
                                                        print(str(j)+" Back to previous menu")
                                                        print(str(j+1)+" Exit program\n")
                                                        print("You may input 'Help' at any time to access the readme.\n")
                                                        input8 = input("Please input a number from the above options: \n")
                                                        if input8.isdigit():
                                                            if int(input8)<=len(assess_portfolio("Stocks.Name")) and int(input8)>0:
                                                                print("\n1 Get the latest news on "+ assess_portfolio("Stocks.Name")[int(input8)-1][0])
                                                                print("2 Get the financials data on " + assess_portfolio("Stocks.Name")[int(input8)-1][0])
                                                                print("3 Back to previous menu")
                                                                print("4 Exit program\n")
                                                                input9 = input("Please input a number from the above options: \n")
                                                                if input9.isdigit():
                                                                    if input9 == "1":
                                                                        title, link = search_google("SGX " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " latest news")
                                                                        j =1
                                                                        for i in title:
                                                                            print(str(j) + " "+i + " (" + link[j-1] + ")")
                                                                            j+=1
                                                                        print(str(j) + " Back to previous menu")
                                                                        print(str(j+1) + " Exit program")

                                                                        input10 = input("\nInput the number associated with the latest news of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " to view in your browser.\n")
                                                                        if input10.isdigit():
                                                                            if int(input10)<=len(title) and int(input10)>0:
                                                                                webbrowser.open(link[int(input10)-1])
                                                                            elif int(input10)==j:
                                                                                continue
                                                                            elif int(input10)==j+1:
                                                                                print("Bye")
                                                                                sys.exit()
                                                                            else:
                                                                                print("You have entered an input that was out of range. Please try again or type 'Help' for readme.\n")
                                                                        else:
                                                                            print("You have entered an invalid entry. Please try again or type 'Help' for readme.\n")

                                                                    elif input9 == "2":
                                                                        date = []
                                                                        time_recorded = []
                                                                        price = []
                                                                        day_highest = []
                                                                        day_lowest = []
                                                                        div_yield = []
                                                                        eps = []
                                                                        buy_volume = []
                                                                        sell_volume = []
                                                                        dps = []
                                                                        nav = []
                                                                        price_per_cashflow = []
                                                                        market_cap = []
                                                                        for i in assess_financials(assess_portfolio("Stocks.Name")[int(input8)-1][0]):
                                                                            date.append(i[2])
                                                                            time_recorded.append(i[3])
                                                                            price.append(i[4])
                                                                            day_highest.append(i[5])
                                                                            day_lowest.append(i[6])
                                                                            div_yield.append(i[7])
                                                                            eps.append(i[8])
                                                                            buy_volume.append(i[9])
                                                                            sell_volume.append(i[10])
                                                                            dps.append(i[11])
                                                                            nav.append(i[12])
                                                                            price_per_cashflow.append(i[13])
                                                                            market_cap.append(i[14])

                                                                        print("The stock prices of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                                        print("Date\t   Time_Recorded\t Price")
                                                                        for i in range(len(date)):
                                                                            print(date[i] + "    " + time_recorded[i] + "\t\t" + price[i])

                                                                        print("\nThe day-high price of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                                        print("Date\t    Time_Recorded\t Highest Price Recorded")
                                                                        for i in range(len(date)):
                                                                            print(date[i] + "     " + time_recorded[i] + "\t\t\t" + day_highest[i])

                                                                        print("\nThe day-low price of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                                        print("Date\t     Time_Recorded\t Lowest Price Recorded")
                                                                        for i in range(len(date)):
                                                                            print(date[i] + "      " + time_recorded[i] + "    \t\t" + day_lowest[i])

                                                                        print("\nThe dividend yield of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                                        print("Date\t    Time_Recorded\t Dividend Yield")
                                                                        for i in range(len(date)):
                                                                            print(date[i] + "  \t" + time_recorded[i] + "     \t\t" + div_yield[i])

                                                                        print("\nThe earnings per share of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                                        print("Date\t    Time_Recorded\t Earnings Per Share")
                                                                        for i in range(len(date)):
                                                                            print(date[i] + "   " + time_recorded[i] + "         \t\t" + eps[i])

                                                                        print("\nThe buy volume of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                                        print("Date\t     Time_Recorded\t Buy Volume")
                                                                        for i in range(len(date)):
                                                                            print(date[i] + "\t" + time_recorded[i] + "    \t\t" + buy_volume[i])

                                                                        print("\nThe sell volume of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                                        print("Date\t\tTime_Recorded\t Sell Volume")
                                                                        for i in range(len(date)):
                                                                            print(date[i] + "\t" + time_recorded[i] + "      \t\t" + sell_volume[i])

                                                                        print("\nThe distribution per share of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                                        print("Date\t\tTime_Recorded\t Dividend per Share")
                                                                        for i in range(len(date)):
                                                                            print(date[i] + "    " + time_recorded[i] + "\t\t\t" + dps[i])

                                                                        print("\nThe net asset value of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                                        print("Date\t    Time_Recorded\t Net Asset Value")
                                                                        for i in range(len(date)):
                                                                            print(date[i] + "      " + time_recorded[i] + "    \t\t" + nav[i])

                                                                        print("\nThe price per cashflow of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                                        print("Date\t   Time_Recorded\t Price per Cashflow")
                                                                        for i in range(len(date)):
                                                                            print(date[i] + "   " + time_recorded[i] + "\t\t\t" + price_per_cashflow[i])

                                                                        print("\nThe market capitalization of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                                        print("Date\t    Time_Recorded\t Market Capitalization ('000)")
                                                                        for i in range(len(date)):
                                                                            print(date[i] + "    " + time_recorded[i] + "       \t\t" + market_cap[i])

                                                                        print("\n\nThe following options are available for selection: \n")
                                                                        print("1 Chart the financials")
                                                                        print("2 Back to previous menu")
                                                                        print("3 Exit program")
                                                                        print("You may input 'Help' at any time to access the readme.\n")
                                                                        input11 = input("Please input a number from the above options: \n")
                                                                        if input11.isdigit():
                                                                            if input11 == "1":
                                                                                print("\n1 Chart Stock's Price")
                                                                                print("2 Chart Stock's Earning Per Share")
                                                                                print("3 Chart Stock's Net Asset Value")
                                                                                print("4 Chart Stock's Price-Earning Ratio")
                                                                                print("5 Chart Stock's Dividend Yield")
                                                                                print("6 Chart Stock's Price per Cashflow")
                                                                                print("7 Chart Stock's Daily Buy and Sell volume")
                                                                                print("8 Chart Stock's Key Financials")
                                                                                print("9 Back to previous menu")
                                                                                print("10 Exit program")
                                                                                print("You may input 'Help' at any time to access the readme.\n")
                                                                                input12 = input("Please select from the options above: \n")
                                                                                if input12.isdigit():
                                                                                    if input12=="1":
                                                                                        print(plot_price(input8))

                                                                                    elif input12 =="2":
                                                                                        print(plot_eps(input8))

                                                                                    elif input12 =="3":
                                                                                        print(plot_nav(input8))

                                                                                    elif input12 =="4":
                                                                                        print(plot_pe(input8))

                                                                                    elif input12 == "5":
                                                                                        print(plot_div_yield(input8))

                                                                                    elif input12 =="6":
                                                                                        print(plot_price_cashflow(input8))

                                                                                    elif input12 == "7":
                                                                                        print(plot_volume(input8))

                                                                                    elif input12 == "8":
                                                                                        plot_charts(input8)

                                                                                    elif input12 == "9":
                                                                                        continue

                                                                                    elif input12 == "10":
                                                                                        print("Bye")
                                                                                        sys.exit()

                                                                                    else:
                                                                                        print("You have entered an input that was out of range. Please try again or type 'Help' for readme.\n")

                                                                                elif input12.lower() == "help":
                                                                                    print(load_help_text())
                                                                                    continue

                                                                                else:
                                                                                    print("You have entered an invalid entry. Please try again or type 'Help' for readme.\n")
                                                                                    continue

                                                                            elif input11 == "2":
                                                                                continue

                                                                            elif input11 == "3":
                                                                                print("Bye")
                                                                                sys.exit()

                                                                        elif input11.lower() == 'help':
                                                                            print(load_help_text())
                                                                            continue

                                                                        else:
                                                                            print("You have entered an input that was out of range. Please try again or type 'Help' for readme.\n")

                                                                    elif input9 == "3":
                                                                        continue

                                                                    elif input9 == "4":
                                                                        print("Bye")
                                                                        sys.exit()

                                                                    else:
                                                                        print("You have entered an input that was out of range. Please try again or type 'Help' for readme.\n")

                                                                elif input9.lower() == "help":
                                                                    print(load_help_text())
                                                                    continue

                                                                else:
                                                                    print("Please input a digit associated with the above options or type 'Help' for readme.\n")

                                                            elif input8.lower() == "help":
                                                                print(load_help_text())
                                                                continue

                                                            elif input8 == str(j):
                                                                continue

                                                            elif input8 == str(j+1):
                                                                print("Bye")
                                                                sys.exit()

                                                            else:
                                                                print("You have entered an invalid entry. Please try again or type 'Help' for readme.\n")
                                                                continue

                                                elif input5 == "3":
                                                    break

                                                elif input5 == "4":
                                                    print("Bye")
                                                    sys.exit()

                                                else:
                                                    print("Please input the number associated with the options above or type 'Help' for readme.\n")
                                                    continue

                                            elif input5.lower() == 'help':
                                                print(load_help_text())
                                                continue

                                            else:
                                                print("Please input the number associated with the options above or type 'Help' for readme.\n")
                                                continue

                                elif input4 == "4":
                                    break

                                elif input4 == "5":
                                    print("Bye")
                                    sys.exit()

                                else:
                                    print("You have entered an invalid entry. Please try again or type 'Help' for readme.\n")
                                    continue

                            elif input4.lower() == "help":
                                print(load_help_text())
                                continue

                            else:
                                print("Please input the number associated with the options above or type 'Help' for readme.\n")
                                continue

                    elif int(input3) == len(extracted_stockcodes)+1:
                        continue

                    elif int(input3) == len(extracted_stockcodes)+2:
                        print("Bye")
                        sys.exit()

                    else:
                        print("You have entered an invalid entry. Please try again or type 'Help' for readme.\n")

                elif input3.lower() == "help":
                    print(load_help_text())

                else:
                    print("You have entered an invalid entry. Please try again or type 'Help' for readme.\n")

            elif input1 == "2":
                try:
                    if len(assess_portfolio("Portfolio.Id"))==0:
                        print("There are no stocks in your portfolio.\n")
                        continue

                    else:
                        print("Assessing your portfolio...\n")
                        print("The stocks in your portfolio are: \n")
                        j=1
                        for i in assess_portfolio("Portfolio.Id"):
                            print(str(j)+("." + i[0] + " (" + i[1] + ")" + " with " + i[2] + " shares purchased at $" + i[3] + " on " + i[4] + " at a total price of $" + i[5] + ". This stock is currently trading at $" + i[6] + ".\n"))
                            j+=1

                except:
                    insert_stuff()
                    print("There are no stocks in your portfolio.\n")
                    continue

                input5=""
                while str(input5)!="4":
                    print("The following options are available for selection.\n")
                    print("1 Remove a stock from portfolio")
                    print("2 Analyze portfolio stocks")
                    print("3 Back to previous menu")
                    print("4 Exit program")
                    print("You may input 'Help' at any time to access the readme.\n")
                    input5 = input("Please input a number from the above options: ")
                    if input5.isdigit():
                        if input5 == "1":
                            if len(assess_portfolio("Portfolio.Id"))==0:
                                print("There are no stocks in your portfolio.\n")
                                continue
                            else:
                                j=1
                                for i in assess_portfolio("Portfolio.Id"):
                                    print(str(j)+("." + i[0] + " (" + i[1] + ")" + " with " + i[2] + " shares purchased at $" + i[3] + " on " + i[4] + " at a total price of $" + i[5] + ". This stock is currently trading at $" + i[6] + ".\n"))
                                    j+=1

                                input6 = input("Please input the associated number from the options above to delete the stock: \n")
                                if input6.isdigit():
                                    if int(input6)<=len(assess_portfolio("Portfolio.Id")) and int(input6)>0:
                                        delete_from_portfolio(input6)
                                        j=1
                                        print("Refreshing portfolio...\n\n")
                                        print("Your portfolio of stocks are listed below:\n")
                                        for i in assess_portfolio("Portfolio.Id"):
                                            print(str(j)+("." + i[0] + " (" + i[1] + ")" + " with " + i[2] + " shares purchased at $" + i[3] + " on " + i[4] + " at a total price of $" + i[5] + ". This stock is currently trading at $" + i[6] + ".\n"))
                                            j+=1

                                    else:
                                        print("Please input a digit associated with the above options or type 'Help' for readme.\n")

                                elif input6.lower() == "help":
                                    print(load_help_text())
                                    continue

                                else:
                                    print("Please input a digit associated with the above option or type 'Help' for readme.\n")
                                    continue

                        elif input5 == "2":
                            if len(assess_portfolio("Portfolio.Id"))==0:
                                print("There are no stocks in your portfolio.\n")
                                continue
                            else:
                                j=1
                                print ("The stocks in your portfolio are: \n")
                                for i in assess_portfolio("Stocks.Name"):
                                    print(str(j)+ " " + i[0])
                                    j+=1

                                print("\nGet the stock's latest news and its financials by inputting the associated number or choose " + str(j) + " to return or " + str(j+1) + " to exit the program.\n")
                                print(str(j)+" Back to previous menu")
                                print(str(j+1)+" Exit program\n")
                                print("You may input 'Help' at any time to access the readme.\n")
                                input8 = input("Please input a number from the above options: \n")
                                if input8.isdigit():
                                    if int(input8)<=len(assess_portfolio("Stocks.Name")) and int(input8)>0:
                                        print("\n1 Get the latest news on "+ assess_portfolio("Stocks.Name")[int(input8)-1][0])
                                        print("2 Get the financials data on " + assess_portfolio("Stocks.Name")[int(input8)-1][0])
                                        print("3 Back to previous menu")
                                        print("4 Exit program\n")
                                        input9 = input("Please input a number from the above options: \n")
                                        if input9.isdigit():
                                            if input9 == "1":
                                                title, link = search_google("SGX " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " latest news")
                                                j =1
                                                for i in title:
                                                    print(str(j) + " "+i + " (" + link[j-1] + ")")
                                                    j+=1
                                                print(str(j) + " Back to previous menu")
                                                print(str(j+1) + "Exit program")

                                                input10 = input("\nInput the number associated with the latest news of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " to view in your browser.\n")
                                                if input10.isdigit():
                                                    if int(input10)<=len(title) and int(input10)>0:
                                                        webbrowser.open(link[int(input10)-1])
                                                    elif int(input10)==j:
                                                        continue
                                                    elif int(input10)==j+1:
                                                        print("Bye")
                                                        sys.exit()
                                                    else:
                                                        print("You have entered an input that was out of range. Please try again or type 'Help' for readme.\n")
                                                else:
                                                    print("You have entered an invalid entry. Please try again or type 'Help' for readme.\n")

                                            elif input9 == "2":
                                                date = []
                                                time_recorded = []
                                                price = []
                                                day_highest = []
                                                day_lowest = []
                                                div_yield = []
                                                eps = []
                                                buy_volume = []
                                                sell_volume = []
                                                dps = []
                                                nav = []
                                                price_per_cashflow = []
                                                market_cap = []
                                                for i in assess_financials(assess_portfolio("Stocks.Name")[int(input8)-1][0]):
                                                    date.append(i[2])
                                                    time_recorded.append(i[3])
                                                    price.append(i[4])
                                                    day_highest.append(i[5])
                                                    day_lowest.append(i[6])
                                                    div_yield.append(i[7])
                                                    eps.append(i[8])
                                                    buy_volume.append(i[9])
                                                    sell_volume.append(i[10])
                                                    dps.append(i[11])
                                                    nav.append(i[12])
                                                    price_per_cashflow.append(i[13])
                                                    market_cap.append(i[14])

                                                print("The stock prices of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                print("Date\t   Time_Recorded\t Price")
                                                for i in range(len(date)):
                                                    print(date[i] + "    " + time_recorded[i] + "\t\t" + price[i])

                                                print("\nThe day-high price of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                print("Date\t    Time_Recorded\t Highest Price Recorded")
                                                for i in range(len(date)):
                                                    print(date[i] + "     " + time_recorded[i] + "\t\t\t" + day_highest[i])

                                                print("\nThe day-low price of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                print("Date\t     Time_Recorded\t Lowest Price Recorded")
                                                for i in range(len(date)):
                                                    print(date[i] + "      " + time_recorded[i] + "    \t\t" + day_lowest[i])

                                                print("\nThe dividend yield of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                print("Date\t    Time_Recorded\t Dividend Yield")
                                                for i in range(len(date)):
                                                    print(date[i] + "  \t" + time_recorded[i] + "     \t\t" + div_yield[i])

                                                print("\nThe earnings per share of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                print("Date\t    Time_Recorded\t Earnings Per Share")
                                                for i in range(len(date)):
                                                    print(date[i] + "   " + time_recorded[i] + "         \t\t" + eps[i])

                                                print("\nThe buy volume of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                print("Date\t     Time_Recorded\t Buy Volume")
                                                for i in range(len(date)):
                                                    print(date[i] + "\t" + time_recorded[i] + "    \t\t" + buy_volume[i])

                                                print("\nThe sell volume of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                print("Date\t\tTime_Recorded\t Sell Volume")
                                                for i in range(len(date)):
                                                    print(date[i] + "\t" + time_recorded[i] + "      \t\t" + sell_volume[i])

                                                print("\nThe distribution per share of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                print("Date\t\tTime_Recorded\t Dividend per Share")
                                                for i in range(len(date)):
                                                    print(date[i] + "    " + time_recorded[i] + "\t\t\t" + dps[i])

                                                print("\nThe net asset value of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                print("Date\t    Time_Recorded\t Net Asset Value")
                                                for i in range(len(date)):
                                                    print(date[i] + "      " + time_recorded[i] + "    \t\t" + nav[i])

                                                print("\nThe price per cashflow of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                print("Date\t   Time_Recorded\t Price per Cashflow")
                                                for i in range(len(date)):
                                                    print(date[i] + "   " + time_recorded[i] + "\t\t\t" + price_per_cashflow[i])

                                                print("\nThe market capitalization of " + assess_portfolio("Stocks.Name")[int(input8)-1][0] + " recorded are: \n")
                                                print("Date\t    Time_Recorded\t Market Capitalization")
                                                for i in range(len(date)):
                                                    print(date[i] + "    " + time_recorded[i] + "       \t\t" + market_cap[i])

                                                print("\n\nThe following options are available for selection: \n")
                                                print("1 Chart the financials")
                                                print("2 Back to previous menu")
                                                print("3 Exit program")
                                                print("You may input 'Help' at any time to access the readme.\n")
                                                input11 = input("Please input a number from the above options: \n")
                                                if input11.isdigit():
                                                    if input11 == "1":
                                                        print("\n1 Chart Stock's Price")
                                                        print("2 Chart Stock's Earning Per Share")
                                                        print("3 Chart Stock's Net Asset Value")
                                                        print("4 Chart Stock's Price-Earning Ratio")
                                                        print("5 Chart Stock's Dividend Yield")
                                                        print("6 Chart Stock's Price per Cashflow")
                                                        print("7 Chart Stock's Daily Buy and Sell volume")
                                                        print("8 Chart Stock's Key Financials")
                                                        print("9 Back to previous menu")
                                                        print("10 Exit program")
                                                        print("You may input 'Help' at any time to access the readme.\n")
                                                        input12 = input("Please select from the options above: \n")
                                                        if input12.isdigit():
                                                            if input12=="1":
                                                                print(plot_price(input8))

                                                            elif input12 =="2":
                                                                print(plot_eps(input8))

                                                            elif input12 =="3":
                                                                print(plot_nav(input8))

                                                            elif input12 =="4":
                                                                print(plot_pe(input8))

                                                            elif input12 == "5":
                                                                print(plot_div_yield(input8))

                                                            elif input12 =="6":
                                                                print(plot_price_cashflow(input8))

                                                            elif input12 == "7":
                                                                print(plot_volume(input8))

                                                            elif input12 == "8":
                                                                plot_charts(input8)

                                                            elif input12 == "9":
                                                                continue

                                                            elif input12 == "10":
                                                                print("Bye")
                                                                sys.exit()

                                                            else:
                                                                print("You have entered an input that was out of range. Please try again or type 'Help' for readme.\n")

                                                        elif input12.lower() == "help":
                                                            print(load_help_text())
                                                            continue

                                                        else:
                                                            print("You have entered an invalid entry. Please try again or type 'Help' for readme.\n")
                                                            continue

                                                    elif input11 == "2":
                                                        continue

                                                    elif input11 == "3":
                                                        print("Bye")
                                                        sys.exit()

                                                elif input11.lower() == 'help':
                                                    print(load_help_text())
                                                    continue

                                                else:
                                                    print("You have entered an input that was out of range. Please try again or type 'Help' for readme.\n")

                                            elif input9 == "3":
                                                continue

                                            elif input9 == "4":
                                                print("Bye")
                                                sys.exit()

                                            else:
                                                print("You have entered an input that was out of range. Please try again or type 'Help' for readme.\n")

                                        elif input9.lower() == "help":
                                            print(load_help_text())
                                            continue

                                        else:
                                            print("Please input a digit associated with the above options or type 'Help' for readme\n.")

                                    elif input8.lower() == "help":
                                        print(load_help_text())
                                        continue

                                    elif input8 == str(j):
                                        continue

                                    elif input8 == str(j+1):
                                        print("Bye")
                                        sys.exit()

                                    else:
                                        print("You have entered an invalid entry. Please try again or type 'Help' for readme.\n")

                        elif input5 == "3":
                            break

                        elif input5 == "4":
                            print("Bye")
                            sys.exit()

                        else:
                            print("Please input a digit associated with the above options or type 'Help' for readme.\n")

                    elif input5.lower() == 'help':
                        print(load_help_text())
                        continue

                    else:
                        print("Please input a digit associated with the above options or type 'Help' for readme.\n")
                        continue
            elif input1 == "3":
                print(load_help_text())
                continue

            elif input1 == "4":
                print("Updating...this may take a while...\n")
                print(auto_update())
                continue

            elif input1 == "5":
                print("Bye")
                sys.exit()
            else:
                print("Please input a digit associated with the above options or type 'Help' for readme.\n")
                continue

        elif input1.lower() == "help":
            print(load_help_text())
            continue

        else:
            print("Please input a digit associated with the above options or type 'Help' for readme.\n")
            continue

    sys.exit()
