import json
import time
from logic import check_stock, send_line

# ローカルのJSONファイルを読み込む (GitHub Actionsが実行時に最新をPullしている)
with open("watchlist.json", "r", encoding="utf-8") as f:
    watchlist = json.load(f)

for name, ticker in watchlist.items():
    print(f"Checking {name}...")
    price, low, alert = check_stock(ticker, "ytd")
    
    if alert and price:
        send_line(f"【定期】{name}({ticker})が年初来安値を更新！\n現在値: {price:,.1f}円")
    
    time.sleep(2) # 制限対策
