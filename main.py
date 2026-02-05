import streamlit as st
import pandas as pd
import plotly.express as px
from logic import get_watchlist, save_watchlist, check_stock_full_detail, get_jp_stock_list

st.set_page_config(page_title="Asset Manager", layout="wide")
st.title("🚀 統合資産管理システム")

watchlist, sha = get_watchlist()
jpx_df = get_jp_stock_list()

# --- サイドバー設定 ---
with st.sidebar:
    st.header("⚙️ 設定")
    alert_threshold = st.number_input("損益アラートしきい値 (%)", value=10.0, step=1.0)
    # watchlistに設定を保存
    if st.button("アラート設定を保存"):
        watchlist["_settings"] = {"alert_pct": alert_threshold}
        save_watchlist(watchlist)
        st.success("設定を保存しました")

# --- メイン画面 (タブ分け) ---
tab1, tab2, tab3 = st.tabs(["📋 ポートフォリオ", "💰 配当金計画", "📊 資産分析"])

# データの集計
portfolio_data = []
for name, info in list(watchlist.items()):
    if name.startswith("_"): continue # 設定データはスキップ
    detail = check_stock_full_detail(info['ticker'])
    if detail:
        profit_pct = ((detail['price'] - info['avg_cost']) / info['avg_cost']) * 100
        portfolio_data.append({
            "name": name, "qty": info['qty'], "avg": info['avg_cost'],
            "current": detail['price'], "profit": (detail['price'] - info['avg_cost']) * info['qty'],
            "profit_pct": profit_pct, "sector": detail['sector'],
            "annual_div": detail['annual_div'] * info['qty'], "div_months": detail['div_months']
        })

df_pf = pd.DataFrame(portfolio_data)

with tab1:
    st.subheader("保有銘柄一覧")
    st.dataframe(df_pf[["name", "current", "avg", "qty", "profit", "profit_pct", "sector"]])

with tab2:
    st.subheader("年間配当シミュレーション")
    total_div = df_pf["annual_div"].sum()
    st.metric("予想年間配当金 (税引前)", f"{total_div:,.0f} 円")
    
    # 月別配当グラフの作成
    monthly_div = {m: 0 for m in range(1, 13)}
    for _, row in df_pf.iterrows():
        if row['div_months']:
            div_per_time = row['annual_div'] / len(row['div_months'])
            for m in row['div_months']:
                monthly_div[m] += div_per_time
    
    df_monthly = pd.DataFrame({"月": [f"{m}月" for m in range(1, 13)], "配当金": list(monthly_div.values())})
    st.bar_chart(df_monthly.set_index("月"))

with tab3:
    st.subheader("業種別資産構成")
    # 円グラフ
    fig = px.pie(df_pf, values=df_pf['current'] * df_pf['qty'], names='sector', hole=0.4)
    st.plotly_chart(fig)
# --- main.py (抜粋) ---
with st.sidebar:
    st.header("🛒 銘柄登録・編集")
    selected_stock = st.selectbox("銘柄検索", options=jpx_df['display'].tolist(), index=None)
    buy_price = st.number_input("購入/取得単価 (円)", min_value=0.0)
    buy_qty = st.number_input("株数", min_value=0)
    # 個別のアラート設定を追加
    indiv_alert = st.number_input("この銘柄のアラート (%)", value=10.0)
    
    if st.button("ポートフォリオに反映"):
        if selected_stock and buy_qty > 0:
            code = selected_stock.split(": ")[0]
            name = selected_stock.split(": ")[1]
            ticker = f"{code}.T"
            
            if name in watchlist:
                # 既存なら平均単価計算とアラート更新
                old_qty = watchlist[name].get('qty', 0)
                old_avg = watchlist[name].get('avg_cost', 0)
                new_avg = calculate_new_average(old_qty, old_avg, buy_qty, buy_price)
                watchlist[name]['qty'] = old_qty + buy_qty
                watchlist[name]['avg_cost'] = new_avg
                watchlist[name]['alert_pct'] = indiv_alert # 更新
            else:
                # 新規登録
                watchlist[name] = {
                    'ticker': ticker, 
                    'qty': buy_qty, 
                    'avg_cost': buy_price,
                    'alert_pct': indiv_alert # 個別設定を保存
                }
            
            save_watchlist(watchlist)
            st.success(f"{name} を保存しました")
            st.rerun()

# --- ポートフォリオ表示部分 ---
if portfolio_data: # ← ここでデータがあるかチェック！
    df_pf = pd.DataFrame(portfolio_data)
    
    with tab1:
        st.subheader("保有銘柄一覧")
        # 表示する列を指定
        display_cols = ["name", "current", "avg", "qty", "profit", "profit_pct", "sector"]
        st.dataframe(df_pf[display_cols])
        
        # 個別銘柄の詳細（チャートなど）を表示
        for _, row in df_pf.iterrows():
            with st.expander(f"{row['name']} (アラート設定: {watchlist[row['name']].get('alert_pct', 10)}%)"):
                # 前回のチャート表示コードなど...
                pass
else:
    st.info("まずはサイドバーから銘柄を登録してください。")
