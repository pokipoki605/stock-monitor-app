import streamlit as st
from logic import get_watchlist, save_watchlist, check_stock, get_jp_stock_list

st.set_page_config(page_title="日本株マネージャー", layout="wide")
st.title("🇯🇵 日本株 監視＆管理")

# 1. 現在のリストをGitHubから読み込む
watchlist, sha = get_watchlist()

# --- 銘柄追加セクション ---
with st.sidebar:
    st.header("🔍 銘柄を検索して追加")
    
    # 社名やコードを入力すると候補が出る検索ボックス
    selected_stock = st.selectbox(
        "社名またはコードを入力",
        options=jpx_df['display'].tolist(),
        index=None,
        placeholder="例: トヨタ、7203"
    )

    if st.button("監視リストに登録"):
        if selected_stock:
            # 「7203: トヨタ自動車」からコードと名前を切り分ける
            code = selected_stock.split(": ")[0]
            name = selected_stock.split(": ")[1]
            
            ticker = f"{code}.T"
            watchlist[name] = ticker
            
            if save_watchlist(watchlist):
                st.success(f"「{name}」を追加しました！")
                st.rerun()

# --- 現在のリストと削除セクション ---
st.subheader("📋 監視中の銘柄")
if not watchlist:
    st.info("現在、監視中の銘柄はありません。")
else:
    for name, ticker in list(watchlist.items()):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1: st.write(f"**{name}** ({ticker})")
        with c2:
            if st.button(f"更新チェック: {name}"):
                price, low, alert = check_stock(ticker)
                st.write(f"{price:,.1f}円 (安値:{low:,.1f})")
        with c3:
            if st.button("🗑️ 削除", key=ticker):
                del watchlist[name]
                save_watchlist(watchlist)
                st.rerun()

st.sidebar.caption("※削除・追加後は、GitHub Actions側にも自動で反映されます。")
