# -*- coding: utf-8 -*-

import os
import sys
import csv
import time
import logging
import requests
import argparse
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from re import sub
from os import mkdir
from os.path import isdir
from pandas.io import sql
from querybase import *

class Crawler():
    def __init__(self, prefix='data'):
        ''' Make directory if not exist when initialize '''
        if not isdir(prefix):
            mkdir(prefix)
        self.prefix = prefix
        
        if not os.path.exists('duration_coverage.csv'):
            self._operation_his(['Date','Created_at'])
        self.duration_covered = pd.read_csv('duration_coverage.csv') 
    
    def _clean_row(self, row):
        ''' Clean comma and spaces '''
        for index, content in enumerate(row):
            row[index] = sub(",", "", content.strip())
        return row

    def _record(self, df):
        print("writing db start")
        conn = sqlite3.connect('stock_analytics.db')
        conn.execute(query_build_price_table)
        sql.to_sql(df, name='STOCK_PRICE', con=conn, if_exists='append')
        conn.commit()
        conn.close()
        print("writing db end")

    def _operation_his(self, row):
        f = open('duration_coverage.csv', 'a')
        cw = csv.writer(f, lineterminator='\n')
        cw.writerow(row)
        f.close()

    def _get_tse_data(self, date_tuple):
        date_str = '{0}{1:02d}{2:02d}'.format(date_tuple[0], date_tuple[1], date_tuple[2])

        url = 'http://www.twse.com.tw/exchangeReport/MI_INDEX'
        query_params = { 'date': date_str, 'response': 'json', 'type': 'ALL', '_': str(round(time.time() * 1000) - 500)}

        # Get json data
        page = requests.get(url, params=query_params)

        if not page.ok:
            logging.error("Can not get TSE data at {}".format(date_str))
            return

        content = page.json()

        dict_raw = {'stock_id':[], 'date':[], 'volume':[], 'turnover_value':[], 'open':[], 'high':[], 'low':[], 'close':[], 'spread':[], 'transactions':[], 'PE_ratio':[]}
        
        for data in content['data9']:
            data = self._clean_row(data)
            sign = '-' if data[9].find('green') > 0 else ''
            dict_raw['stock_id'].append(str(data[0])),
            dict_raw['date'].append(datetime(date_tuple[0], date_tuple[1], date_tuple[2])),
            dict_raw['volume'].append(data[2]), 
            dict_raw['turnover_value'].append(data[4]), 
            dict_raw['open'].append(data[5]), 
            dict_raw['high'].append(data[6]), 
            dict_raw['low'].append(data[7]), 
            dict_raw['close'].append(data[8]),
            dict_raw['spread'].append( sign + data[10]),
            dict_raw['transactions'].append(data[3]),
            dict_raw['PE_ratio'].append(data[15])
        
        df = pd.DataFrame(dict_raw)
        df['date'] = pd.to_datetime(df['date'])
        df.replace(['--','---','X','----'], np.nan, inplace=True)
        df.replace(['除息','除權息', 'X0.00'], 0, inplace=True)
        df[['open', 'high', 'low', 'close', 'spread']] = df[['open', 'high', 'low', 'close', 'spread']].apply(pd.to_numeric)
        df['change_ratio'] = (df['close'] / (df['close'] - df['spread']) -1 )*100
        df = df.round({'change_ratio':2}) 
        df.set_index('date',inplace=True)
        self._record(df)

    def _get_otc_data(self, date_tuple):
        date_str = '{0}/{1:02d}/{2:02d}'.format(date_tuple[0] - 1911, date_tuple[1], date_tuple[2])
        ttime = str(int(time.time()*100))
        url = 'http://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php?l=zh-tw&d={}&_={}'.format(date_str, ttime)
        page = requests.get(url)

        if not page.ok:
            logging.error("Can not get OTC data at {}".format(date_str))
            return

        result = page.json()

        if result['reportDate'] != date_str:
            logging.error("Get error date OTC data at {}".format(date_str))
            return

        dict_raw = {'stock_id':[], 'date':[], 'volume':[], 'turnover_value':[], 'open':[], 'high':[], 'low':[], 'close':[], 'spread':[], 'transactions':[], 'PE_ratio':[]}

        for table in [result['mmData'], result['aaData']]:
            for tr in table:
                data = self._clean_row(tr)
                dict_raw['stock_id'].append(str(data[0])),
                dict_raw['date'].append(datetime(date_tuple[0], date_tuple[1], date_tuple[2])),
                dict_raw['volume'].append(data[8]), 
                dict_raw['turnover_value'].append(data[9]), 
                dict_raw['open'].append(data[4]), 
                dict_raw['high'].append(data[5]), 
                dict_raw['low'].append(data[6]), 
                dict_raw['close'].append(data[2]),
                dict_raw['spread'].append(data[3]),
                dict_raw['transactions'].append(data[10]),
                dict_raw['PE_ratio'].append(None)

        df = pd.DataFrame(dict_raw)
        df['date'] = pd.to_datetime(df['date'])
        df.replace(['--','---','X','----'], np.nan, inplace=True)
        df.replace(['除息','除權息', 'X0.00'], 0, inplace=True)
        df[['open', 'high', 'low', 'close', 'spread']] = df[['open', 'high', 'low', 'close', 'spread']].apply(pd.to_numeric)
        df['change_ratio'] = (df['close'] / (df['close'] - df['spread']) -1 )*100
        df = df.round({'change_ratio':2}) 
        df.set_index('date',inplace=True)
        self._record(df)

    def get_data(self, date_tuple):
        print('Crawling {}'.format(date_tuple))
        self._get_tse_data(date_tuple)
        self._get_otc_data(date_tuple)

def main():
    # Set logging
    if not os.path.isdir('log'):
        os.makedirs('log')
    logging.basicConfig(filename='log/crawl-error.log',
        level=logging.ERROR,
        format='%(asctime)s\t[%(levelname)s]\t%(message)s',
        datefmt='%Y/%m/%d %H:%M:%S')

    # Get arguments
    parser = argparse.ArgumentParser(description='Crawl data at assigned day')
    parser.add_argument('day', type=int, nargs='*',
        help='assigned day (format: YYYY MM DD), default is today')
    parser.add_argument('-b', '--back', action='store_true',
        help='crawl back from assigned day until 2004/2/11')
    parser.add_argument('-c', '--check', action='store_true',
        help='crawl back 10 days for check data')

    args = parser.parse_args()

    # Day only accept 0 or 3 arguments
    if len(args.day) == 0:
        first_day = datetime.today()
    elif len(args.day) == 3:
        first_day = datetime(args.day[0], args.day[1], args.day[2])
    else:
        parser.error('Date should be assigned with (YYYY MM DD) or none')
        return

    crawler = Crawler()

    # If back flag is on, crawl till 2004/2/11, else crawl one day
    #if args.back or args.check:
        # otc first day is 2007/04/20
        # tse first day is 2004/02/11
        # last_day = datetime(2004, 2, 11) if args.back else first_day - timedelta(10)
    last_day =  datetime(2019, 5, 1) #First day of the curent data format
    existed_day = crawler.duration_covered['Date'].tolist()
    execution_days = []
    handling_date = str(first_day.year-1911)+str(first_day.strftime("/%m/%d"))
    
    while first_day >= last_day and handling_date not in existed_day:
        execution_days += [first_day]
        first_day -= timedelta(1)
        handling_date = str(first_day.year-1911)+str(first_day.strftime("/%m/%d"))
    
    if execution_days == []:
        sys.exit(0)
    
    for first_day in execution_days[::-1]:
        try:
            crawler.get_data((first_day.year, first_day.month, first_day.day))
        except Exception as e:
            print("Failed: ", first_day)
            print(e)
            date_str = first_day.strftime('%Y/%m/%d')
            logging.error('Crawl raise error {}'.format(date_str))
            continue
        finally:
            handling_date = str(first_day.year-1911)+str(first_day.strftime("/%m/%d"))
            crawler._operation_his([ handling_date, datetime.now() ])

if __name__ == '__main__':
    main()