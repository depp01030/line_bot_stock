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
    df = Fetcher(stock_id, [2019, 4, 18], [2021, 3, 17]).getHistorical()
    reply = stock_id + df["Date"][-1].astype(str) + "的收盤價是" + df["Close"][-1].astype(str)
    return reply

    
#====================================================================

# 載入需要的模組

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,StickerSendMessage
)

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

df_temp.loc[len(df_temp)-1,"Close"]
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    
    msg = event.message.text
    
    if msg == "來個貼圖":
        sticker_message = StickerSendMessage(
        package_id='1',
        sticker_id='2'
        )
        
        line_bot_api.reply_message(
        event.reply_token,
        sticker_message)
        
        return
    if msg == "2330":
        #stock_id = stock_id + ".TW"
        df = Fetcher("2330.TW", [2019, 4, 18], [2021, 3, 17]).getHistorical()
        #reply = stock_id + df["Date"][-1].astype(str) + "的收盤價是" + df["Close"][-1].astype(str)
        r = df.loc[len(df)-1,"Close"]
        
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=r))
        
        return
    r = '我不想回答耶'
    if msg in ["你好","hi","Hi","妳好"]:
        r = "我很好啊"
    elif msg == "你能幹嘛":
        r = "我現在很笨，什麼都不會"
        
        
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=r))

if __name__ == "__main__":
    app.run()