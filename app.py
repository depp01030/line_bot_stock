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
stock_id = "2330.TW"
def stock_close(stock_id):
    stock_id = stock_id + ".TW"
    df = Fetcher(stock_id, [2019, 4, 18], [2021, 3, 19]).getHistorical()
    r = "2330   " + df.loc[len(df)-1,"Date"] +\
        "  的收盤價是  " +df.loc[len(df)-1,"Close"].astype(str)
    return r

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
    MessageEvent, TextMessage, TextSendMessage,StickerSendMessage,ImageSendMessage
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
        
    #照片傳送
    if msg == "照片測試":
        message = ImageSendMessage(
            original_content_url='https://i.imgur.com/My240Nc.jpeg',
            preview_image_url='https://example.com/preview.jpg'
        )
        line_bot_api.reply_message(event.reply_token, message)
    
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=r))

if __name__ == "__main__":
    app.run()