import sqlite3
import csv
import json
import codecs
import sys
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

# proj3_choc.py
# You can change anything in this file you want as long as you pass the tests
# and meet the project requirements! You will need to implement several new
# functions.

# Part 1: Read data from CSV and JSON into a new database called choc.db
DBNAME = 'choc.db'
BARSCSV = 'flavors_of_cacao_cleaned.csv'
COUNTRIESJSON = 'countries.json'

def create_db():
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
        with open(BARSCSV) as csvDataFile:
            csvReader = csv.reader(csvDataFile)
    except:
        print("Error. No database found.")
    cur = conn.cursor()

    # Drop tables
    statement = '''
        DROP TABLE IF EXISTS 'Bars';
    '''
    cur.execute(statement)

    statement = '''
        DROP TABLE IF EXISTS 'Countries';
    '''
    cur.execute(statement)
    conn.commit()

    statement = '''
        CREATE TABLE 'Bars' (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                'Company' TEXT NOT NULL,
                'SpecificBeanBarName' TEXT NOT NULL,
                'REF' TEXT NOT NULL,
                'ReviewDate' TEXT NOT NULL,
                'CocoaPercent' REAL NOT NULL,
                'CompanyLocationId' INTEGER NOT NULL,
                'Rating' REAL NOT NULL,
                'BeanType' TEXT NOT NULL,
                'BroadBeanOriginId' INTEGER NOT NULL
        );
    '''
    cur.execute(statement)

    statement = '''
        CREATE TABLE 'Countries' (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                'Alpha2' TEXT NOT NULL,
                'Alpha3' TEXT NOT NULL,
                'EnglishName' TEXT NOT NULL,
                'Region' TEXT NOT NULL,
                'Subregion' TEXT NOT NULL,
                'Population' INTEGER NOT NULL,
                'Area' REAL
        );
    '''
    cur.execute(statement)
    conn.commit()
    conn.close()

flavors_list = []
def insert_stuff():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    with open(COUNTRIESJSON, encoding ='utf-8') as f:
        countries = json.load(f)
    for i in countries:
        insertion = (None, i['alpha2Code'], i['alpha3Code'], i['name'], i['region'], i['subregion'], i['population'], i['area'])
        statement = 'INSERT INTO "Countries" '
        statement += 'VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
        cur.execute(statement, insertion)
    conn.commit()
    conn.close()

    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    with open(BARSCSV, encoding = 'utf-8') as csvDataFile:
        csvReader = csv.reader(csvDataFile)
        for row in csvReader:
            flavors_list.append(row)

    statement = 'SELECT Id, EnglishName FROM Countries'
    cur.execute(statement)
    results = cur.fetchall()

    country_list = []
    origin_list =[]
    for data in flavors_list:
        if data[0] != 'Company':
            for i in results:
                if data[5] == i[1]:
                    country_list.append(i[0])
                else:
                    pass

    for data in flavors_list:
        if data[0] != 'Company':
            for i in results:
                if i[1] == data[8]:
                    origin_list.append(i[0])
                else:
                    if data[8] == "Unknown":
                        origin_list.append("Unknown")
                        break

    i=0
    for data in flavors_list:
        if data[0] != 'Company':
            insertion = (None, data[0], data[1], data[2], data[3], data[4].replace('%',''), country_list[i], data[6], data[7], origin_list[i])
            statement = 'INSERT INTO "Bars" '
            statement += 'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
            cur.execute(statement, insertion)
            i+=1

    conn.commit()
    conn.close()

#create_db()
#insert_stuff()
# Part 2: Implement logic to process user commands


def query_bar(param = None, cmd = None, rating = 'Rating', limit = 'DESC', value = 10):
    results1 = []
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    if param!= None and cmd!= None:
        insertion = (cmd,)
        statement='''
            SELECT SpecificBeanBarName, Company, c1.EnglishName, Rating, CocoaPercent, c2.EnglishName FROM 'Bars'
            JOIN 'Countries' AS c1
            ON Bars.CompanyLocationId=c1.Id
            LEFT JOIN 'Countries' AS c2
            ON Bars.BroadBeanOriginId = c2.Id
            WHERE {} = ?
            ORDER By {} {}
            LIMIT {}
        '''.format(param ,rating, limit, value)
        cur.execute(statement, insertion)
        results = cur.fetchall()
        conn.close()
        for i in results:
            t = i
            lst = list(t)
            lst[4] = str(int(i[4]))+'%'
            results1.append(tuple(lst))
        return (results1)

    else:
        statement='''
            SELECT SpecificBeanBarName, Company, c1.EnglishName, Rating, CocoaPercent, c2.EnglishName FROM 'Bars'
            JOIN 'Countries' AS c1
            ON Bars.CompanyLocationId=c1.Id
            LEFT JOIN 'Countries' AS c2
            ON Bars.BroadBeanOriginId = c2.Id
            ORDER By {} {}
            LIMIT {}
        '''.format(rating, limit, value)
        cur.execute(statement)
        results = cur.fetchall()
        conn.close()
        #print(results)
        for i in results:
            t = i
            lst = list(t)
            lst[4] = str(int(i[4]))+'%'
            results1.append(tuple(lst))
        return (results1)


def load_help_text():
    with open('help.txt') as f:
        return f.read()


def query_company(param = None, cmd = None, rating = 'round(Avg(Rating),1)', limit = 'DESC', value = 10):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    if param!= None and cmd!= None:
        insertion = (cmd,)
        statement='''
            SELECT Company, Countries.EnglishName, {} FROM 'Bars'
            JOIN 'Countries'
            ON Bars.CompanyLocationId=Countries.Id
            WHERE {} = ?
            Group By Bars.Company
            HAVING count(Company)>4
            Order By {} {}
            Limit {}
        '''.format(rating, param, rating,limit, value)
        cur.execute(statement, insertion)
        results = cur.fetchall()
        conn.close()
        return (results)

    else:
        statement='''
            SELECT Company, Countries.EnglishName, {} FROM 'Bars'
            JOIN 'Countries'
            ON Bars.CompanyLocationId=Countries.Id
            Group By Bars.Company
            HAVING count(Company) > 4
            Order By {} {}
            Limit {}
        '''.format(rating, rating, limit, value)
        cur.execute(statement)
        results = cur.fetchall()
        conn.close()
        return (results)


def query_countries(param = 'Bars.CompanyLocationId', cmd = None, rating = 'round(Avg(Rating),1)', limit = 'DESC', value = 10):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    if cmd== None:
        statement='''
            SELECT Countries.EnglishName, Countries.Region, {} FROM 'Bars'
            JOIN 'Countries'
            ON {}=Countries.Id
            Group By {}
            HAVING count(Company)>4
            Order By {} {}
            Limit {}
        '''.format(rating, param, param, rating, limit, value)
        cur.execute(statement)
        results = cur.fetchall()
        conn.close()
        return (results)

    else:
        insertion = (cmd,)
        statement='''
            SELECT Countries.EnglishName, Countries.Region, {} FROM 'Bars'
            JOIN 'Countries'
            ON {}=Countries.Id
            WHERE Countries.Region = ?
            Group By {}
            HAVING count(Company)>4
            Order By {} {}
            Limit {}
        '''.format(rating, param, param, rating, limit, value)
        cur.execute(statement, insertion)
        results = cur.fetchall()
        conn.close()
        return (results)


def query_regions(param = 'Bars.CompanyLocationId', rating = 'round(Avg(Rating),1)', limit = 'DESC', value = 10):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    statement='''
        SELECT Countries.Region, {} FROM 'Bars'
        JOIN 'Countries'
        ON {}=Countries.Id
        Group By Countries.Region
        HAVING count(Company)>4
        Order By {} {}
        Limit {}
    '''.format(rating, param, rating, limit, value)
    cur.execute(statement)
    results = cur.fetchall()
    conn.close()
    return (results)


def process_command(command):
    if len(command.split(' ')) == 1:
        if command.split(' ')[0] == 'bars':
            return query_bar()
        elif command.split(' ')[0]== 'companies':
            return query_company()
        elif command.split(' ')[0]=='countries':
            return query_countries()
        elif command.split(' ')[0]=='regions':
            return query_regions()
        else:
            pass

    elif len(command.split(' ')) == 2:
        if command.split(' ')[0] == 'bars':
            if 'ratings' in command.split(' ')[1] or 'cocoa' in command.split(' ')[1]:
                if 'ratings' == command.split(' ')[1]:
                    return query_bar()
                else:
                    return query_bar(rating = 'CocoaPercent')
            elif 'sellcountry' in command.split(' ')[1] or 'sellregion' in command.split(' ')[1] or 'sourcecountry' in command.split(' ')[1] or 'sourceregion' in command.split(' ')[1]:
                if 'sellcountry' in command.split(' ')[1]:
                    y = command.split(' ')[1].split('=')[1]
                    return query_bar(param = 'c1.Alpha2', cmd = y)
                elif 'sellregion' in command.split(' ')[1]:
                    y = command.split(' ')[1].split('=')[1]
                    return query_bar(param = 'c1.Region', cmd = y)
                elif 'sourcecountry' in command.split(' ')[1]:
                    y = command.split(' ')[1].split('=')[1]
                    return query_bar(param = 'c2.Alpha2', cmd = y)
                else:
                    y = command.split(' ')[1].split('=')[1]
                    return query_bar(param = 'c2.Region', cmd = y)
            elif 'top' in command.split(' ')[1] or 'bottom' in command.split(' ')[1]:
                if 'top' in command.split(' ')[1]:
                    y = command.split(' ')[1].split('=')[1]
                    return query_bar(value = y)
                else:
                    y = command.split(' ')[1].split('=')[1]
                    return query_bar(limit = 'ASC', value = y)
            else:
                print("Command not recognized: " + command)

        elif command.split(' ')[0] == 'companies':
            if 'region' in command.split(' ')[1] or 'country' in command.split(' ')[1]:
                if 'region' in command.split(' ')[1]:
                    y = command.split(' ')[1].split('=')[1]
                    return query_company(param = 'Countries.Region', cmd = y)
                else:
                    y = command.split(' ')[1].split('=')[1]
                    return query_company(param = 'Countries.Alpha2', cmd = y)
            elif 'ratings' in command.split(' ')[1] or 'cocoa' in command.split(' ')[1] or 'bars_sold' in command.split(' ')[1]:
                if 'ratings' in command.split(' ')[1]:
                    return query_company()
                elif 'cocoa' in command.split(' ')[1]:
                    return query_company(rating = 'round(avg(CocoaPercent),1)')
                else:
                    return query_company(rating = 'count(Company)')
            elif 'top' in command.split(' ')[1] or 'bottom' in command.split(' ')[1]:
                if 'top' in command.split(' ')[1]:
                    y = command.split(' ')[1].split('=')[1]
                    return query_company(value = y)
                else:
                    y = command.split(' ')[1].split('=')[1]
                    return query_company(limit = 'ASC', value = y)
            else:
                print("Command not recognized: " + command)

        elif command.split(' ')[0] == 'countries':
            if 'sellers' in command.split(' ')[1] or 'sources' in command.split(' ')[1]:
                if 'sellers' == command.split(' ')[1]:
                    return query_countries()
                else:
                    return query_countries(param = "Bars.BroadBeanOriginId")
            elif 'ratings' in command.split(' ')[1] or 'cocoa' in command.split(' ')[1] or 'bars_sold' in command.split(' ')[1]:
                if 'ratings' == command.split(' ')[1]:
                    return query_countries()
                elif 'cocoa' == command.split(' ')[1]:
                    return query_countries(rating = 'round(avg(CocoaPercent),1)')
                else:
                    return query_countries(rating = 'count(Company)')
            elif 'top' in command.split(' ')[1] or 'bottom' in command.split(' ')[1]:
                if 'top' in command.split(' ')[1]:
                    y = command.split(' ')[1].split('=')[1]
                    return query_countries(value = y)
                else:
                    y = command.split(' ')[1].split('=')[1]
                    return query_countries(limit = 'ASC', value = y)
            elif 'region' in command.split(' ')[1]:
                y = command.split(' ')[1].split('=')[1]
                return query_countries(cmd = y)

            else:
                print("Command not recognized: " + command)

        elif command.split(' ')[0] == 'regions':
            if 'sellers' in command.split(' ')[1] or 'sources' in command.split(' ')[1]:
                if 'sellers' == command.split(' ')[1]:
                    return query_regions()
                else:
                    return query_regions(param = 'Bars.BroadBeanOriginId')
            elif 'ratings' in command.split(' ')[1] or 'cocoa' in command.split(' ')[1] or 'bars_sold' in command.split(' ')[1]:
                if 'ratings' == command.split(' ')[1]:
                    return query_regions()
                elif 'cocoa' == command.split(' ')[1]:
                    return query_regions(rating = 'round(avg(CocoaPercent),1)')
                else:
                    return query_regions(rating = 'count(Company)')
            elif 'top' in command.split(' ')[1] or 'bottom' in command.split(' ')[1]:
                if 'top' in command.split(' ')[1]:
                    y = command.split(' ')[1].split('=')[1]
                    return query_regions(value = y)
                else:
                    y = command.split(' ')[1].split('=')[1]
                    return query_regions(limit = 'ASC', value = y)
            else:
                print("Command not recognized: " + command)
    elif len(command.split(' ')) == 3:
        if command.split(' ')[0] == 'bars':
            if 'sellcountry' in command.split(' ')[1] or 'sellregion' in command.split(' ')[1] or 'sourcecountry' in command.split(' ')[1] or 'sourceregion' in command.split(' ')[1]:
                if 'sellcountry' in command.split(' ')[1]:
                    if 'ratings' in command.split(' ')[2] or 'cocoa' in command.split(' ')[2]:
                        if 'ratings' == command.split(' ')[2]:
                            y = command.split(' ')[1].split('=')[1]
                            return query_bar(param = 'c1.Alpha2', cmd = y)
                        elif 'cocoa' in command.split(' ')[2]:
                            y = command.split(' ')[1].split('=')[1]
                            return query_bar(param = 'c1.Alpha2', cmd = y, rating = 'CocoaPercent')

                elif 'sellregion' in command.split(' ')[1]:
                    if 'ratings' in command.split(' ')[2] or 'cocoa' in command.split(' ')[2]:
                        if 'ratings' == command.split(' ')[2]:
                            y = command.split(' ')[1].split('=')[1]
                            return query_bar(param = 'c1.Region', cmd = y)
                        elif 'cocoa' in command.split(' ')[2]:
                            y = command.split(' ')[1].split('=')[1]
                            return query_bar(param = 'c1.Region', cmd = y, rating = 'CocoaPercent')
                elif 'sourcecountry' in command.split(' ')[1]:
                    if 'ratings' in command.split(' ')[2] or 'cocoa' in command.split(' ')[2]:
                        if 'ratings' == command.split(' ')[2]:
                            y = command.split(' ')[1].split('=')[1]
                            return query_bar(param = 'c2.Alpha2', cmd = y)
                        elif 'cocoa' in command.split(' ')[2]:
                            y = command.split(' ')[1].split('=')[1]
                            return query_bar(param = 'c2.Alpha2', cmd = y, rating = 'CocoaPercent')
                else:
                    if 'ratings' in command.split(' ')[2] or 'cocoa' in command.split(' ')[2]:
                        if 'ratings' == command.split(' ')[2]:
                            y = command.split(' ')[1].split('=')[1]
                            return query_bar(param = 'c1.Region', cmd = y)
                        elif 'cocoa' in command.split(' ')[2]:
                            y = command.split(' ')[1].split('=')[1]
                            return query_bar(param = 'c1.Region', cmd = y, rating = 'CocoaPercent')
            elif 'ratings' in command.split(' ')[1] or 'cocoa' in command.split(' ')[1]:
                if 'ratings' == command.split(' ')[1]:
                    if 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                        if 'top' in command.split(' ')[2]:
                            y = command.split(' ')[2].split('=')[1]
                            return query_bar(value = y)
                        else:
                            y = command.split(' ')[2].split('=')[1]
                            return query_bar(limit = 'ASC', value = y)
                else:
                    if 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                        if 'top' in command.split(' ')[2]:
                            y = command.split(' ')[2].split('=')[1]
                            return query_bar(rating = 'CocoaPercent',value = y)
                        else:
                            y = command.split(' ')[2].split('=')[1]
                            return query_bar(rating = 'CocoaPercent', limit = 'ASC', value = y)
            else:
                print("Command not recognized: " + command)

        elif command.split(' ')[0] == 'companies':
            if 'region' in command.split(' ')[1] or 'country' in command.split(' ')[1]:
                if 'region' in command.split(' ')[1]:
                    if 'ratings' in command.split(' ')[2] or 'cocoa' in command.split(' ')[2] or 'bars_sold' in command.split(' ')[2]:
                        if 'ratings' == command.split(' ')[2]:
                            y = command.split(' ')[1].split('=')[1]
                            return query_company(param = 'Countries.Region', cmd = y)
                        elif 'cocoa' == command.split(' ')[2]:
                            y = command.split(' ')[1].split('=')[1]
                            return query_company(param = 'Countries.Region', cmd = y, rating = 'round(avg(CocoaPercent),1)')
                        else:
                            y = command.split(' ')[1].split('=')[1]
                            return query_company(param = 'Countries.Region', cmd = y, rating = 'count(Company)')
                    elif 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                        if 'top' in command.split(' ')[2]:
                            y = command.split(' ')[1].split('=')[1]
                            z = command.split(' ')[2].split('=')[1]
                            return query_company(param = 'Countries.Region', cmd = y, value = z)
                        else:
                            y = command.split(' ')[1].split('=')[1]
                            z = command.split(' ')[2].split('=')[1]
                            return query_company(param = 'Countries.Region', cmd = y, limit = 'ASC', value = z)
                    else:
                        print("Command not recognized: " + command)

                else:
                    if 'ratings' in command.split(' ')[2] or 'cocoa' in command.split(' ')[2] or 'bars_sold' in command.split(' ')[2]:
                        if 'ratings' == command.split(' ')[2]:
                            y = command.split(' ')[1].split('=')[1]
                            return query_company(param = 'Countries.Alpha2', cmd = y)
                        elif 'cocoa' == command.split(' ')[2]:
                            y = command.split(' ')[1].split('=')[1]
                            return query_company(param = 'Countries.Alpha2', cmd = y, rating = 'round(avg(CocoaPercent),1)')
                        else:
                            y = command.split(' ')[1].split('=')[1]
                            return query_company(param = 'Countries.Alpha2', cmd = y, rating = 'count(Company)')
                    elif 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                        if 'top' in command.split(' ')[2]:
                            y = command.split(' ')[1].split('=')[1]
                            z = command.split(' ')[2].split('=')[1]
                            return query_company(param = 'Countries.Alpha2', cmd = y, value = z)
                        else:
                            y = command.split(' ')[1].split('=')[1]
                            z = command.split(' ')[2].split('=')[1]
                            return query_company(param = 'Countries.Alpha2', cmd = y, limit = 'ASC', value = z)
                    else:
                        print("Command not recognized: " + command)
            elif 'ratings' in command.split(' ')[1] or 'cocoa' in command.split(' ')[1] or 'bars_sold' in command.split(' ')[1]:
                if 'ratings' == command.split(' ')[1]:
                    if 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                        if 'top'in command.split(' ')[2]:
                            y=command.split(' ')[2].split('=')[1]
                            return query_company(value = y)
                        else:
                            y=command.split(' ')[2].split('=')[1]
                            return query_company(limit = 'ASC', value = y)
                elif 'cocoa' in command.split(' ')[1]:
                    if 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                        if 'top'in command.split(' ')[2]:
                            y=command.split(' ')[2].split('=')[1]
                            return query_company(rating = 'round(avg(CocoaPercent),1)', value = y)
                        else:
                            y=command.split(' ')[2].split('=')[1]
                            return query_company(rating = 'round(avg(CocoaPercent),1)',limit = 'ASC', value = y)
                else:
                    if 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                        if 'top'in command.split(' ')[2]:
                            y=command.split(' ')[2].split('=')[1]
                            return query_company(rating = 'count(Company)', value = y)
                        else:
                            y=command.split(' ')[2].split('=')[1]
                            return query_company(rating = 'count(Company)',limit = 'ASC', value = y)
            else:
                print("Command not recognized: " + command)

        elif command.split(' ')[0] == 'countries':
            if 'sellers' in command.split(' ')[1] or 'sources' in command.split(' ')[1]:
                if 'sellers' == command.split(' ')[1]:
                    if 'ratings' in command.split(' ')[2] or 'cocoa' in command.split(' ')[2] or 'bars_sold' in command.split(' ')[2]:
                        if 'ratings' == command.split(' ')[2]:
                            return query_countries()
                        elif 'cocoa' == command.split(' ')[2]:
                            return query_countries(rating = 'round(avg(CocoaPercent),1)')
                        else:
                            return query_countries(rating = 'count(Company)')
                else:
                    if 'ratings' in command.split(' ')[2] or 'cocoa' in command.split(' ')[2] or 'bars_sold' in command.split(' ')[2]:
                        if 'ratings' == command.split(' ')[2]:
                            return query_countries(param = "Bars.BroadBeanOriginId")
                        elif 'cocoa' == command.split(' ')[2]:
                            return query_countries(param = "Bars.BroadBeanOriginId",rating = 'round(avg(CocoaPercent),1)')
                        else:
                            return query_countries(param = "Bars.BroadBeanOriginId",rating = 'count(Company)')
            elif 'ratings' in command.split(' ')[1] or 'cocoa' in command.split(' ')[1] or 'bars_sold' in command.split(' ')[1]:
                if 'ratings' == command.split(' ')[1]:
                    if 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                        if 'top' in command.split(' ')[2]:
                            y = command.split(' ')[2].split('=')[1]
                            return query_countries(value = y)
                        else:
                            y = command.split(' ')[2].split('=')[1]
                            return query_countries(limit = 'ASC', value = y)
            elif 'region' in command.split(' ')[1]:
                y = command.split(' ')[1].split('=')[1]
                if 'ratings' == command.split(' ')[2]:
                    return query_countries(cmd = y)
                elif 'cocoa' == command.split(' ')[2]:
                    return query_countries(cmd = y, rating = 'round(avg(CocoaPercent),1)')
                elif 'bars_sold' == command.split(' ')[2]:
                    return query_countries(cmd = y, rating = 'count(Company)')
                else:
                    print("Command not recognized: " + command)

            else:
                print("Command not recognized: " + command)

        else:
            if 'sellers' in command.split(' ')[1] or 'sources' in command.split(' ')[1]:
                if 'sellers' == command.split(' ')[1]:
                    if 'ratings' in command.split(' ')[2] or 'cocoa' in command.split(' ')[2] or 'bars_sold' in command.split(' ')[2]:
                        if 'ratings' == command.split(' ')[2]:
                            return query_regions()
                        elif 'cocoa' == command.split(' ')[2]:
                            return query_regions(rating = 'round(avg(CocoaPercent),1)')
                        else:
                            return query_regions(rating = 'count(Company)')
                    elif 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                        if 'top' in command.split(' ')[2]:
                            y = command.split(' ')[2].split('=')[1]
                            return query_regions(value = y)
                        else:
                            y = command.split(' ')[2].split('=')[1]
                            return query_regions(limit = 'ASC',value = y)
                elif 'sources' == command.split(' ')[1]:
                    if 'ratings' in command.split(' ')[2] or 'cocoa' in command.split(' ')[2] or 'bars_sold' in command.split(' ')[2]:
                        if 'ratings' == command.split(' ')[2]:
                            return query_regions(param = 'Bars.BroadBeanOriginId')
                        elif 'cocoa' == command.split(' ')[2]:
                            return query_regions(param = 'Bars.BroadBeanOriginId',rating = 'round(avg(CocoaPercent),1)')
                        else:
                            return query_regions(param = 'Bars.BroadBeanOriginId',rating = 'count(Company)')
                    elif 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                        if 'top' in command.split(' ')[2]:
                            y = command.split(' ')[2].split('=')[1]
                            return query_regions(param = 'Bars.BroadBeanOriginId',value = y)
                        else:
                            y = command.split(' ')[2].split('=')[1]
                            return query_regions(param = 'Bars.BroadBeanOriginId',limit = 'ASC',value = y)
                else:
                    print("Command not recognized: " + command)
            elif 'ratings' in command.split(' ')[1] or 'cocoa' in command.split(' ')[1] or 'bars_sold' in command.split(' ')[1]:
                if 'ratings' == command.split(' ')[1]:
                    if 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                        if 'top' in command.split(' ')[2]:
                            y = command.split(' ')[2].split('=')[1]
                            return query_regions(value = y)
                        else:
                            y = command.split(' ')[2].split('=')[1]
                            return query_regions(limit = 'ASC', value = y)
                    else:
                        print("Command not recognized: " + command)
                elif 'cocoa' == command.split(' ')[1]:
                    if 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                        if 'top' in command.split(' ')[2]:
                            y = command.split(' ')[2].split('=')[1]
                            return query_regions(rating = 'round(avg(CocoaPercent),1)',value = y)
                        else:
                            y = command.split(' ')[2].split('=')[1]
                            return query_regions(rating = 'round(avg(CocoaPercent),1)',limit = 'ASC', value = y)
                    else:
                        print("Command not recognized: " + command)
                else:
                    if 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                        if 'top' in command.split(' ')[2]:
                            y = command.split(' ')[2].split('=')[1]
                            return query_regions(rating = 'count(Company)',value = y)
                        else:
                            y = command.split(' ')[2].split('=')[1]
                            return query_regions(rating = 'count(Company)',limit = 'ASC', value = y)
                    else:
                        print("Command not recognized: " + command)
            else:
                print("Command not recognized: " + command)

    elif len(command.split(' ')) == 4:
        if command.split(' ')[0] == 'bars':
            if 'sellcountry' in command.split(' ')[1]:
                y = command.split(' ')[1].split('=')[1]
                if 'ratings' in command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_bar(param = 'c1.Alpha2', cmd = y, value = z)
                    elif 'bottom' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_bar(param = 'c1.Alpha2', cmd = y, limit = 'ASC', value = z)
                    else:
                        print("Command not recognized: " + command)
                elif 'cocoa' in command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_bar(param = 'c1.Alpha2', cmd = y, rating = 'CocoaPercent',value = z)
                    elif 'bottom' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_bar(param = 'c1.Alpha2', cmd = y, rating = 'CocoaPercent',limit = 'ASC', value = z)
                    else:
                        print("Command not recognized: " + command)
                else:
                    print("Command not recognized: " + command)
            elif 'sellregion' in command.split(' ')[1]:
                y = command.split(' ')[1].split('=')[1]
                if 'ratings' in command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_bar(param = 'c1.Region', cmd = y, value = z)
                    elif 'bottom' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_bar(param = 'c1.Region', cmd = y, limit = 'ASC', value = z)
                    else:
                        print("Command not recognized: " + command)
                elif 'cocoa' in command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_bar(param = 'c1.Region', cmd = y, rating = 'CocoaPercent',value = z)
                    elif 'bottom' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_bar(param = 'c1.Region', cmd = y, rating = 'CocoaPercent',limit = 'ASC', value = z)
                    else:
                        print("Command not recognized: " + command)
                else:
                    print("Command not recognized: " + command)
            elif 'sourcecountry' in command.split(' ')[1]:
                y = command.split(' ')[1].split('=')[1]
                if 'ratings' in command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_bar(param = 'c2.Alpha2', cmd = y, value = z)
                    elif 'bottom' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_bar(param = 'c2.Alpha2', cmd = y, limit = 'ASC', value = z)
                    else:
                        print("Command not recognized: " + command)
                elif 'cocoa' in command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_bar(param = 'c2.Alpha2', cmd = y, rating = 'CocoaPercent',value = z)
                    elif 'bottom' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_bar(param = 'c2.Alpha2', cmd = y, rating = 'CocoaPercent',limit = 'ASC', value = z)
                    else:
                        print("Command not recognized: " + command)
                else:
                    print("Command not recognized: " + command)
            elif 'sourceregion' in command.split(' ')[1]:
                y = command.split(' ')[1].split('=')[1]
                if 'ratings' in command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_bar(param = 'c2.Region', cmd = y, value = z)
                    elif 'bottom' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_bar(param = 'c2.Region', cmd = y, limit = 'ASC', value = z)
                    else:
                        print("Command not recognized: " + command)
                elif 'cocoa' in command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_bar(param = 'c2.Region', cmd = y, rating = 'CocoaPercent',value = z)
                    elif 'bottom' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_bar(param = 'c2.Region', cmd = y, rating = 'CocoaPercent',limit = 'ASC', value = z)
                    else:
                        print("Command not recognized: " + command)
                else:
                    print("Command not recognized: " + command)
            else:
                print("Command not recognized: " + command)

        elif command.split(' ')[0] == 'companies':
            if 'region' in command.split(' ')[1]:
                y = command.split(' ')[1].split('=')[1]
                if 'ratings' == command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_company(param = 'Countries.Region', cmd = y, value = z)
                    elif 'bottom' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_company(param = 'Countries.Region', cmd = y, limit = 'ASC',value = z)
                    else:
                        print("Command not recognized: " + command)
                elif 'cocoa' == command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_company(param = 'Countries.Region', cmd = y, rating = 'round(avg(CocoaPercent),1)',value = z)
                    elif 'bottom' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_company(param = 'Countries.Region', cmd = y, rating = 'round(avg(CocoaPercent),1)',limit = 'ASC',value = z)
                    else:
                        print("Command not recognized: " + command)
                elif 'bars_sold' == command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_company(param = 'Countries.Region', cmd = y, rating = 'count(Company)',value = z)
                    elif 'bottom' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_company(param = 'Countries.Region', cmd = y, rating = 'count(Company)',limit = 'ASC',value = z)
                    else:
                        print("Command not recognized: " + command)
                else:
                    print("Command not recognized: " + command)
            elif 'country' in command.split(' ')[1]:
                y = command.split(' ')[1].split('=')[1]
                if 'ratings' == command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_company(param = 'Countries.Alpha2', cmd = y, value = z)
                    elif 'bottom' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_company(param = 'Countries.Alpha2', cmd = y, limit = 'ASC',value = z)
                    else:
                        print("Command not recognized: " + command)
                elif 'cocoa' == command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_company(param = 'Countries.Alpha2', cmd = y, rating = 'round(avg(CocoaPercent),1)',value = z)
                    elif 'bottom' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_company(param = 'Countries.Alpha2', cmd = y, rating = 'round(avg(CocoaPercent),1)',limit = 'ASC',value = z)
                    else:
                        print("Command not recognized: " + command)
                elif 'bars_sold' == command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_company(param = 'Countries.Alpha2', cmd = y, rating = 'count(Company)',value = z)
                    elif 'bottom' in command.split(' ')[3]:
                        z = command.split(' ')[3].split('=')[1]
                        return query_company(param = 'Countries.Alpha2', cmd = y, rating = 'count(Company)',limit = 'ASC',value = z)
                    else:
                        print("Command not recognized: " + command)
                else:
                    print("Command not recognized: " + command)
            else:
                print("Command not recognized: " + command)

        elif command.split(' ')[0] == 'countries':
            if 'sellers' in command.split(' ')[1]:
                if 'ratings' == command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_countries(value = y)
                    elif 'bottom' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_countries(limit = 'ASC',value = y)
                    else:
                        print("Command not recognized: " + command)
                elif 'cocoa' == command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_countries(rating = 'round(avg(CocoaPercent),1)',value = y)
                    elif 'bottom' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_countries(rating = 'round(avg(CocoaPercent),1)',limit = 'ASC',value = y)
                    else:
                        print("Command not recognized: " + command)
                elif 'bars_sold' == command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_countries(rating = 'count(Company)',value = y)
                    elif 'bottom' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_countries(rating = 'count(Company)',limit = 'ASC',value = y)
                    else:
                        print("Command not recognized: " + command)
            elif 'sources' in command.split(' ')[1]:
                if 'ratings' == command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_countries(param = "Bars.BroadBeanOriginId",value = y)
                    elif 'bottom' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_countries(param = "Bars.BroadBeanOriginId",limit = 'ASC',value = y)
                    else:
                        print("Command not recognized: " + command)
                elif 'cocoa' == command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_countries(param = "Bars.BroadBeanOriginId",rating = 'round(avg(CocoaPercent),1)',value = y)
                    elif 'bottom' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_countries(param = "Bars.BroadBeanOriginId",rating = 'round(avg(CocoaPercent),1)',limit = 'ASC',value = y)
                    else:
                        print("Command not recognized: " + command)
                elif 'bars_sold' in command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_countries(param = "Bars.BroadBeanOriginId",rating = 'count(Company)',value = y)
                    elif 'bottom' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_countries(param = "Bars.BroadBeanOriginId",rating = 'count(Company)',limit = 'ASC',value = y)
                    else:
                        print("Command not recognized: " + command)
            else:
                print("Command not recognized: " + command)

        elif command.split(' ')[0] == 'regions':
            if 'sellers' in command.split(' ')[1]:
                if 'ratings' == command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_regions(value = y)
                    elif 'bottom' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_regions(limit = 'ASC',value = y)
                    else:
                        print("Command not recognized: " + command)
                elif 'cocoa' == command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_regions(rating = 'round(avg(CocoaPercent),1)',value = y)
                    elif 'bottom' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_regions(rating = 'round(avg(CocoaPercent),1)',limit = 'ASC',value = y)
                    else:
                        print("Command not recognized: " + command)
                elif 'bars_sold' == command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_regions(rating = 'count(Company)',value = y)
                    elif 'bottom' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_regions(rating = 'count(Company)',limit = 'ASC',value = y)
                    else:
                        print("Command not recognized: " + command)
            elif 'sources' in command.split(' ')[1]:
                if 'ratings' == command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_regions(param = 'Bars.BroadBeanOriginId',value = y)
                    elif 'bottom' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_regions(param = 'Bars.BroadBeanOriginId',limit = 'ASC',value = y)
                    else:
                        print("Command not recognized: " + command)
                elif 'cocoa' == command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_regions(param = 'Bars.BroadBeanOriginId',rating = 'round(avg(CocoaPercent),1)',value = y)
                    elif 'bottom' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_regions(param = 'Bars.BroadBeanOriginId',rating = 'round(avg(CocoaPercent),1)',limit = 'ASC',value = y)
                    else:
                        print("Command not recognized: " + command)
                elif 'bars_sold' == command.split(' ')[2]:
                    if 'top' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_regions(param = 'Bars.BroadBeanOriginId',rating = 'count(Company)',value = y)
                    elif 'bottom' in command.split(' ')[3]:
                        y = command.split(' ')[3].split('=')[1]
                        return query_regions(param = 'Bars.BroadBeanOriginId',rating = 'count(Company)',limit = 'ASC',value = y)
                    else:
                        print("Command not recognized: " + command)
                else:
                    print("Command not recognized: " + command)
            else:
                print("Command not recognized: " + command)
        else:
            print("Command not recognized: " + command)
    else:
        print("Command not recognized: " + command)

# Part 3: Implement interactive prompt. We've started for you!


def interactive_prompt():
    width = 31
    help_text = load_help_text()
    command = ''
    command1 = ''
    while command != 'exit':
        command1 = input('Enter a command or input Help to view help text or Exit to quit: ')
        command = command1.lower()
        try:
            if command == 'help':
                print(help_text)

            elif len(command.split(' '))== 1:
                if command.split(' ')[0] == 'bars':
                    for i in process_command('bars'):
                        j=0
                        string=""
                        while j<(len(i)):
                            string += f'{str((i[j])): <{width}}'
                            j+=1
                        print(string)
                    print('\n')
                elif command.split(' ')[0] == 'companies':
                    for i in process_command('companies'):
                        j=0
                        string=""
                        while j<(len(i)):
                            string += f'{str((i[j])): <{width}}'
                            j+=1
                        print(string)
                    print('\n')
                elif command.split(' ')[0] == 'countries':
                    for i in process_command('countries'):
                        j=0
                        string=""
                        while j<(len(i)):
                            string += f'{str((i[j])): <{width}}'
                            j+=1
                        print(string)
                    print('\n')
                elif command.split(' ')[0] == 'regions':
                    for i in process_command('regions'):
                        j=0
                        string=""
                        while j<(len(i)):
                            string += f'{str((i[j])): <{width}}'
                            j+=1
                        print(string)
                    print('\n')
                elif command.split(' ')[0] == 'exit':
                    print("Bye")
                else:
                    print("Command not recognized: " + command)
            elif len(command.split(' '))== 2:
                if command.split(' ')[0] == 'bars':
                    if 'ratings' in command.split(' ')[1] or 'cocoa' in command.split(' ')[1]:
                        if 'ratings' == command.split(' ')[1]:
                            for i in process_command('bars ratings'):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                        else:
                            for i in process_command('bars cocoa'):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                    elif 'sellcountry' in command.split(' ')[1] or 'sellregion' in command.split(' ')[1] or 'sourcecountry' in command.split(' ')[1] or 'sourceregion' in command.split(' ')[1]:
                        if 'sellcountry' in command.split(' ')[1]:
                            y = command.split(' ')[1].split('=')[1]
                            for i in query_bar(param = 'c1.Alpha2', cmd = y):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                        elif 'sellregion' in command.split(' ')[1]:
                            y = command.split(' ')[1].split('=')[1]
                            for i in query_bar(param = 'c1.Region', cmd = y):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                        elif 'sourcecountry' in command.split(' ')[1]:
                            y = command.split(' ')[1].split('=')[1]
                            for i in query_bar(param = 'c2.Alpha2', cmd = y):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                        else:
                            y = command.split(' ')[1].split('=')[1]
                            for i in query_bar(param = 'c2.Region', cmd = y):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                    elif 'top' in command.split(' ')[1] or 'bottom' in command.split(' ')[1]:
                        if 'top' in command.split(' ')[1]:
                            y = command.split(' ')[1].split('=')[1]
                            for i in query_bar(value = y):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                        else:
                            y = command.split(' ')[1].split('=')[1]
                            for i in query_bar(limit = 'ASC', value = y):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                    else:
                        pass
                elif command.split(' ')[0] == 'companies':
                    if 'region' in command.split(' ')[1] or 'country' in command.split(' ')[1]:
                        if 'region' in command.split(' ')[1]:
                            y = command.split(' ')[1].split('=')[1]
                            for i in query_company(param = 'Countries.Region', cmd = y):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                        else:
                            y = command.split(' ')[1].split('=')[1]
                            for i in query_company(param = 'Countries.Alpha2', cmd = y):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                    elif 'ratings' in command.split(' ')[1] or 'cocoa' in command.split(' ')[1] or 'bars_sold' in command.split(' ')[1]:
                        if 'ratings' in command.split(' ')[1]:
                            for i in query_company():
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                        elif 'cocoa' in command.split(' ')[1]:
                            for i in query_company(rating = 'round(avg(CocoaPercent),1)'):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                        else:
                            for i in query_company(rating = 'count(Company)'):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                    elif 'top' in command.split(' ')[1] or 'bottom' in command.split(' ')[1]:
                        if 'top' in command.split(' ')[1]:
                            y = command.split(' ')[1].split('=')[1]
                            for i in query_company(value = y):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                        else:
                            y = command.split(' ')[1].split('=')[1]
                            for i in query_company(limit = 'ASC', value = y):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                    else:
                        print("Command not recognized: " + command)
                elif command.split(' ')[0] == 'countries':
                    if 'sellers' in command.split(' ')[1] or 'sources' in command.split(' ')[1]:
                        if 'sellers' == command.split(' ')[1]:
                            for i in query_countries():
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                        else:
                            for i in query_countries(param = "Bars.BroadBeanOriginId"):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                    elif 'ratings' in command.split(' ')[1] or 'cocoa' in command.split(' ')[1] or 'bars_sold' in command.split(' ')[1]:
                        if 'ratings' == command.split(' ')[1]:
                            for i in query_countries():
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                        elif 'cocoa' == command.split(' ')[1]:
                            for i in query_countries(rating = 'round(avg(CocoaPercent),1)'):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                        else:
                            for i in query_countries(rating = 'count(Company)'):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                    elif 'top' in command.split(' ')[1] or 'bottom' in command.split(' ')[1]:
                        if 'top' in command.split(' ')[1]:
                            y = command.split(' ')[1].split('=')[1]
                            for i in query_countries(value = y):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                        else:
                            y = command.split(' ')[1].split('=')[1]
                            for i in query_countries(limit = 'ASC', value = y):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                    elif 'region' in command.split(' ')[1]:
                        y = command.split(' ')[1].split('=')[1]
                        for i in query_countries(cmd = y):
                            j=0
                            string=""
                            while j<(len(i)):
                                string += f'{str((i[j])): <{width}}'
                                j+=1
                            print(string)
                        print('\n')
                    else:
                        print("Command not recognized: " + command)

                elif command.split(' ')[0] == 'regions':
                    if 'sellers' in command.split(' ')[1] or 'sources' in command.split(' ')[1]:
                        if 'sellers' == command.split(' ')[1]:
                            for i in query_regions():
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                        else:
                            for i in query_regions(param = 'Bars.BroadBeanOriginId'):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                    elif 'ratings' in command.split(' ')[1] or 'cocoa' in command.split(' ')[1] or 'bars_sold' in command.split(' ')[1]:
                        if 'ratings' == command.split(' ')[1]:
                            for i in query_regions():
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                        elif 'cocoa' == command.split(' ')[1]:
                            for i in query_regions(rating = 'round(avg(CocoaPercent),1)'):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                        else:
                            for i in query_regions(rating = 'count(Company)'):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                    elif 'top' in command.split(' ')[1] or 'bottom' in command.split(' ')[1]:
                        if 'top' in command.split(' ')[1]:
                            y = command.split(' ')[1].split('=')[1]
                            for i in query_regions(value = y):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                        else:
                            y = command.split(' ')[1].split('=')[1]
                            for i in query_regions(limit = 'ASC', value = y):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                    else:
                        print("Command not recognized: " + command)
                else:
                    print("Command not recognized: " + command)
            elif len(command.split(' ')) == 3:
                if command.split(' ')[0] == 'bars':
                    if 'sellcountry' in command.split(' ')[1] or 'sellregion' in command.split(' ')[1] or 'sourcecountry' in command.split(' ')[1] or 'sourceregion' in command.split(' ')[1]:
                        if 'sellcountry' in command.split(' ')[1]:
                            if 'ratings' in command.split(' ')[2] or 'cocoa' in command.split(' ')[2]:
                                if 'ratings' == command.split(' ')[2]:
                                    y = command.split(' ')[1].split('=')[1]
                                    for i in query_bar(param = 'c1.Alpha2', cmd = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                elif 'cocoa' in command.split(' ')[2]:
                                    y = command.split(' ')[1].split('=')[1]
                                    for i in query_bar(param = 'c1.Alpha2', cmd = y, rating = 'CocoaPercent'):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                        elif 'sellregion' in command.split(' ')[1]:
                            if 'ratings' in command.split(' ')[2] or 'cocoa' in command.split(' ')[2]:
                                if 'ratings' == command.split(' ')[2]:
                                    y = command.split(' ')[1].split('=')[1]
                                    for i in query_bar(param = 'c1.Region', cmd = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                elif 'cocoa' in command.split(' ')[2]:
                                    y = command.split(' ')[1].split('=')[1]
                                    for i in query_bar(param = 'c1.Region', cmd = y, rating = 'CocoaPercent'):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                        elif 'sourcecountry' in command.split(' ')[1]:
                            if 'ratings' in command.split(' ')[2] or 'cocoa' in command.split(' ')[2]:
                                if 'ratings' == command.split(' ')[2]:
                                    y = command.split(' ')[1].split('=')[1]
                                    for i in query_bar(param = 'c2.Alpha2', cmd = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                elif 'cocoa' in command.split(' ')[2]:
                                    y = command.split(' ')[1].split('=')[1]
                                    for i in query_bar(param = 'c2.Alpha2', cmd = y, rating = 'CocoaPercent'):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                        else:
                            if 'ratings' in command.split(' ')[2] or 'cocoa' in command.split(' ')[2]:
                                if 'ratings' == command.split(' ')[2]:
                                    y = command.split(' ')[1].split('=')[1]
                                    for i in query_bar(param = 'c1.Region', cmd = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                elif 'cocoa' in command.split(' ')[2]:
                                    y = command.split(' ')[1].split('=')[1]
                                    for i in query_bar(param = 'c1.Region', cmd = y, rating = 'CocoaPercent'):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                    elif 'ratings' in command.split(' ')[1] or 'cocoa' in command.split(' ')[1]:
                        if 'ratings' == command.split(' ')[1]:
                            if 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                                if 'top' in command.split(' ')[2]:
                                    y = command.split(' ')[2].split('=')[1]
                                    for i in query_bar(value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                else:
                                    y = command.split(' ')[2].split('=')[1]
                                    for i in query_bar(limit = 'ASC', value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                        else:
                            if 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                                if 'top' in command.split(' ')[2]:
                                    y = command.split(' ')[2].split('=')[1]
                                    for i in query_bar(rating = 'CocoaPercent',value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                else:
                                    y = command.split(' ')[2].split('=')[1]
                                    for i in query_bar(rating = 'CocoaPercent', limit = 'ASC', value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                    else:
                        print("Command not recognized: " + command)
                elif command.split(' ')[0] == 'companies':
                    if 'region' in command.split(' ')[1] or 'country' in command.split(' ')[1]:
                        if 'region' in command.split(' ')[1]:
                            if 'ratings' in command.split(' ')[2] or 'cocoa' in command.split(' ')[2] or 'bars_sold' in command.split(' ')[2]:
                                if 'ratings' == command.split(' ')[2]:
                                    y = command.split(' ')[1].split('=')[1]
                                    for i in query_company(param = 'Countries.Region', cmd = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                elif 'cocoa' == command.split(' ')[2]:
                                    y = command.split(' ')[1].split('=')[1]
                                    for i in query_company(param = 'Countries.Region', cmd = y, rating = 'round(avg(CocoaPercent),1)'):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                else:
                                    y = command.split(' ')[1].split('=')[1]
                                    for i in query_company(param = 'Countries.Region', cmd = y, rating = 'count(Company)'):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                            elif 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                                if 'top' in command.split(' ')[2]:
                                    y = command.split(' ')[1].split('=')[1]
                                    z = command.split(' ')[2].split('=')[1]
                                    for i in query_company(param = 'Countries.Region', cmd = y, value = z):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                else:
                                    y = command.split(' ')[1].split('=')[1]
                                    z = command.split(' ')[2].split('=')[1]
                                    for i in query_company(param = 'Countries.Region', cmd = y, limit = 'ASC', value = z):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                            else:
                                print("Command not recognized: " + command)
                        else:
                            if 'ratings' in command.split(' ')[2] or 'cocoa' in command.split(' ')[2] or 'bars_sold' in command.split(' ')[2]:
                                if 'ratings' == command.split(' ')[2]:
                                    y = command.split(' ')[1].split('=')[1]
                                    for i in query_company(param = 'Countries.Alpha2', cmd = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                elif 'cocoa' == command.split(' ')[2]:
                                    y = command.split(' ')[1].split('=')[1]
                                    for i in query_company(param = 'Countries.Alpha2', cmd = y, rating = 'round(avg(CocoaPercent),1)'):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                else:
                                    y = command.split(' ')[1].split('=')[1]
                                    for i in query_company(param = 'Countries.Alpha2', cmd = y, rating = 'count(Company)'):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                            elif 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                                if 'top' in command.split(' ')[2]:
                                    y = command.split(' ')[1].split('=')[1]
                                    z = command.split(' ')[2].split('=')[1]
                                    for i in query_company(param = 'Countries.Alpha2', cmd = y, value = z):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                else:
                                    y = command.split(' ')[1].split('=')[1]
                                    z = command.split(' ')[2].split('=')[1]
                                    for i in query_company(param = 'Countries.Alpha2', cmd = y, limit = 'ASC', value = z):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                            else:
                                print("Command not recognized: " + command)
                    elif 'ratings' in command.split(' ')[1] or 'cocoa' in command.split(' ')[1] or 'bars_sold' in command.split(' ')[1]:
                        if 'ratings' == command.split(' ')[1]:
                            if 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                                if 'top'in command.split(' ')[2]:
                                    y=command.split(' ')[2].split('=')[1]
                                    for i in query_company(value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                else:
                                    y=command.split(' ')[2].split('=')[1]
                                    for i in query_company(limit = 'ASC', value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                        elif 'cocoa' in command.split(' ')[1]:
                            if 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                                if 'top'in command.split(' ')[2]:
                                    y=command.split(' ')[2].split('=')[1]
                                    for i in query_company(rating = 'round(avg(CocoaPercent),1)', value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                else:
                                    y=command.split(' ')[2].split('=')[1]
                                    for i in query_company(rating = 'round(avg(CocoaPercent),1)',limit = 'ASC', value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                        else:
                            if 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                                if 'top'in command.split(' ')[2]:
                                    y=command.split(' ')[2].split('=')[1]
                                    for i in query_company(rating = 'count(Company)', value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                else:
                                    y=command.split(' ')[2].split('=')[1]
                                    for i in query_company(rating = 'count(Company)',limit = 'ASC', value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                    else:
                        print("Command not recognized: " + command)
                elif command.split(' ')[0] == 'countries':
                    if 'sellers' in command.split(' ')[1] or 'sources' in command.split(' ')[1]:
                        if 'sellers' == command.split(' ')[1]:
                            if 'ratings' in command.split(' ')[2] or 'cocoa' in command.split(' ')[2] or 'bars_sold' in command.split(' ')[2]:
                                if 'ratings' == command.split(' ')[2]:
                                    for i in query_countries():
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                elif 'cocoa' == command.split(' ')[2]:
                                    for i in query_countries(rating = 'round(avg(CocoaPercent),1)'):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                else:
                                    for i in query_countries(rating = 'count(Company)'):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                        else:
                            if 'ratings' in command.split(' ')[2] or 'cocoa' in command.split(' ')[2] or 'bars_sold' in command.split(' ')[2]:
                                if 'ratings' == command.split(' ')[2]:
                                    for i in query_countries(param = "Bars.BroadBeanOriginId"):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                elif 'cocoa' == command.split(' ')[2]:
                                    for i in query_countries(param = "Bars.BroadBeanOriginId",rating = 'round(avg(CocoaPercent),1)'):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                else:
                                    return query_countries(param = "Bars.BroadBeanOriginId",rating = 'count(Company)')
                                    for i in query_countries(param = "Bars.BroadBeanOriginId",rating = 'count(Company)'):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                    elif 'ratings' in command.split(' ')[1] or 'cocoa' in command.split(' ')[1] or 'bars_sold' in command.split(' ')[1]:
                        if 'ratings' == command.split(' ')[1]:
                            if 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                                if 'top' in command.split(' ')[2]:
                                    y = command.split(' ')[2].split('=')[1]
                                    for i in query_countries(value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                else:
                                    y = command.split(' ')[2].split('=')[1]
                                    for i in query_countries(limit = 'ASC', value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                    elif 'region' in command.split(' ')[1]:
                        y = command.split(' ')[1].split('=')[1]
                        if 'ratings' == command.split(' ')[2]:
                            for i in query_countries(cmd = y):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                        elif 'cocoa' == command.split(' ')[2]:
                            for i in query_countries(cmd = y, rating = 'round(avg(CocoaPercent),1)'):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                        elif 'bars_sold' == command.split(' ')[2]:
                            for i in query_countries(cmd = y, rating = 'count(Company)'):
                                j=0
                                string=""
                                while j<(len(i)):
                                    string += f'{str((i[j])): <{width}}'
                                    j+=1
                                print(string)
                            print('\n')
                        else:
                            print("Command not recognized: " + command)
                    else:
                        print("Command not recognized: " + command)
                else:
                    if 'sellers' in command.split(' ')[1] or 'sources' in command.split(' ')[1]:
                        if 'sellers' == command.split(' ')[1]:
                            if 'ratings' in command.split(' ')[2] or 'cocoa' in command.split(' ')[2] or 'bars_sold' in command.split(' ')[2]:
                                if 'ratings' == command.split(' ')[2]:
                                    for i in query_regions():
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                elif 'cocoa' == command.split(' ')[2]:
                                    for i in query_regions(rating = 'round(avg(CocoaPercent),1)'):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                else:
                                    for i in query_regions(rating = 'count(Company)'):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                            elif 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                                if 'top' in command.split(' ')[2]:
                                    y = command.split(' ')[2].split('=')[1]
                                    for i in query_regions(value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                else:
                                    y = command.split(' ')[2].split('=')[1]
                                    for i in query_regions(limit = 'ASC',value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                        elif 'sources' == command.split(' ')[1]:
                            if 'ratings' in command.split(' ')[2] or 'cocoa' in command.split(' ')[2] or 'bars_sold' in command.split(' ')[2]:
                                if 'ratings' == command.split(' ')[2]:
                                    for i in query_regions(param = 'Bars.BroadBeanOriginId'):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                elif 'cocoa' == command.split(' ')[2]:
                                    for i in query_regions(param = 'Bars.BroadBeanOriginId',rating = 'round(avg(CocoaPercent),1)'):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                else:
                                    for i in query_regions(param = 'Bars.BroadBeanOriginId',rating = 'count(Company)'):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                            elif 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                                if 'top' in command.split(' ')[2]:
                                    y = command.split(' ')[2].split('=')[1]
                                    for i in query_regions(param = 'Bars.BroadBeanOriginId',value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                else:
                                    y = command.split(' ')[2].split('=')[1]
                                    for i in query_regions(param = 'Bars.BroadBeanOriginId',limit = 'ASC',value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                        else:
                            print("Command not recognized: " + command)
                    elif 'ratings' in command.split(' ')[1] or 'cocoa' in command.split(' ')[1] or 'bars_sold' in command.split(' ')[1]:
                        if 'ratings' == command.split(' ')[1]:
                            if 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                                if 'top' in command.split(' ')[2]:
                                    y = command.split(' ')[2].split('=')[1]
                                    for i in query_regions(value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                else:
                                    y = command.split(' ')[2].split('=')[1]
                                    for i in query_regions(limit = 'ASC', value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                            else:
                                print("Command not recognized: " + command)
                        elif 'cocoa' == command.split(' ')[1]:
                            if 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                                if 'top' in command.split(' ')[2]:
                                    y = command.split(' ')[2].split('=')[1]
                                    for i in query_regions(rating = 'round(avg(CocoaPercent),1)',value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                else:
                                    y = command.split(' ')[2].split('=')[1]
                                    for i in query_regions(rating = 'round(avg(CocoaPercent),1)',limit = 'ASC', value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                            else:
                                print("Command not recognized: " + command)
                        else:
                            if 'top' in command.split(' ')[2] or 'bottom' in command.split(' ')[2]:
                                if 'top' in command.split(' ')[2]:
                                    y = command.split(' ')[2].split('=')[1]
                                    for i in query_regions(rating = 'count(Company)',value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                                else:
                                    y = command.split(' ')[2].split('=')[1]
                                    for i in query_regions(rating = 'count(Company)',limit = 'ASC', value = y):
                                        j=0
                                        string=""
                                        while j<(len(i)):
                                            string += f'{str((i[j])): <{width}}'
                                            j+=1
                                        print(string)
                                    print('\n')
                            else:
                                print("Command not recognized: " + command)
                    else:
                        print("Command not recognized: " + command)

            elif len(command.split(' ')) == 4:
                if command.split(' ')[0] == 'bars':
                    if 'sellcountry' in command.split(' ')[1]:
                        y = command.split(' ')[1].split('=')[1]
                        if 'ratings' in command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_bar(param = 'c1.Alpha2', cmd = y, value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_bar(param = 'c1.Alpha2', cmd = y, limit = 'ASC', value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        elif 'cocoa' in command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_bar(param = 'c1.Alpha2', cmd = y, rating = 'CocoaPercent',value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_bar(param = 'c1.Alpha2', cmd = y, rating = 'CocoaPercent',limit = 'ASC', value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        else:
                            print("Command not recognized: " + command)
                    elif 'sellregion' in command.split(' ')[1]:
                        y = command.split(' ')[1].split('=')[1]
                        if 'ratings' in command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_bar(param = 'c1.Region', cmd = y, value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_bar(param = 'c1.Region', cmd = y, limit = 'ASC', value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        elif 'cocoa' in command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_bar(param = 'c1.Region', cmd = y, rating = 'CocoaPercent',value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_bar(param = 'c1.Region', cmd = y, rating = 'CocoaPercent',limit = 'ASC', value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        else:
                            print("Command not recognized: " + command)
                    elif 'sourcecountry' in command.split(' ')[1]:
                        y = command.split(' ')[1].split('=')[1]
                        if 'ratings' in command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_bar(param = 'c2.Alpha2', cmd = y, value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_bar(param = 'c2.Alpha2', cmd = y, limit = 'ASC', value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        elif 'cocoa' in command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_bar(param = 'c2.Alpha2', cmd = y, rating = 'CocoaPercent',value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_bar(param = 'c2.Alpha2', cmd = y, rating = 'CocoaPercent',limit = 'ASC', value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        else:
                            print("Command not recognized: " + command)
                    elif 'sourceregion' in command.split(' ')[1]:
                        y = command.split(' ')[1].split('=')[1]
                        if 'ratings' in command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_bar(param = 'c2.Region', cmd = y, value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_bar(param = 'c2.Region', cmd = y, limit = 'ASC', value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        elif 'cocoa' in command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_bar(param = 'c2.Region', cmd = y, rating = 'CocoaPercent',value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_bar(param = 'c2.Region', cmd = y, rating = 'CocoaPercent',limit = 'ASC', value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        else:
                            print("Command not recognized: " + command)
                    else:
                        print("Command not recognized: " + command)

                elif command.split(' ')[0] == 'companies':
                    if 'region' in command.split(' ')[1]:
                        y = command.split(' ')[1].split('=')[1]
                        if 'ratings' == command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_company(param = 'Countries.Region', cmd = y, value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_company(param = 'Countries.Region', cmd = y, limit = 'ASC',value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        elif 'cocoa' == command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_company(param = 'Countries.Region', cmd = y, rating = 'round(avg(CocoaPercent),1)',value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_company(param = 'Countries.Region', cmd = y, rating = 'round(avg(CocoaPercent),1)',limit = 'ASC',value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        elif 'bars_sold' == command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_company(param = 'Countries.Region', cmd = y, rating = 'count(Company)',value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_company(param = 'Countries.Region', cmd = y, rating = 'count(Company)',limit = 'ASC',value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        else:
                            print("Command not recognized: " + command)
                    elif 'country' in command.split(' ')[1]:
                        y = command.split(' ')[1].split('=')[1]
                        if 'ratings' == command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_company(param = 'Countries.Alpha2', cmd = y, value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_company(param = 'Countries.Alpha2', cmd = y, limit = 'ASC',value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        elif 'cocoa' == command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_company(param = 'Countries.Alpha2', cmd = y, rating = 'round(avg(CocoaPercent),1)',value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_company(param = 'Countries.Alpha2', cmd = y, rating = 'round(avg(CocoaPercent),1)',limit = 'ASC',value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        elif 'bars_sold' == command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_company(param = 'Countries.Alpha2', cmd = y, rating = 'count(Company)',value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                z = command.split(' ')[3].split('=')[1]
                                for i in query_company(param = 'Countries.Alpha2', cmd = y, rating = 'count(Company)',limit = 'ASC',value = z):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        else:
                            print("Command not recognized: " + command)
                    else:
                        print("Command not recognized: " + command)

                elif command.split(' ')[0] == 'countries':
                    if 'sellers' in command.split(' ')[1]:
                        if 'ratings' == command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_countries(value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_countries(limit = 'ASC',value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        elif 'cocoa' == command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_countries(rating = 'round(avg(CocoaPercent),1)',value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_countries(rating = 'round(avg(CocoaPercent),1)',limit = 'ASC',value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        elif 'bars_sold' == command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_countries(rating = 'count(Company)',value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_countries(rating = 'count(Company)',limit = 'ASC',value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                    elif 'sources' in command.split(' ')[1]:
                        if 'ratings' == command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_countries(param = "Bars.BroadBeanOriginId",value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_countries(param = "Bars.BroadBeanOriginId",limit = 'ASC',value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        elif 'cocoa' == command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_countries(param = "Bars.BroadBeanOriginId",rating = 'round(avg(CocoaPercent),1)',value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_countries(param = "Bars.BroadBeanOriginId",rating = 'round(avg(CocoaPercent),1)',limit = 'ASC',value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        elif 'bars_sold' in command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_countries(param = "Bars.BroadBeanOriginId",rating = 'count(Company)',value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_countries(param = "Bars.BroadBeanOriginId",rating = 'count(Company)',limit = 'ASC',value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                    else:
                        print("Command not recognized: " + command)

                elif command.split(' ')[0] == 'regions':
                    if 'sellers' in command.split(' ')[1]:
                        if 'ratings' == command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_regions(value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_regions(limit = 'ASC',value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        elif 'cocoa' == command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_regions(rating = 'round(avg(CocoaPercent),1)',value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_regions(rating = 'round(avg(CocoaPercent),1)',limit = 'ASC',value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        elif 'bars_sold' == command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_regions(rating = 'count(Company)',value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_regions(rating = 'count(Company)',limit = 'ASC',value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                    elif 'sources' in command.split(' ')[1]:
                        if 'ratings' == command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_regions(param = 'Bars.BroadBeanOriginId',value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_regions(param = 'Bars.BroadBeanOriginId',limit = 'ASC',value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        elif 'cocoa' == command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_regions(param = 'Bars.BroadBeanOriginId',rating = 'round(avg(CocoaPercent),1)',value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_regions(param = 'Bars.BroadBeanOriginId',rating = 'round(avg(CocoaPercent),1)',limit = 'ASC',value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        elif 'bars_sold' == command.split(' ')[2]:
                            if 'top' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_regions(param = 'Bars.BroadBeanOriginId',rating = 'count(Company)',value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            elif 'bottom' in command.split(' ')[3]:
                                y = command.split(' ')[3].split('=')[1]
                                for i in query_regions(param = 'Bars.BroadBeanOriginId',rating = 'count(Company)',limit = 'ASC',value = y):
                                    j=0
                                    string=""
                                    while j<(len(i)):
                                        string += f'{str((i[j])): <{width}}'
                                        j+=1
                                    print(string)
                                print('\n')
                            else:
                                print("Command not recognized: " + command)
                        else:
                            print("Command not recognized: " + command)
                    else:
                        print("Command not recognized: " + command)
                else:
                    print("Command not recognized: " + command)
            else:
                print("Command not recognized: " + command)
        except:
            print("Command not recognized: " + command)
# Make sure nothing runs or prints out when this file is run as a module

if __name__=="__main__":
    interactive_prompt()
