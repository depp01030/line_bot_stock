# -*- coding: utf-8 -*-
"""
Created on Wed Mar 17 18:15:11 2021

@author: depp
"""


# 必須先安裝yfinance套件
import time
import yfinance as yf
import h5py
import pandas as pd
from yahoo_historical import Fetcher

#data_2330 = Fetcher('2330.TW', [2019, 4, 18], [2021, 3, 17])
# df_2330 = data_2330.getHistorical()
# df_2330.head(10)
# 讀取csv檔
stock_list = pd.read_csv('stock_id.csv',encoding='gbk')
stock_list.columns = ['STOCK_ID', 'NAME']
list1= ["df_2330","df_2308"]
historical_data = pd.DataFrame()

for i in range(len(stock_list)):    

    # 抓取股票資料
    stock_id = stock_list.loc[i,"STOCK_ID"].astype(str) + ".TW"
    temp = Fetcher(stock_id, [2019, 4, 18], [2021, 3, 17])
    df = temp.getHistorical()

    #修正格式 ["dates","open","high","low","close","delta","volume"]
    df.iloc[:,5] =df.iloc[:,4].rolling(2).apply(lambda x: x.iloc[1] - x.iloc[0])
    # 增加股票代號
    #df['STOCK_ID'] = stock_list.loc[i, 'STOCK_ID']
    exec(f"{list1[i]} = df")
    # 合併
    #historical_data = pd.concat([historical_data, df])
    time.sleep(0.8)

    #exec(f"{list1[i]} = i")

