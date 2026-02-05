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
for name, info in watchlist.items():
    if name.startswith("_"): continue
    
    # logic.pyのcheck_stockを呼び出し
    price, low, alert_low = check_stock(info['ticker'])
    
    # 個別設定を読み込み（なければデフォルト10%）
    threshold = info.get('alert_pct', 10.0)
    
    profit_pct = ((price - info['avg_cost']) / info['avg_cost']) * 100
    
    # 個別のしきい値で判定
    if abs(profit_pct) >= threshold:
        direction = "利益" if profit_pct > 0 else "損失"
        send_line(f"【個別アラート】\n{name} の{direction}が設定値({threshold}%)を超えました。\n現在損益: {profit_pct:.1f}%\n現在値: {price:,.1f}円")
