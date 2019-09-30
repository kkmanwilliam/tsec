import pandas as pd
import requests
import os
from io import StringIO
import time
import csv
from datetime import datetime, timedelta

def operation_his(row):
    ''' Save row to csv file '''
    f = open(storage+'duration_coverage_sii_rev.csv', 'a')
    cw = csv.writer(f, lineterminator='\n')
    cw.writerow(row)
    f.close()

def monthly_report(year, month):
    
    # 假如是西元，轉成民國
    if year > 1990:
        year -= 1911
    
    url = 'https://mops.twse.com.tw/nas/t21/sii/t21sc03_'+str(year)+'_'+str(month)+'_0.html'
    if year <= 98:
        url = 'https://mops.twse.com.tw/nas/t21/sii/t21sc03_'+str(year)+'_'+str(month)+'.html'
    
    # 偽瀏覽器
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    
    # 下載該年月的網站，並用pandas轉換成 dataframe
    r = requests.get(url, headers=headers)
    r.encoding = 'big5'

    dfs = pd.read_html(StringIO(r.text), encoding='big-5')

    df = pd.concat([df for df in dfs if df.shape[1] <= 11 and df.shape[1] > 5])
    
    if 'levels' in dir(df.columns):
        df.columns = df.columns.get_level_values(1)
    else:
        df = df[list(range(0,10))]
        column_index = df.index[(df[0] == '公司代號')][0]
        df.columns = df.iloc[column_index]
    
    df['當月營收'] = pd.to_numeric(df['當月營收'], 'coerce')
    df = df[~df['當月營收'].isnull()]
    df = df[df['公司代號'] != '合計']
    df['年份'] = pd.Series([year] * df.shape[0])
    df['季度'] = pd.Series([month] * df.shape[0])
    
    # 偽停頓
    time.sleep(5)

    return df

storage = "//Users/adrian/Python/tsec/tsec/financial_statement/"

if not os.path.exists(storage+'duration_coverage_sii_rev.csv'):
    operation_his(["Month", "Created_at"])
duration_covered = pd.read_csv(storage+'duration_coverage_sii_rev.csv')
existed_month = duration_covered['Month'].tolist()

df = pd.read_csv(storage+'sii_revenue.csv') if os.path.exists(storage+'sii_revenue.csv') else pd.DataFrame()

for year in list(range(2001, datetime.now().year+1)):
    for month in list(range(1,13)):
        handling_month = "{0}-{1}".format(str(year), str(month))
        if handling_month in existed_month:
            print("Pass: ", handling_month)
        else:
            print("Handling: ", handling_month)
            try:
                df = pd.concat([df, monthly_report(year,month)], axis=0, sort=True)
                operation_his([handling_month, datetime.now()])
            except Exception as e:
                print("Failed: ", handling_month)
            
df.to_csv(storage+'sii_revenue.csv', index=0)