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
GITHUB_REPO = "pokipoki605/stock-monitor-app" 
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
def check_stock_detail(ticker):
    """株価、配当利回り、チャート用データを取得"""
    stock = yf.Ticker(ticker)
    # チャート用（過去6ヶ月）
    df = stock.history(period="6mo")
    if df.empty: return None
    
    current_price = df['Close'].iloc[-1]
    
    # 配当利回りの取得 (yfinanceのinfoは遅い場合があるためtry-except)
    try:
        dividend_yield = stock.info.get('dividendYield', 0) 
        if dividend_yield is None: dividend_yield = 0
        dividend_yield *= 100 # 0.03 -> 3.0%
    except:
        dividend_yield = 0
        
    return {
        "price": current_price,
        "yield": dividend_yield,
        "history": df['Close']
    }

def calculate_new_average(old_qty, old_avg, add_qty, add_price):
    """買い増し時の平均取得単価を計算"""
    total_qty = old_qty + add_qty
    if total_qty == 0: return 0
    new_avg = ((old_qty * old_avg) + (add_qty * add_price)) / total_qty
    return new_avg
    
@st.cache_data(ttl=3600)
def check_stock_full_detail(ticker):
    """
    株価、配当、業種データを取得。
    stock.infoは重いため、まずは株価(history)を優先し、
    infoが失敗してもアプリが止まらないようにします。
    """
    try:
        stock = yf.Ticker(ticker)
        
        # 1. 株価チャートと現在値を取得 (infoより圧倒的に軽い)
        hist = stock.history(period="1y")
        if hist.empty:
            return None
        
        current_price = hist['Close'].iloc[-1]
        
        # 2. 業種と配当利回りを「おまけ」として取得を試みる
        # ここでエラーが起きても、株価さえあれば表示は継続させる
        sector = "不明"
        dividend_rate = 0
        div_months = []
        
        try:
            # .info へのアクセスを最小限にするための try-except
            s_info = stock.info
            sector = s_info.get('sector', '不明')
            dividend_rate = s_info.get('dividendRate', 0)
        except:
            # アクセス制限にかかった場合は、デフォルト値のまま進む
            pass

        # 3. 配当月を履歴から算出 (これも失敗してもOK)
        try:
            div_history = stock.dividends
            if not div_history.empty:
                div_months = list(set(div_history.tail(4).index.month))
        except:
            pass

        return {
            "price": current_price,
            "yield": 0, # 計算が必要なら追加
            "annual_div": dividend_rate,
            "sector": sector,
            "div_months": div_months,
            "history": hist['Close']
        }
        
    except Exception as e:
        # 万が一アクセス制限で完全に止まった場合
        st.warning(f"Yahoo Financeの制限により {ticker} の詳細が取得できませんでした。少し時間をおいてください。")
        return None
