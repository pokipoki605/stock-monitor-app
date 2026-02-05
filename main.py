import streamlit as st
from logic import get_watchlist, save_watchlist, check_stock

st.title("🇯🇵 日本株 監視マネージャー")

# 1. 現在のリストをGitHubから読み込む
watchlist, sha = get_watchlist()

# --- 銘柄追加セクション ---
st.subheader("➕ 銘柄を追加")
col1, col2 = st.columns([3, 1])
with col1:
    new_code = st.text_input("銘柄コード (例: 7203)", placeholder="数字4桁")
with col2:
    new_name = st.text_input("表示名", placeholder="トヨタ")

if st.button("監視リストに登録"):
    if new_code and new_name:
        ticker = f"{new_code}.T"
        watchlist[new_name] = ticker
        if save_watchlist(watchlist):
            st.success(f"{new_name} を追加しました！GitHub反映に数分かかる場合があります。")
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
