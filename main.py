import streamlit as st
import pandas as pd
import plotly.express as px
from logic import get_watchlist, save_watchlist, check_stock_full_detail, get_jp_stock_list, calculate_new_average

# --- 初期設定 ---
st.set_page_config(page_title="Asset Manager", layout="wide")
st.title("🚀 統合資産管理システム")

# データの読み込み
watchlist, sha = get_watchlist()
jpx_df = get_jp_stock_list()

# --- 1. サイドバー（登録・編集） ---
# 表示より先に処理を行うことで、追加・変更が即座に反映されます
with st.sidebar:
    st.header("🛒 銘柄登録・編集")
    selected_stock = st.selectbox("銘柄検索", options=jpx_df['display'].tolist(), index=None, placeholder="社名またはコード")
    buy_price = st.number_input("購入/取得単価 (円)", min_value=0.0, step=1.0)
    buy_qty = st.number_input("株数", min_value=0, step=1)
    indiv_alert = st.number_input("この銘柄のアラート (%)", value=10.0, step=0.1)
    
    if st.button("ポートフォリオに反映"):
        if selected_stock and buy_qty > 0:
            code = selected_stock.split(": ")[0]
            name = selected_stock.split(": ")[1]
            ticker = f"{code}.T"
            
            if name in watchlist:
                # 既存銘柄：重み付き平均で取得単価を更新
                old_qty = watchlist[name].get('qty', 0)
                old_avg = watchlist[name].get('avg_cost', 0)
                new_avg = calculate_new_average(old_qty, old_avg, buy_qty, buy_price)
                watchlist[name]['qty'] = old_qty + buy_qty
                watchlist[name]['avg_cost'] = new_avg
                watchlist[name]['alert_pct'] = indiv_alert
            else:
                # 新規銘柄：登録
                watchlist[name] = {
                    'ticker': ticker, 
                    'qty': buy_qty, 
                    'avg_cost': buy_price,
                    'alert_pct': indiv_alert
                }
            
            save_watchlist(watchlist)
            st.success(f"「{name}」を保存しました。")
            st.rerun()

# --- 2. データ集計（バックエンド処理） ---
portfolio_data = []
for name, info in list(watchlist.items()):
    if name.startswith("_"): continue  # 設定用データを除外
    
    # logic.pyで作成した詳細取得関数を呼び出し
    detail = check_stock_full_detail(info['ticker'])
    if detail:
        # 損益率の計算
        profit_pct = ((detail['price'] - info['avg_cost']) / info['avg_cost']) * 100
        portfolio_data.append({
            "name": name, 
            "current": detail['price'], 
            "avg": info['avg_cost'],
            "qty": info['qty'], 
            "profit": (detail['price'] - info['avg_cost']) * info['qty'],
            "profit_pct": profit_pct, 
            "sector": detail['sector'],
            "annual_div": detail['annual_div'] * info['qty'], 
            "div_months": detail['div_months'],
            "history": detail['history'] # チャート表示用
        })

# --- 3. メイン表示（UI） ---
if portfolio_data:
    df_pf = pd.DataFrame(portfolio_data)
    tab1, tab2, tab3 = st.tabs(["📋 ポートフォリオ", "💰 配当金計画", "📊 資産分析"])

    with tab1:
        st.subheader("保有銘柄一覧")
        # 表示用フォーマットを整えたデータフレーム
        display_cols = ["name", "current", "avg", "qty", "profit", "profit_pct", "sector"]
        st.dataframe(
            df_pf[display_cols].style.format({
                "current": "{:,.1f}円", "avg": "{:,.1f}円", 
                "profit": "{:,.0f}円", "profit_pct": "{:+.2f}%"
            }),
            use_container_width=True
        )
        
        # 各銘柄の詳細表示（チャート・削除ボタン）
        st.divider()
        for _, row in df_pf.iterrows():
            current_alert = watchlist[row['name']].get('alert_pct', 10.0)
            with st.expander(f"📈 {row['name']} (損益: {row['profit_pct']:+.2f}% / アラート設定: {current_alert}%)"):
                col_c1, col_c2 = st.columns([2, 1])
                with col_c1:
                    st.line_chart(row['history'])
                with col_c2:
                    st.write(f"**セクター:** {row['sector']}")
                    st.write(f"**年間配当予想:** {row['annual_div']:,.0f} 円")
                    if st.button(f"🗑️ {row['name']}を削除", key=f"del_{row['name']}"):
                        del watchlist[row['name']]
                        save_watchlist(watchlist)
                        st.rerun()

    with tab2:
        st.subheader("年間配当シミュレーション")
        total_div = df_pf["annual_div"].sum()
        st.metric("予想年間配当合計 (税引前)", f"{total_div:,.0f} 円")
        
        # 月別配当グラフ
        monthly_div = {m: 0 for m in range(1, 13)}
        for _, row in df_pf.iterrows():
            if row['div_months']:
                div_per_time = row['annual_div'] / len(row['div_months'])
                for m in row['div_months']:
                    monthly_div[m] += div_per_time
        
        df_monthly = pd.DataFrame({"月": [f"{m}月" for m in range(1, 13)], "配当金": list(monthly_div.values())})
        st.bar_chart(df_monthly.set_index("月"))

    with tab3:
        st.subheader("セクター（業種）別資産構成")
        # 投資金額（現在値×株数）で割合を算出
        df_pf['total_value'] = df_pf['current'] * df_pf['qty']
        fig = px.pie(df_pf, values='total_value', names='sector', hole=0.4, 
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig, use_container_width=True)

else:
    # 銘柄が1つも無い場合の表示
    st.info("👆 左のサイドバーから、最初の銘柄を登録してみましょう。")
