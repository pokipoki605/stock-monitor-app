import streamlit as st
from logic import check_stock_and_notify, send_line

# 日本株の簡易リスト（社名で探せるように）
JP_STOCKS = {"トヨタ": "7203.T", "ソフトバンクG": "9984.T", "任天堂": "7974.T", "ソニーG": "6758.T", "三菱UFJ": "8306.T"}

st.title("🇯🇵 日本株 監視ボード")

# 1. 銘柄を選ぶ
selected_name = st.selectbox("社名で探す", list(JP_STOCKS.keys()) + ["直接入力"])
if selected_name == "直接入力":
    ticker = st.text_input("銘柄コードを入力 (例: 9101.T)", "9101.T")
else:
    ticker = JP_STOCKS[selected_name]

period = st.radio("通知の基準にする期間", ["ytd", "1y", "3y", "5y"], horizontal=True)

# 2. 更新ボタン
if st.button("🔄 今すぐ最新情報を取得・通知チェック"):
    with st.spinner('取得中...'):
        price, low, alert = check_stock_and_notify(ticker, period)
        if price:
            st.metric("現在値", f"{price:,.1f} 円")
            st.write(f"期間内最安値: {low:,.1f} 円")
            if alert:
                st.error("🚨 安値更新！LINEに通知します。")
                send_line(f"【手動チェック】\n{selected_name}({ticker})が安値更新！\n現在値: {price:,.1f}円")
            else:
                st.success("✅ 異常ありません。")
        else:
            st.error("株価が取得できませんでした。")
