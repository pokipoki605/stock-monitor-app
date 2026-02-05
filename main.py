import streamlit as st
import pandas as pd
from logic import get_watchlist, save_watchlist, check_stock_detail, get_jp_stock_list, calculate_new_average

st.set_page_config(page_title="My Portfolio", layout="wide")
st.title("💰 資産管理・高配当監視ボード")

watchlist, sha = get_watchlist()
jpx_df = get_jp_stock_list()

# --- サイドバー：購入・登録 ---
with st.sidebar:
    st.header("🛒 銘柄登録・買い増し")
    selected_stock = st.selectbox("銘柄検索", options=jpx_df['display'].tolist(), index=None)
    buy_price = st.number_input("購入価格 (円)", min_value=0.0)
    buy_qty = st.number_input("株数", min_value=0)
    
    if st.button("ポートフォリオに反映"):
        if selected_stock and buy_qty > 0:
            code = selected_stock.split(": ")[0]
            name = selected_stock.split(": ")[1]
            ticker = f"{code}.T"
            
            # すでに持っている場合は平均単価を再計算
            if name in watchlist:
                old_qty = watchlist[name].get('qty', 0)
                old_avg = watchlist[name].get('avg_cost', 0)
                new_avg = calculate_new_average(old_qty, old_avg, buy_qty, buy_price)
                watchlist[name]['qty'] = old_qty + buy_qty
                watchlist[name]['avg_cost'] = new_avg
            else:
                watchlist[name] = {'ticker': ticker, 'qty': buy_qty, 'avg_cost': buy_price}
            
            save_watchlist(watchlist)
            st.success(f"{name} を反映しました")
            st.rerun()

# --- メイン画面：ポートフォリオ一覧 ---
if watchlist:
    total_profit = 0
    data_for_table = []
    
    for name, info in watchlist.items():
        stock_data = check_stock_detail(info['ticker'])
        if stock_data:
            current = stock_data['price']
            avg = info['avg_cost']
            qty = info['qty']
            
            # 含み益の計算
            profit = (current - avg) * qty
            total_profit += profit
            
            data_for_table.append({
                "銘柄": name,
                "現在値": f"{current:,.1f}円",
                "取得単価": f"{avg:,.1f}円",
                "保有数": f"{qty}株",
                "配当利回り": f"{stock_data['yield']:.2f}%",
                "含み損益": profit,
                "history": stock_data['history'] # チャート用
            })

    # 合計損益の表示
    st.metric("トータル含み損益", f"{total_profit:,.0f} 円", delta=f"{total_profit:,.0f} 円")

    # 銘柄ごとの詳細表示
    for item in data_for_table:
        with st.expander(f"{item['銘柄']} (損益: {item['含み損益']:,.0f}円 / 利回り: {item['配当利回り']})"):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.write(f"**現在値:** {item['現在値']}")
                st.write(f"**取得単価:** {item['取得単価']}")
                if st.button(f"全部売却 (削除)", key=item['銘柄']):
                    del watchlist[item['銘柄']]
                    save_watchlist(watchlist)
                    st.rerun()
            with col2:
                # 株価チャートの表示
                st.line_chart(item['history'])
