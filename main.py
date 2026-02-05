import streamlit as st
import pandas as pd
import plotly.express as px
from logic import *

st.set_page_config(page_title="Stock Portfolio", layout="wide")
st.title("🚀 統合資産管理 & 期間別最安値監視")

watchlist, sha = get_watchlist()
jpx_df = get_jp_stock_list()

# --- サイドバー：登録 ---
with st.sidebar:
    st.header("🛒 銘柄登録・買い増し")
    selected_stock = st.selectbox("銘柄検索", options=jpx_df['display'].tolist(), index=None)
    buy_price = st.number_input("取得価格 (円)", min_value=0.0)
    buy_qty = st.number_input("株数", min_value=1)
    alert_pct = st.number_input("損益アラート (%)", value=10.0)

    if st.button("反映する"):
        if selected_stock:
            code = selected_stock.split(": ")[0]
            name = selected_stock.split(": ")[1]
            if name in watchlist:
                watchlist[name]['avg_cost'] = calculate_new_average(watchlist[name]['qty'], watchlist[name]['avg_cost'], buy_qty, buy_price)
                watchlist[name]['qty'] += buy_qty
                watchlist[name]['alert_pct'] = alert_pct
            else:
                watchlist[name] = {'ticker': f"{code}.T", 'qty': buy_qty, 'avg_cost': buy_price, 'alert_pct': alert_pct}
            save_watchlist(watchlist)
            st.rerun()

# --- データ集計 ---
portfolio_data = []
for name, info in list(watchlist.items()):
    data = fetch_stock_data(info['ticker'], info)
    if data:
        # 含み損益計算
        profit = (data['price'] - info['avg_cost']) * info['qty']
        profit_pct = ((data['price'] - info['avg_cost']) / info['avg_cost']) * 100
        portfolio_data.append({
            "銘柄": name, "現在値": data['price'], "取得単価": info['avg_cost'], "保有数": info['qty'],
            "含み益": profit, "損益率": profit_pct, "セクター": data['sector'],
            "ytd_low": data['low_ytd'], "3y_low": data['low_3y'], "5y_low": data['low_5y'],
            "annual_div": data['annual_div'] * info['qty'], "history": data['history'], "is_live": data['is_live']
        })

if portfolio_data:
    df = pd.DataFrame(portfolio_data)
    tab1, tab2, tab3 = st.tabs(["📋 ポートフォリオ", "💰 配当金", "📊 分析"])

    with tab1:
        st.subheader("保有銘柄一覧")
        st.dataframe(df[["銘柄", "現在値", "取得単価", "保有数", "含み益", "損益率", "セクター"]].style.format({"損益率": "{:.2f}%"}))
        
        for item in portfolio_data:
            with st.expander(f"📈 {item['銘柄']} の詳細と削除"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    if item['history'] is not None: st.line_chart(item['history'])
                with col2:
                    st.write(f"年初来最安値: {item['ytd_low']:.1f}")
                    st.write(f"3年間最安値: {item['3y_low']:.1f}")
                    if st.button(f"🗑️ {item['銘柄']} を削除", key=f"del_{item['銘柄']}"):
                        del watchlist[item['銘柄']]
                        save_watchlist(watchlist)
                        st.rerun()
    # (tab2, tab3 は前回のグラフ表示コードと同様)
else:
    st.info("銘柄を登録してください。")
