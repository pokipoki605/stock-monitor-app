import time
from logic import get_watchlist, save_watchlist, fetch_stock_data, send_line

watchlist, _ = get_watchlist()
updated = False

for name, info in watchlist.items():
    print(f"Checking {name}...")
    data = fetch_stock_data(info['ticker'], info)
    if not data or not data["is_live"]: continue

    price = data['price']
    msg = ""

    # 1. 期間別最安値判定
    if price <= data['low_5y']: msg = f"【🚨5年ぶり最安値！】\n{name}が過去5年で最も安くなっています。"
    elif price <= data['low_3y']: msg = f"【🚨3年ぶり最安値！】\n{name}が過去3年で最も安くなっています。"
    elif price <= data['low_ytd']: msg = f"【🚨年初来安値！】\n{name}が今年の最安値を更新しました。"

    # 2. 個別損益アラート判定
    profit_pct = ((price - info['avg_cost']) / info['avg_cost']) * 100
    if abs(profit_pct) >= info.get('alert_pct', 10):
        msg += f"\n【損益通知】目標値({info.get('alert_pct')}%)を超えました。現在:{profit_pct:.1f}%"

    if msg:
        send_line(f"{msg}\n銘柄: {name}\n現在値: {price:,.1f}円")

    # JSONを最新情報で更新（キャッシュ化）
    watchlist[name]['last_price'] = price
    watchlist[name]['sector'] = data['sector']
    watchlist[name]['annual_div'] = data['annual_div']
    watchlist[name].update({"low_ytd": data['low_ytd'], "low_3y": data['low_3y'], "low_5y": data['low_5y']})
    updated = True
    time.sleep(2)

if updated:
    save_watchlist(watchlist)
