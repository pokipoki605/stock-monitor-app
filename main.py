import streamlit as st
import yfinance as yf
import requests
import time
import pandas as pd
from datetime import datetime

# --- LINE設定 ---
LINE_ACCESS_TOKEN = st.secrets["LINE_ACCESS_TOKEN"]
LINE_USER_ID = st.secrets["LINE_USER_ID"]

def send_line_push(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"}
    data = {"to": LINE_USER_ID, "messages": [{"type": "text", "text": message}]}
    return requests.post(url, headers=headers, json=data).status_code

# --- ロジック関数 ---
def get_historical_low(ticker_symbol, period="1y"):
    """指定期間の最安値を取得 (period: 'ytd', '3y', '5y' など)"""
    hist = yf.Ticker(ticker_symbol).history(period=period)
    if hist.empty: return None
    return hist['Low'].min()

# --- UI ---
st.set_page_config(page_title="Stock Dashboard", layout="wide")
st.title("📊 多機能株価監視ダッシュボード")

# 監視設定（カンマ区切りで複数入力）
tickers_input = st.sidebar.text_input("監視する銘柄 (カンマ区切り)", "7203.T, 9984.T, AAPL")
tickers = [t.strip() for t in tickers_input.split(",")]

period_choice = st.sidebar.selectbox("監視基準とする期間", ["ytd", "1y", "3y", "5y"], index=0)
check_interval = st.sidebar.slider("チェック間隔（分）", 1, 60, 5)

if st.sidebar.button("監視 & ダッシュボード更新"):
    st.info(f"監視銘柄: {', '.join(tickers)} / 基準期間: {period_choice}")
    
    # 表示用プレースホルダー
    dashboard_area = st.empty()
    
    while True:
        results = []
        for ticker in tickers:
            stock = yf.Ticker(ticker)
            current_price = stock.fast_info['last_price']
            target_low = get_historical_low(ticker, period_choice)
            
            # 判定
            status = "通常"
            if target_low and current_price <= target_low:
                status = "🚨 最安値更新！"
                send_line_push(f"【通知】{ticker}が{period_choice}の最安値を更新しました。\n現在値: {current_price:.1f}\n基準値: {target_low:.1f}")
            
            results.append({
                "銘柄": ticker,
                "現在値": round(current_price, 2),
                f"{period_choice} 最安値": round(target_low, 2) if target_low else "不明",
                "状態": status
            })
        
        # ダッシュボード表示更新
        df = pd.DataFrame(results)
        with dashboard_area.container():
            st.subheader(f"現在時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            # メトリック表示（横並び）
            cols = st.columns(len(tickers))
            for i, res in enumerate(results):
                cols[i].metric(res["銘柄"], res["現在値"], delta=None)
            
            st.table(df) # 一覧表
            
        time.sleep(check_interval * 60)