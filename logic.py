import yfinance as yf
import requests
import os
import json
import base64
import streamlit as st
import pandas as pd
from datetime import datetime

# --- 設定取得 ---
def get_config(key):
    if key in os.environ: return os.environ[key]
    if key in st.secrets: return st.secrets[key]
    return None

# --- GitHub連携の設定 ---
GITHUB_REPO = "あなたのユーザー名/リポジトリ名" # ★ここを書き換えてください
FILE_PATH = "watchlist.json"
GH_PAT = get_config("GH_PAT")

# --- 日本株全銘柄のリストを取得 ---
@st.cache_data
def get_jp_stock_list(): # ← 名前を main.py と合わせました
    url = "https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls"
    try:
        df = pd.read_excel(url)
        df = df[['コード', '銘柄名']]
        df['display'] = df['コード'].astype(str) + ": " + df['銘柄名']
        return df
    except Exception as e:
        st.error(f"銘柄リストの取得に失敗しました: {e}")
        return pd.DataFrame(columns=['コード', '銘柄名', 'display'])

def get_watchlist():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GH_PAT}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        data = r.json()
        content = json.loads(base64.b64decode(data['content']).decode('utf-8'))
        return content, data['sha']
    return {}, None

def save_watchlist(new_list):
    current_data, sha = get_watchlist()
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GH_PAT}"}
    content_json = json.dumps(new_list, ensure_ascii=False, indent=4)
    content_base64 = base64.b64encode(content_json.encode('utf-8')).decode('utf-8')
    data = {"message": "Update watchlist via Streamlit", "content": content_base64, "sha": sha}
    r = requests.put(url, headers=headers, json=data)
    return r.status_code == 200

def send_line(message):
    token = get_config("LINE_ACCESS_TOKEN")
    user_id = get_config("LINE_USER_ID")
    if not token or not user_id: return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    data = {"to": user_id, "messages": [{"type": "text", "text": message}]}
    requests.post(url, headers=headers, json=data)

def check_stock(ticker, period="ytd"):
    stock = yf.Ticker(ticker)
    df = stock.history(period="1y")
    if df.empty: return None, None, False
    current = df['Close'].iloc[-1]
    if period == "ytd":
        low = df[df.index >= f"{datetime.now().year}-01-01"]['Low'].min()
    else:
        low = df['Low'].min()
    return current, low, (current <= low)
