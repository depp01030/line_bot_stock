# -*- coding: utf-8 -*-
"""
Created on Thu Mar 18 14:47:51 2021

@author: depp
"""
'''
git add .
git commit -m "update"
git push
git push heroku


'''


#====================================================================
#%% 股票圖表相關
import copy 
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt
import mpl_finance as mpf
from matplotlib.gridspec import GridSpec

import time
import h5py
from yahoo_historical import Fetcher

def stock_close(stock_id):
    stock_id = stock_id + ".TW"
    df = Fetcher(stock_id, [2019, 4, 18], [2021, 3, 19]).getHistorical()
    r = "2330   " + df.loc[len(df)-1,"Date"] +\
        "  的收盤價是  " +df.loc[len(df)-1,"Close"].astype(str)
    return r

#布林通道 (標準差的計算有問題)
def bl_tunnel(df,delta=20):
    bl = pd.DataFrame()
    bl["bl_MA"] = df["close"].rolling(delta).mean()
    bl["bl_ul"] = bl["bl_MA"] + df["close"].rolling(delta).std(ddof = 1)*2
    bl["bl_ll"] = bl["bl_MA"] - df["close"].rolling(delta).std(ddof = 1)*2
    return bl
#KD線製作
def KD_line(df,init_k = 50,init_d = 50):
    k = pd.DataFrame(np.repeat(init_k,8))
    for i in range(8,len(df)):
        k.loc[i,0] = k.loc[i-1,0] *2/3 +df["rsv"][i] * 1/3
    
    d = pd.DataFrame(np.repeat(init_d,8))
    for i in range(8,len(df)):
        d.loc[i,0] = d.loc[i-1,0] *2/3 + k.loc[i,0] * 1/3
    return k,d
#macd製作
#DIV 6.24 5.16
def macd(df):
    macd_df = pd.DataFrame()
    macd_df["EMA_12"] = df['close'].ewm(span=12, adjust=False).mean()
    macd_df['EMA_26'] = df['close'].ewm(span=26, adjust=False).mean()
    macd_df['DIF'] = macd_df['EMA_12'] - macd_df['EMA_26']
    macd_df['MACD'] = macd_df['DIF'].ewm(span=9, adjust=False).mean()
    macd_df['MACD_hist'] = macd_df['DIF'] - macd_df['MACD']
    return macd_df

# init_k_lst = np.repeat(50,len(stock_list)) #先建立所有股票的init_kd
# init_d_lst =np.repeat(50,len(stock_list))
i=0
begin_date = [2019, 4, 18]
end_date = [2021, 3, 20]

'========================股價資訊爬蟲 (價格 收盤 等等====================================='
def scrape_stock_price_f(stock_id,begin = begin_date ,end = end_date):
        # 抓取股票資料
        stock_id = stock_id + ".TW"
        df_temp = Fetcher(stock_id, begin, end).getHistorical()
        #修正格式 ["dates","open","high","low","close","delta","volume"]
        df_temp.iloc[:,5] =df_temp.iloc[:,4].rolling(2).apply(lambda x: x.iloc[1] - x.iloc[0])
        df_temp.columns = ["dates","open","high","low","close","delta","volume"]
        '==========================增加欄位===================================='
        #製作均線
        df_temp["5MA"] = df_temp["close"].rolling(5).mean()
        df_temp["10MA"] = df_temp["close"].rolling(10).mean()
        df_temp["20MA"] = df_temp["close"].rolling(20).mean()
        df_temp["60MA"] = df_temp["close"].rolling(60).mean()
        #RSV
        rsv =(df_temp['close']-df_temp['low'].rolling(window=9).min())/\
            (df_temp['high'].rolling(window=9).max()-\
            df_temp['low'].rolling(window=9).min())*100
        df_temp["rsv"] = pd.DataFrame(rsv).fillna(0)
        
        #製作KD線
        df_temp["k"] , df_temp["d"] = KD_line(df_temp)
        #MACD
        df_temp = pd.concat([df_temp,macd(df_temp)],axis = 1)
        #布林通道 (標準差的計算有問題)
        df_temp = pd.concat([df_temp,bl_tunnel(df_temp)],axis = 1)
        # 增加股票代號
        return df_temp

#%% 
'=================================經營績效==============================================='
def scrape_busi_perf_f(stock_id):
    browser = webdriver.Chrome()
    perf_indexes = ["獲利指標", "季增統計", "年增統計", "PER/PBR"]
    busi_performance = pd.DataFrame()
    try:
        for h in range(len(perf_indexes)):
            browser.get("https://goodinfo.tw/StockInfo/StockBzPerformance.asp?STOCK_ID="+ stock_id +"&YEAR_PERIOD=9999&RPT_CAT=M_QUAR")
            select_index= Select(browser.find_element_by_xpath("/html/body/table[2]/tbody/tr/td[3]/table[3]/tbody/tr/td/table/tbody/tr/td[1]/nobr[1]/select"))#日期選單定位
            select_index = select_index.select_by_value(perf_indexes[h])#選單項目定位
            time.sleep(2)
            soup = BeautifulSoup(browser.page_source, 'html.parser')
            data = soup.select_one('#divDetail')
            temp_df = pd.read_html(data.prettify()) #輸出網頁表格 (亂
    
            #整理出正確column 名稱
            temp_df_col = temp_df[0].columns
            temp_colname = []
            for i in range(len(temp_df_col)):
                df_text = pd.DataFrame(temp_df_col[i]).drop_duplicates(keep='first')
                texts =""
                for j in range(len(df_text)):
                    if h == 3:
                        texts = texts + "年" +df_text[0][j].replace(" ","")
                    else:
                        texts = texts + df_text[0][j].replace(" ","")
                temp_colname.append(texts)
            #加上正確column 名稱
            temp_df[0].columns = temp_colname
            #合併四頁資訊
            busi_performance = pd.concat([busi_performance,temp_df[0]],axis=1)
        browser.close() #關掉網頁
        return busi_performance
    except:
        return busi_performance

#%%
'==========================買賣策略標籤===================================='
class Stock_f:
    def __init__(self,df,name):
        self.df = df
        self.sig_lst = pd.DataFrame()
        self.vol_col = pd.DataFrame()
        self.trade_mark = pd.DataFrame()
        self.name = name
    #增加策略標籤
    def strategy_10MA(self):
        df = self.df
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
        if label_lst.count(1) > label_lst.count(0):
            label_lst[-1] = 0
        self.sig_lst =  label_lst
        self.strategy_apply()
    #布林通道
    
    def strategy_bl(self):
        df = self.df
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
            if label_lst[-1]== 1:
                label_lst[-1] = 2
            else:
                label_lst[-1] = 0
        self.sig_lst =  label_lst
        self.strategy_apply()
    
    #KD策略
    def strategy_KD(self,ul=80,ll=20):
        df = self.df
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
        if label_lst.count(1) > label_lst.count(0):
            if label_lst[-1]== 1:
                label_lst[-1] = 2
            else:
                label_lst[-1] = 0
        self.sig_lst =  label_lst
        self.strategy_apply()
    #MACD 策略
    def strategy_MACD_line(self):
        df = self.df
        flag = 0 #持有0張
        label_lst = [2]#第一天空手
        for i in range(len(df)):
            if df["DIF"][i] >=df["MACD"][i] and flag ==0:
                label_lst.append(int(1))
                flag = 1
            elif df["DIF"][i] <=df["MACD"][i] and flag ==1:
                label_lst.append(int(0))
                flag = 0
            else:
                label_lst.append(int(2))
        label_lst.pop()
        if label_lst.count(1) > label_lst.count(0):
            if label_lst[-1]== 1:
                label_lst[-1] = 2
            else:
                label_lst[-1] = 0
        self.sig_lst =  label_lst
        self.strategy_apply()
    
    def strategy_MACD_hist(self):
        df = self.df
        flag = 0 #持有0張
        label_lst = [2,2]#第一天空手 第二天也空手(沒有i-1)
        for i in range(1,len(df)):
            if df["MACD_hist"][i-1] < 0 and df["MACD_hist"][i] >0 and flag ==0:
                label_lst.append(int(1))
                flag = 1
            elif (df["MACD_hist"][i] - df["MACD_hist"][i-1]) < 0 and flag ==1:
                label_lst.append(int(0))
                flag = 0
            else:
                label_lst.append(int(2))
        label_lst.pop()
        if label_lst.count(1) > label_lst.count(0):
            if label_lst[-1]== 1:
                label_lst[-1] = 2
            else:
                label_lst[-1] = 0
        self.sig_lst =  label_lst
        self.strategy_apply()
        #執行策略
    def strategy_apply(self):
        df = self.df
        sigs = self.sig_lst
        price_lst = []
        bs_temp =[] #buy and sell price
        buy_total = []
        flag =0
        for i in range(len(df)):
            if (sigs[i] == 1 )&(flag == 0):
                bs_temp.append(df["close"][i])
                buy_total.append(df["close"][i])
                flag = 1
            elif (sigs[i]==0)&(flag ==1):
                bs_temp.append(df["close"][i])
                flag = 0
                price_lst.append(bs_temp)
                bs_temp = []
        profit = 0
        for trade in price_lst:
            profit += (trade[1] - trade[0])
        roi =round(profit/sum(buy_total) * 100,2)
        self.profit = profit
        self.price_lst = price_lst
        self.roi =roi
        print(price_lst,profit,len(price_lst),roi)
    '================================畫圖================================'
    #製作標記
    def plot_result(self,save_flag = 0,trade_line_flag = 0):
        name = self.name
        self.macd_color_f()
        macd_col = self.macd_col
        self.trade_mark_f()
        trade_mark = self.trade_mark
        df = self.df
        plt.rcParams['font.sans-serif'] = ['Taipei Sans TC Beta']
        fig = plt.figure(figsize=(25, 10))
        '''add_subplot(上下切幾塊，左右切幾塊，左上到右下第幾塊)'''
        '''add_axes( x初始座標, y初始座標, 寬, 高 )'''
        #ax = fig.add_subplot(1, 1, 1)
        ax_note = fig.add_axes([0,1.6,1,0.2])
        ax = fig.add_axes([0,1,1,0.6])
        ax2 = fig.add_axes([0,0.6,1,0.4])
        ax4 = fig.add_axes([0,0.2,1,0.4])
        ax3 = fig.add_axes([0,0,1,0.2])
        
        #主圖
        ax.set_xticks(range(0, len(df['dates']), 20))
        ax.set_xticklabels(df['dates'].str[5:][::20])
        ax_note.set_title(name ,fontsize = 40)
        #移動平均
        ax.plot(df['5MA'], label='5 MA')
        ax.plot(df['10MA'], label='10 MA')
        ax.plot(df['20MA'], label='20 MA')
        ax.plot(df['60MA'], label='60 MA')
        #布林通道
        ax.plot(df["bl_MA"],color="blue",linewidth = 1)
        ax.plot(df["bl_ul"],color="blue", linestyle=':',linewidth = 3)
        ax.plot(df["bl_ll"],color="blue", linestyle=':',linewidth = 3)
        
        
        ax.legend(loc='upper left')
        mpf.candlestick2_ochl(ax, df['open'], df['close'], df['high'], df['low'],
                              width=0.5, colorup='r', colordown='green',
                              alpha=0.6)
        shift = (df["close"].max()-df["close"].min())/20
        ax.scatter(trade_mark["sell_x"],
                    trade_mark["sell_y"]-shift,color = "green",
                    marker = "^",s =100)
        ax.scatter(trade_mark["buy_x"],
                    trade_mark["buy_y"]+shift,color = "red",
                    marker = "v",s =100)
        for i in range(len(trade_mark["buy_x"])):
            ax.text(trade_mark.loc[i,"buy_x"],trade_mark.loc[i,"buy_y"]+shift*1.5,
                    round(trade_mark.loc[i,"buy_y"],2), ha='center',fontsize = 15)
            ax.text(trade_mark.loc[i,"sell_x"],trade_mark.loc[i,"sell_y"]-shift*2.2,
                    round(trade_mark.loc[i,"sell_y"],2), ha='center',fontsize = 15)


        ax.grid(True)
        #KD線圖
        ax2.plot(df['k'], label='K')
        ax2.plot(df['d'], label='D')
        ax2.set_xticks(range(0, len(df['dates']), 20))
        ax2.set_xticklabels(df['dates'].str[5:][::20])
        ax2.legend(loc='upper left')
        ax2.axhline(y=20, color='k', linestyle='--')
        ax2.axhline(y=80, color='k', linestyle='--')
        ax2.grid(True)
        #MACD
        ax4.plot(df['DIF'], color='red', label="DIF", alpha=1)
        ax4.plot(df['MACD'], color='green', label="MACD", alpha=1)
        ax4.set_xticks(range(0, len(df['dates']), 20))
        ax4.set_xticklabels(df['dates'].str[5:][::20])
        ax4.legend(loc="upper left")
        ax4.bar(df['dates'], df["MACD_hist"],color = macd_col)
        ax4.grid(True)
        # #價量圖
        mpf.volume_overlay(ax3, df['open'], df['close'], df['volume'],
                            colorup='r', colordown='g', width=0.5, alpha=0.8)
        ax3.set_xticks(range(0, len(df['dates']), 20))
        ax3.set_xticklabels(df['dates'].str[5:][::20])
        ax3.grid(True)
        
        #畫買賣線
        if trade_line_flag == 1:
            for ax_plot in [ax,ax2,ax3,ax4]:
                for i in range(len(trade_mark["buy_x"])):
                    ax_plot.axvline(x=trade_mark.loc[i,"buy_x"],color = "red")
                    ax_plot.axvline(x=trade_mark.loc[i,"sell_x"],color = "green")

        '================備註欄內文字===================='
        if len(trade_mark) > 0:
            note = "股票名稱 : " + name +\
                "\n買賣次數 : " + str(len(self.price_lst)) +\
                "\n總收益 : " + str(round(self.profit,2)) + "        投資報酬率 : " + str(self.roi)
            '================備註欄內文字===================='
            ax_note.text(0.01,0.8,
                        note, ha='left',va = "top",fontsize = 20)
        if save_flag == 1:
            fig.savefig("stock_chart.jpg", dpi=200, bbox_inches='tight')

    '-------------價量圖顏色------------'
    def macd_color_f(self):
        df = self.df
        col_lst =list(range(len(df)))
        for i in range(len(df)):
            if df["MACD_hist"][i] <0:
                col_lst[i] = "green"
            else:
                col_lst[i] = "red"
        self.macd_col = col_lst

    '-------------買賣點標記-------------'
    def trade_mark_f(self):
        df = self.df
        sigs = self.sig_lst
        #賣出標記
        sell_mark_y = []
        sell_mark_x = []
        #shift = (df["close"].max()-df["close"].min())/10
        for i in range(len(sigs)):
            if sigs[i] == 0:
                sell_mark_y.append(df["close"][i])
                sell_mark_x.append(i)
        #買入標記
        buy_mark_y = []
        buy_mark_x = []
        for i in range(len(sigs)):
            if sigs[i] == 1:
                buy_mark_y.append(df["close"][i])
                buy_mark_x.append(i)
        result = pd.DataFrame({'sell_x':sell_mark_x,
                                'sell_y':sell_mark_y,
                                'buy_x':buy_mark_x,
                                'buy_y':buy_mark_y})
        self.trade_mark = result

#====================================================================

#%% 載入需要的模組 line bot

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,StickerSendMessage,ImageSendMessage
)
import pyimgur

#%% line bot imgur 獲取圖片網址
CLIENT_ID = "2a681c0da3c830b"
def stock_plot(CLIENT_ID,stock_id):

    
    stock_df = scrape_stock_price_f(stock_id)
    perf_df = scrape_busi_perf_f(stock_id)

    stock_name = stock_id #+"_" + stock_list.loc[i,"NAME"]
    stock_df = Stock_f(stock_df,stock_name)
    stock_df.strategy_MACD_line()
    stock_df.plot_result(1,0)
    
    PATH = "stock_chart.jpg"
    im = pyimgur.Imgur(CLIENT_ID)
    uploaded_image = im.upload_image(PATH)
    return uploaded_image.link


#%% line bot 相關
app = Flask(__name__)
line_bot_api = LineBotApi('/oF4i+jfrlLhmSYiTcjR0h2S5+L17ZYPApY8SXRCQSVMsXAa3mwZhuRcpxWhGd9Zq6dzpPwNCqvrf08NJrVXvC38YpgLinL1HvZmz2Mw9L339WNDu5Xw3NQ3SIqqABSV1FEdCmWv1iId93sFHlmVtgdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('a845249d237879925cfdddf8bbb3c9b9')


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    
    msg = event.message.text
    r = '我不想理你耶'
    if msg == "來個貼圖":
        sticker_message = StickerSendMessage(
        package_id='1',
        sticker_id='3'
        )
        
        line_bot_api.reply_message(
        event.reply_token,
        sticker_message)
        
        return
    if msg == "2330":
        r = stock_close(msg)
        
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=r))
        
        return
    if msg in ["你好","hi","Hi","妳好"]:
        r = "我很好啊"
    elif msg == "你能幹嘛":
        r = "我現在很笨，什麼都不會"
        
    #照片傳送==================================================================
    
    if msg == "照片測試":
        stock_id = "2330"
        image_url = stock_plot(CLIENT_ID,stock_id)
        message = ImageSendMessage(
            original_content_url=image_url,
            preview_image_url= image_url
        )
        line_bot_api.reply_message(event.reply_token, message)
    
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=r))
    

if __name__ == "__main__":
    app.run()