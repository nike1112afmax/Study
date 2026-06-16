#!/usr/bin/env python3
"""
測試鐵礦石 TIO=F 的 fast_info 與 history 數值
"""
import subprocess, sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "-q"])
import yfinance as yf
from datetime import date, timedelta

symbol = 'TIO=F'
ticker = yf.Ticker(symbol)

print("=== fast_info ===")
try:
    info = ticker.fast_info
    attrs = ['last_price', 'previous_close', 'currency', 'exchange', 'quote_type']
    for a in attrs:
        val = getattr(info, a, 'N/A')
        print(f"  {a}: {val}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n=== history 最近5筆 ===")
try:
    start = (date.today() - timedelta(days=10)).isoformat()
    df = ticker.history(start=start, interval='1d', auto_adjust=False)
    df = df[df['Close'].notna() & (df['Close'] > 0)]
    print(df[['Close', 'Volume']].tail(5).to_string())
except Exception as e:
    print(f"  ERROR: {e}")

print("\n=== ticker.info 貨幣 ===")
try:
    info2 = ticker.info
    for k in ['currency', 'exchange', 'shortName', 'regularMarketPrice']:
        print(f"  {k}: {info2.get(k, 'N/A')}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n完成！")
