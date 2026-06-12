#!/usr/bin/env python3
"""
診斷腳本：測試鋼鐵相關期貨代碼
"""

import subprocess, sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "-q"])
import yfinance as yf
from datetime import date, timedelta

SYMBOLS = {
    '熱軋鋼卷期貨 (HRC)': 'HR=F',
    '鐵礦石期貨 (SGX)':   'TIO=F',
    '鐵礦石期貨2':        'SCOA.L',
    '鋼鐵ETF (SLX)':     'SLX',
    '美國鋼鐵 (X)':       'X',
}

start = (date.today() - timedelta(days=10)).isoformat()
end   = date.today().isoformat()

print(f"{'資產':<25} {'代碼':<15} {'狀態':<10} {'最新值':<15} {'日期'}")
print("-" * 75)

for name, symbol in SYMBOLS.items():
    try:
        df = yf.Ticker(symbol).history(start=start, end=end, interval='1d', auto_adjust=False)
        df = df[df['Close'].notna() & (df['Close'] > 0)]
        if df.empty:
            print(f"{name:<25} {symbol:<15} {'⚠️ EMPTY':<10}")
        else:
            latest = df.iloc[-1]
            print(f"{name:<25} {symbol:<15} {'✅ OK':<10} {latest['Close']:<15.2f} {df.index[-1].strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"{name:<25} {symbol:<15} {'❌ ERROR':<10} {str(e)[:35]}")

print("\n完成！")
