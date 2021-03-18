# -*- coding: utf-8 -*-
"""
Created on Thu Mar 18 14:47:51 2021

@author: depp
"""

# 載入需要的模組

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
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
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))


if __name__ == "__main__":
    app.run()