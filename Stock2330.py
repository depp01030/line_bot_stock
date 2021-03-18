# -*- coding: utf-8 -*-
"""
Created on Sat Mar 13 16:53:25 2021

@author: depp
"""

import copy 
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt
import mpl_finance as mpf
from matplotlib.gridspec import GridSpec

import time
import h5py
from yahoo_historical import Fetcher
%matplotlib inline
'''原文網址：https://kknews.cc/code/zpr8y2l.html'''
# data = pd.read_csv('2330_stock.csv', encoding='big5')
# data = data[::-1]
# data.index = pd.RangeIndex(len(data.index))
# data.iloc[:,8] = data.iloc[:,8].str.replace(',', '').astype(float)
#stock_df = copy.deepcopy(data.iloc[:,[0,1,2,3,4,5,8]])
'舊的輸入方式'

'先建立一個database'
stock_list = pd.read_csv('stock_list.csv',encoding = "big5")
stock_list.columns = ['STOCK_ID', 'NAME']
stock_df_lst = "df_" + stock_list.loc[:,"STOCK_ID"].astype(str) 

for i in range(1):    

    # 抓取股票資料
    stock_id = stock_list.loc[i,"STOCK_ID"].astype(str) + ".TW"
    temp = Fetcher(stock_id, [2019, 4, 18], [2021, 3, 17])
    df = temp.getHistorical()
    #修正格式 ["dates","open","high","low","close","delta","volume"]
    df.iloc[:,5] =df.iloc[:,4].rolling(2).apply(lambda x: x.iloc[1] - x.iloc[0])
    # 增加股票代號
    exec(f"{stock_df_lst[i]} = df")
    # 合併
    #historical_data = pd.concat([historical_data, df])
    time.sleep(0.8)
stock_df = copy.deepcopy(df_2330)
stock_df.columns = ["dates","open","high","low","close","delta","volume"]


'==========================增加欄位===================================='
#製作均線
stock_df["5MA"] = stock_df["close"].rolling(5).mean()
stock_df["10MA"] = stock_df["close"].rolling(10).mean()
stock_df["20MA"] = stock_df["close"].rolling(20).mean()
stock_df["60MA"] = stock_df["close"].rolling(60).mean()
    

#RSV
rsv =(stock_df['close']-stock_df['low'].rolling(window=9).min())/\
    (stock_df['high'].rolling(window=9).max()-\
    stock_df['low'].rolling(window=9).min())*100
stock_df["rsv"] = pd.DataFrame(rsv).fillna(0)
#製作KD線
def KD_line(init_k,init_d,df):
    k = pd.DataFrame(np.repeat(init_k,8))
    for i in range(8,len(df)):
        k.loc[i,0] = k.loc[i-1,0] *2/3 +df["rsv"][i] * 1/3
    
    d = pd.DataFrame(np.repeat(init_d,8))
    for i in range(8,len(df)):
        d.loc[i,0] = d.loc[i-1,0] *2/3 + k.loc[i,0] * 1/3
    return k,d
k , d = KD_line(57.1,39.9,stock_df)
stock_df["k"] = pd.DataFrame(k)
stock_df["d"] = pd.DataFrame(d)

#布林通道 (標準差的計算有問題)
def bl_tunnel(df,delta=20):
    bl = pd.DataFrame()
    bl["bl_MA"] = df["close"].rolling(delta).mean()
    bl["bl_ul"] = bl["bl_MA"] + df["close"].rolling(delta).std(ddof = 1)*2
    bl["bl_ll"] = bl["bl_MA"] - df["close"].rolling(delta).std(ddof = 1)*2
    return bl
bl = bl_tunnel(stock_df)
stock_df = pd.concat([stock_df,bl],axis = 1)
#決定使用多少資料
#stock_df = stock_df.iloc[0:80]
# stock_df.index = pd.RangeIndex(len(stock_df.index))
'==========================買賣策略標籤===================================='
#策略標籤
def strategy_10MA(df):
    flag = 0 #持有0張
    label_lst = [2]
    for i in range(len(df)):
        if (df["10MA"][i] <= df["close"][i] )& (flag ==0):
            label_lst.append(int(1))    
            flag = 1
        elif( df["10MA"][i] > df["close"][i]) & (flag ==1):
            label_lst.append(int(0))
            flag = 0
        else:
            label_lst.append(int(2))
    label_lst.pop()
    label_lst[-1] = 0
    return label_lst

#布林通道
def strategy_bl(df):
    flag = 0 #持有0張
    pos = 0 #判斷股價是否大於20MA
    label_lst = [2,2]
    comp_range =df["bl_ul"].rolling(20).mean() -df["bl_ll"].rolling(20).mean()
    comp_range = comp_range.fillna(100)
    if df["close"][0] >=df["bl_MA"][0]:
        pos = 1
    for i in range(1,len(df)):        
        if df["close"][i] >=df["bl_MA"][i] and pos == 0:
            if flag == 0:
                pos = 1
                if (df["bl_ul"][i] -df["bl_ll"][i]) < comp_range[i-1]:
                    label_lst.append(2)
                else:
                    label_lst.append(1)
                    flag = 1
            elif flag ==1:
                pos = 1
                label_lst.append(2)
        elif df["close"][i] <df["bl_MA"][i] and pos == 1:
            if flag == 1:
                pos = 0
                if (df["bl_ul"][i] -df["bl_ll"][i]) < comp_range[i-1]:
                    label_lst.append(2)
                else:
                    label_lst.append(0)
                    flag = 0
            elif flag ==0:
                pos = 0
                label_lst.append(2)
        else:
            label_lst.append(2)

    label_lst.pop()
    if label_lst.count(1) > label_lst.count(0):
        label_lst[-1] = 0
    return label_lst

#KD策略
def strategy_KD(df,ul=80,ll=20):
    flag = 0 #持有0張
    label_lst = [2]#第一天空手
    for i in range(len(df)):
        #if df["k"][i] >=df["d"][i] and df["k"][i] >=ll and flag ==0:
        if df["k"][i] >=df["d"][i] and flag ==0:
            label_lst.append(int(1))
            flag = 1
        elif df["k"][i] <=df["d"][i] and flag ==1:
            label_lst.append(int(0))
            flag = 0
        else:
            label_lst.append(int(2))
    label_lst.pop()
    label_lst[-1] = 0
    return label_lst

# sig_lst =strategy_KD(stock_df,70,30)
sig_lst = strategy_10MA(stock_df)
# sig_lst = strategy_bl(stock_df)
#計算積效
def strategy_apply(df,sig):
    price_lst = []
    bs_temp =[] #buy and sell price
    flag =0
    for i in range(len(df)):
        if (sig[i] == 1 )&(flag == 0):
            bs_temp.append(df["close"][i])
            flag = 1
        elif (sig[i]==0)&(flag ==1):
            bs_temp.append(df["close"][i])
            flag = 0
            price_lst.append(bs_temp)
            bs_temp = []
    profit = 0
    for trade in price_lst:
        profit += (trade[1] - trade[0])
    return price_lst,profit,len(price_lst)

    
print(strategy_apply(stock_df, sig_lst))


'================================畫圖================================'
#製作標記
def volume_color(df):
    col_lst =list(range(len(df)))
    for i in range(len(df)):
        if df["delta"][i] <0:
            col_lst[i] = "green"
        else:
            col_lst[i] = "red"
    return col_lst

vol_col = volume_color(stock_df)
        
df = copy.deepcopy(stock_df)
def trade_mark_f(sigs,df):
    #賣出標記
    sell_mark_y = []
    sell_mark_x = []
    shift = (df["close"].max()-df["close"].min())/10
    for i in range(len(sigs)):
        if sigs[i] == 0:
            sell_mark_y.append(df["close"][i]-shift)
            sell_mark_x.append(i)
    
    #買入標記
    buy_mark_y = []
    buy_mark_x = []
    for i in range(len(sigs)):
        if sigs[i] == 1:
            buy_mark_y.append(df["close"][i]+shift)
            buy_mark_x.append(i)
    result = pd.DataFrame({'sell_x':sell_mark_x,
                            'sell_y':sell_mark_y,
                            'buy_x':buy_mark_x,
                            'buy_y':buy_mark_y})
    
    return result
trade_mark = trade_mark_f(sig_lst,stock_df)



fig = plt.figure(figsize=(30, 10))
'''add_subplot(上下切幾塊，左右切幾塊，左上到右下第幾塊)'''
'''add_axes( x初始座標, y初始座標, 寬, 高 )'''
#ax = fig.add_subplot(1, 1, 1)
ax = fig.add_axes([0,0.6,1,0.6])
ax2 = fig.add_axes([0,0.2,1,0.4])
ax3 = fig.add_axes([0,0,1,0.2])

#主圖
ax.set_xticks(range(0, len(stock_df['dates']), 20))
ax.set_xticklabels(stock_df['dates'].str[5:][::20])
#移動平均
ax.plot(stock_df['5MA'], label='5 MA')
ax.plot(stock_df['10MA'], label='10 MA')
ax.plot(stock_df['20MA'], label='20 MA')
ax.plot(stock_df['60MA'], label='60 MA')
#布林通道
ax.plot(stock_df["bl_MA"],color="blue",linewidth = 1)
ax.plot(stock_df["bl_ul"],color="blue", linestyle=':',linewidth = 3)
ax.plot(stock_df["bl_ll"],color="blue", linestyle=':',linewidth = 3)


ax.legend(loc='upper left')
mpf.candlestick2_ochl(ax, stock_df['open'], stock_df['close'], stock_df['high'], stock_df['low'],
                      width=0.5, colorup='r', colordown='green',
                      alpha=0.6)
ax.scatter(trade_mark["sell_x"],
            trade_mark["sell_y"],color = "green",
            marker = "^",s =100)
ax.scatter(trade_mark["buy_x"],
            trade_mark["buy_y"],color = "red",
            marker = "v",s =100)
#KD線圖
ax2.plot(stock_df['k'], label='K')
ax2.plot(stock_df['d'], label='D')
ax2.set_xticks(range(0, len(stock_df['dates']), 20))
ax2.set_xticklabels(stock_df['dates'].str[5:][::20])
ax2.legend(loc='upper left')
ax2.axhline(y=20, color='k', linestyle='--')
ax2.axhline(y=80, color='k', linestyle='--')

# #價量圖
mpf.volume_overlay(ax3, stock_df['open'], stock_df['close'], stock_df['volume'], colorup='r', colordown='g', width=0.5, alpha=0.8)
ax3.set_xticks(range(0, len(stock_df['dates']), 20))
ax3.set_xticklabels(stock_df['dates'].str[5:][::20])