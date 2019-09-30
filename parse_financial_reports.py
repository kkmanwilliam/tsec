import requests
import pandas as pd
import numpy as np
import math
import os
from tenacity import retry, stop_after_attempt, wait_fixed
from datetime import datetime, timedelta

storage = "//Users/adrian/Python/tsec/tsec/financial_statement/"

# check all data form (sii, otc, pub, rotc)
def operation_his(row):
    ''' Save row to csv file '''
    f = open(storage+'duration_coverage_FS.csv', 'a')
    cw = csv.writer(f, lineterminator='\n')
    cw.writerow(row)
    f.close()

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def financial_statement(year, season, record_str, type='PL'):

    if year >= 1000:
        year -= 1911

    if type == 'PL': # 綜合損益彙總表
        url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb04'
    elif type == 'BS': # 資產負債彙總表
        url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb05'
    else:
        print('type does not match')
    
    df_final = pd.DataFrame()
    
    for corp_type in ["sii", "otc", "pub", "rotc"]:

        r = requests.post(url, {
            'encodeURIComponent':1,
            'step':1,
            'firstin':1,
            'off':1,
            'TYPEK':corp_type, # sii上市，otc上櫃，rotc興櫃，pub公開發行
            'year':str(year),
            'season':str(season),
        })
        r.encoding = 'utf8'

        try:
            dfs = pd.read_html(r.text, header=None)
            df = pd.concat(dfs[1:], axis=0, sort=False)
            df['年份'] = pd.Series([year] * df.shape[0])
            df['季度'] = pd.Series([season] * df.shape[0])
            df = df.set_index(['公司名稱']).apply(lambda s: pd.to_numeric(s, errors='ceorce'))
            df['公司名稱'] = df.index
            df['公司代號'] = df['公司代號'].astype(str)
            df = df.set_index('公司代號')
            df_final = pd.concat([df_final, df], axis=0, sort=False)
            operation_his([ record_str, datetime.now() ])
        except Exception as e:
            print(corp_type, " : ", e)
            
    return df_final

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def financial_analysis(year, season, record_str): # 營益分析彙總表
    
    if year >= 1000:
        year -= 1911
    
    url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb06'
    
    df_final = pd.DataFrame()
    
    for corp_type in ["sii", "otc", "pub", "rotc"]:
        
        r = requests.post(url, {
            'encodeURIComponent':1,
            'step':1,
            'firstin':1,
            'off':1,
            'TYPEK':corp_type, #otc pub rotc sii
            'year':str(year),
            'season':str(season),
        })
        r.encoding = 'utf8'

        try:
            dfs = pd.read_html(r.text, header=None)
            dfs[0].columns = dfs[0].iloc[0]
            df = dfs[0]
            df['年份'] = pd.Series([year] * df.shape[0])
            df['季度'] = pd.Series([season] * df.shape[0])
            df = df.set_index(['公司名稱']).apply(lambda s: pd.to_numeric(s, errors='ceorce'))
            df = df[~df['公司代號'].apply(lambda x: math.isnan(x))]
            df['公司名稱'] = df.index
            df['公司代號'] = df['公司代號'].astype(int).astype(str)
            df = df.set_index('公司代號')
            df_final = pd.concat([df_final, df], axis=0, sort=False)
            operation_his([ record_str, datetime.now() ])
        
        except Exception as e:
        	print(corp_type, " : ", e)

    return df_final

# Loading Files

if not os.path.exists(storage+'duration_coverage_FS.csv'):
    operation_his(["Season", "Created_at"])
duration_covered = pd.read_csv(storage+'duration_coverage_FS.csv')
existed_season = duration_covered['Season'].tolist()

df_PL = pd.read_csv(storage+'P&L.csv') if os.path.exists(storage+'P&L.csv') else pd.DataFrame()
df_BS = pd.read_csv(storage+'Balance_Sheet.csv') if os.path.exists(storage+'Balance_Sheet.csv') else pd.DataFrame()
df_FA = pd.read_csv(storage+'Financial_Analysis.csv') if os.path.exists(storage+'Financial_Analysis.csv') else pd.DataFrame()

# Main Part - Start from 2013-1
for year in list(range(2013, datetime.now().year+1)):
    for season in list(range(1, 5)):

        handling_season = "{0}-{1}".format(str(year), str(season))
        
        record_str = handling_season+" - 綜合損益彙總表"

        if record_str in existed_season:
            print("Pass: ", record_str)
        else:
            print("Handling: ", record_str)
            df_PL = pd.concat([df_PL, financial_statement(year, season, record_str, type='PL')], axis=0, sort=False)
    
        record_str = handling_season+" - 資產負債彙總表"

        if record_str in existed_season:
            print("Pass: ", record_str)
        else:
            print("Handling: ", record_str)
            df_BS = pd.concat([df_BS, financial_statement(year, season, record_str, type='BS')], axis=0, sort=False)
            
        
        record_str = handling_season+" - 營益分析彙總表"

        if record_str in existed_season:
            print("Pass: ", record_str)
        else:
            print("Handling: ", record_str)
            df_FA = pd.concat([df_FA, financial_analysis(year, season, record_str)], axis=0, sort=False)
                
df_PL.to_csv(storage+'P&L.csv', index=0)
df_BS.to_csv(storage+'Balance_Sheet.csv', index=0)
df_FA.to_csv(storage+'Financial_Analysis.csv', index=0) 

