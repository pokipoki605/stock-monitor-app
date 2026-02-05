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

GITHUB_REPO = "あなたのユーザー名/リポジトリ名" # ★必ず書き換えてください
FILE_PATH = "watchlist.json"
GH_PAT = get_config("GH_PAT")

# --- 日本株リスト取得 ---
@st.cache_data(ttl=86400)
def get_jp_stock_list():
    url = "https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls"
    try:
        df = pd.read_excel(url)
        df = df[['コード', '銘柄名']]
        df['display'] = df['コード'].astype(str) + ": " + df['銘柄名']
        return df
    except:
        return pd.DataFrame(columns=['display'])

# --- GitHub連携 ---
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
    _, sha = get_watchlist()
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GH_PAT}"}
    content_json = json.dumps(new_list, ensure_ascii=False, indent=4)
    content_base64 = base64.b64encode(content_json.encode('utf-8')).decode('utf-8')
    data = {"message": "Update via App", "content": content_base64, "sha": sha}
    return requests.put(url, headers=headers, json=data).status_code == 200

# --- 株価・配当・最安値チェック (キャッシュ・フォールバック付) ---
def fetch_stock_data(ticker, cached_info):
    try:
        stock = yf.Ticker(ticker)
        # 5年分のデータを一気に取得（期間別最安値のため）
        hist = stock.history(period="5y")
        if hist.empty: raise ValueError("No data")

        current_price = hist['Close'].iloc[-1]
        
        # 期間別最安値の計算
        low_ytd = hist[hist.index >= f"{datetime.now().year}-01-01"]['Low'].min()
        low_3y = hist.tail(252*3)['Low'].min() # 約3年
        low_5y = hist['Low'].min()

        # 配当・セクター (失敗してもキャッシュを使う)
        try:
            info = stock.info
            sector = info.get('sector', cached_info.get('sector', '不明'))
            div_rate = info.get('dividendRate', cached_info.get('annual_div', 0))
        except:
            sector = cached_info.get('sector', '不明')
            div_rate = cached_info.get('annual_div', 0)

        return {
            "price": current_price, "low_ytd": low_ytd, "low_3y": low_3y, "low_5y": low_5y,
            "sector": sector, "annual_div": div_rate, "history": hist['Close'], "is_live": True
        }
    except:
        # 失敗時はJSONに保存されている「前回の値」を返す
        return {
            "price": cached_info.get('last_price', 0),
            "low_ytd": cached_info.get('low_ytd', 0),
            "low_3y": cached_info.get('low_3y', 0),
            "low_5y": cached_info.get('low_5y', 0),
            "sector": cached_info.get('sector', '不明'),
            "annual_div": cached_info.get('annual_div', 0),
            "history": None, "is_live": False
        }

def calculate_new_average(old_qty, old_avg, add_qty, add_price):
    total_qty = old_qty + add_qty
    if total_qty == 0: return 0
    return ((old_qty * old_avg) + (add_qty * add_price)) / total_qty

def send_line(message):
    token = get_config("LINE_ACCESS_TOKEN")
    user_id = get_config("LINE_USER_ID")
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    data = {"to": user_id, "messages": [{"type": "text", "text": message}]}
    requests.post(url, headers=headers, json=data)
