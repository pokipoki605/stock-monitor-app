import yfinance as yf
import requests
import os
import streamlit as st

# LINE設定（環境変数またはStreamlit Secretsから取得）
def get_config(key):
    if key in os.environ: return os.environ[key]
    return st.secrets[key]

def send_line(message):
    token = get_config("LINE_ACCESS_TOKEN")
    user_id = get_config("LINE_USER_ID")
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    data = {"to": user_id, "messages": [{"type": "text", "text": message}]}
    requests.post(url, headers=headers, json=data)

def check_stock_and_notify(ticker, period_choice):
    stock = yf.Ticker(ticker)
    df_now = stock.history(period="1d")
    if df_now.empty: return None, None
    
    current_price = df_now['Close'].iloc[-1]
    target_low = stock.history(period=period_choice)['Low'].min()
    
    is_alert = current_price <= target_low
    return current_price, target_low, is_alert
