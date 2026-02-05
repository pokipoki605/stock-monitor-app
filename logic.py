import yfinance as yf
import requests
import os
import json
import base64
import streamlit as st

# --- 設定取得 ---
def get_config(key):
    if key in os.environ: return os.environ[key]
    return st.secrets[key]

# --- GitHub上のJSONファイルを読み書きする関数 ---
GITHUB_REPO = "toshiki-tsuji/stock-monitor"
FILE_PATH = "watchlist.json"
GITHUB_TOKEN = get_config("GITHUB_TOKEN")

def get_watchlist():
    """GitHubから現在のリストを取得"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = json.loads(base64.b64decode(r.json()['content']))
        return content, r.json()['sha'] # shaは更新に必要
    return {}, None

def save_watchlist(new_list):
    """GitHubのファイルを更新"""
    current_data, sha = get_watchlist()
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    content_base64 = base64.b64encode(json.dumps(new_list, ensure_ascii=False, indent=4).encode()).decode()
    data = {
        "message": "Update watchlist via Streamlit",
        "content": content_base64,
        "sha": sha
    }
    r = requests.put(url, headers=headers, json=data)
    return r.status_code == 200

# --- 通知・株価チェック ---
def send_line(message):
    token = get_config("LINE_ACCESS_TOKEN")
    user_id = get_config("LINE_USER_ID")
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    data = {"to": user_id, "messages": [{"type": "text", "text": message}]}
    requests.post(url, headers=headers, json=data)

def check_stock(ticker, period="ytd"):
    stock = yf.Ticker(ticker)
    df = stock.history(period="1y") # 判定用に長めに取る
    if df.empty: return None, None, False
    current = df['Close'].iloc[-1]
    # 指定期間の安値
    if period == "ytd":
        low = df[df.index >= f"{df.index[-1].year}-01-01"]['Low'].min()
    else:
        low = df['Low'].tail(250 if period=="1y" else 750).min() # 簡易計算
    return current, low, (current <= low)
