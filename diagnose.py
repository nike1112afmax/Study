#!/usr/bin/env python3
"""
測試 yfinance 各指標能否抓到最新盤中/即時數據
使用 fast_info 取得即時報價（非收盤價）
"""

import subprocess, sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "-q"])
import yfinance as yf
from datetime import date, timedelta

SYMBOLS = {
    '美國10Y':    '^TNX',
    'VIX':        '^VIX',
    '美元指數':   'DX-Y.NYB',
    '歐元/美元':  'EURUSD=X',
    '美元/日圓':  'USDJPY=X',
    '美元/台幣':  'TWD=X',
    '美元/人民幣':'CNY=X',
    '紐約黃金':   'GC=F',
    '金蟲指數':   '^HUI',
    '布蘭特原油': 'BZ=F',
    '紐約原油':   'CL=F',
    '鐵礦石':     'TIO=F',
    'Wilshire':   '^W5000',
}

print("=== 方法一：fast_info（即時報價）===")
print(f"{'指標':<15} {'代碼':<15} {'狀態':<10} {'即時價格':<15} {'前收盤'}")
print("-" * 70)

for name, symbol in SYMBOLS.items():
    try:
        info = yf.Ticker(symbol).fast_info
        price = getattr(info, 'last_price', None)
        prev  = getattr(info, 'previous_close', None)
        if price and price > 0:
            print(f"{name:<15} {symbol:<15} {'✅ OK':<10} {price:<15.4f} {prev:.4f if prev else '—'}")
        else:
            print(f"{name:<15} {symbol:<15} {'⚠️ EMPTY':<10}")
    except Exception as e:
        print(f"{name:<15} {symbol:<15} {'❌ ERROR':<10} {str(e)[:30]}")

print("\n=== 方法二：history 最新一筆（收盤價）===")
print(f"{'指標':<15} {'代碼':<15} {'狀態':<10} {'收盤價':<15} {'日期'}")
print("-" * 70)

start = (date.today() - timedelta(days=5)).isoformat()
end   = date.today().isoformat()

for name, symbol in SYMBOLS.items():
    try:
        df = yf.Ticker(symbol).history(start=start, end=end, interval='1d', auto_adjust=False)
        df = df[df['Close'].notna() & (df['Close'] > 0)]
        if df.empty:
            print(f"{name:<15} {symbol:<15} {'⚠️ EMPTY':<10}")
        else:
            latest = df.iloc[-1]
            print(f"{name:<15} {symbol:<15} {'✅ OK':<10} {latest['Close']:<15.4f} {df.index[-1].strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"{name:<15} {symbol:<15} {'❌ ERROR':<10} {str(e)[:30]}")

print("\n完成！")
