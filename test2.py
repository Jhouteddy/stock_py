import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager

# 設置中文字體
font_path = "C:/Windows/Fonts/msyh.ttc"  # Windows 系統的微軟正黑體字體路徑
font_prop = font_manager.FontProperties(fname=font_path)

# 下載資料
ticker = '00631L.TW'
data = yf.download(ticker, start='2015-01-01', auto_adjust=True)

# 計算布林通道
data['MA20'] = data['Close'].rolling(window=20).mean()
data['STD20'] = data['Close'].rolling(window=20).std()
data['Upper'] = data['MA20'] + 2 * data['STD20']
data['Lower'] = data['MA20'] - 2 * data['STD20']
data.dropna(inplace=True)  # 去除 NaN

# 初始資金與持倉（50:50）
initial_cash = 1_000_000
cash = initial_cash * 0.5
shares = (initial_cash * 0.5) / data['Close'].iloc[0]

portfolio_values = []
positions = []

# 狀態記錄
pending_buy = False
pending_sell = False
buy_points = []  # 記錄買入的時間點
sell_points = []  # 記錄賣出的時間點

# 回測主迴圈
for i in range(1, len(data)):
    idx = data.index[i]
    prev_idx = data.index[i - 1]

    # 確保 `price` 和 `volume` 是單個數值
    price = data.loc[idx, 'Close'].values[0]
    volume = data.loc[idx, 'Volume'].values[0]

    # 前一天判斷 (確保獲取的是單一數值)
    yesterday_close = data.loc[prev_idx, 'Close'].values[0]
    yesterday_upper = data.loc[prev_idx, 'Upper'].values[0]
    yesterday_lower = data.loc[prev_idx, 'Lower'].values[0]
    today_upper = data.loc[idx, 'Upper'].values[0]
    today_lower = data.loc[idx, 'Lower'].values[0]

    # 條件設定 (確保是單一數值)
    if yesterday_close >= yesterday_upper:
        pending_sell = True
        pending_buy = False
    elif yesterday_close <= yesterday_lower:
        pending_buy = True
        pending_sell = False
    else:
        pending_buy = False
        pending_sell = False

    # 賣出條件：跌回布林上通道以內
    if pending_sell and price < today_upper:
        total = cash + shares * price
        target_cash = total * 0.5
        shares = (total - target_cash) / price
        cash = target_cash
        sell_points.append(idx)  # 記錄賣出時間點
        pending_sell = False

    # 買入條件：有量 + 回到布林下通道上方
    if pending_buy and volume > 0 and price > today_lower:
        total = cash + shares * price
        target_stock_value = total * 0.5
        shares = target_stock_value / price
        cash = total - target_stock_value
        buy_points.append(idx)  # 記錄買入時間點
        pending_buy = False

    # 資產統計
    total_value = cash + shares * price
    portfolio_values.append(total_value)
    positions.append(shares * price / total_value)

# 結果輸出
result = data.iloc[1:].copy()  # 從第1天開始
result['Portfolio'] = portfolio_values
result['Position'] = positions

# 繪圖
plt.figure(figsize=(14, 6))
plt.plot(result.index, result['Portfolio'], label='資產總值', color='green')

# 標記買入和賣出的點
plt.scatter(buy_points, result.loc[buy_points, 'Portfolio'], color='blue', label='買入點', marker='o', s=100)
plt.scatter(sell_points, result.loc[sell_points, 'Portfolio'], color='red', label='賣出點', marker='o', s=100)

plt.title('00631L 布林通道再平衡策略（50:50 配置）', fontproperties=font_prop)
plt.xlabel('日期', fontproperties=font_prop)
plt.ylabel('新台幣資產價值', fontproperties=font_prop)
plt.grid(True)
plt.legend(prop=font_prop)
plt.tight_layout()
plt.show()
