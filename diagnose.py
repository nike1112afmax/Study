#!/usr/bin/env python3
"""
測試 yfinance fast_info 即時報價
"""
import subprocess, sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "-q"])
import yfinance as yf

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

print("=== fast_info 即時報價測試 ===")
print(f"{'指標':<15} {'代碼':<15} {'狀態':<10} {'即時價格':<15} {'前收盤'}")
print("-" * 70)

for name, symbol in SYMBOLS.items():
    try:
        info = yf.Ticker(symbol).fast_info
        price = getattr(info, 'last_price', None)
        prev  = getattr(info, 'previous_close', None)
        if price and float(price) > 0:
            prev_str = f"{float(prev):.4f}" if prev is not None else '—'
            print(f"{name:<15} {symbol:<15} {'✅ OK':<10} {float(price):<15.4f} {prev_str}")
        else:
            print(f"{name:<15} {symbol:<15} {'⚠️ EMPTY':<10} price={price}")
    except Exception as e:
        print(f"{name:<15} {symbol:<15} {'❌ ERROR':<10} {str(e)[:35]}")

print("\n完成！")
