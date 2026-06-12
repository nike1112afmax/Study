#!/usr/bin/env python3
"""
診斷腳本：測試重要資產價格 yfinance 代碼是否可用
"""

import subprocess, sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "-q"])
import yfinance as yf
from datetime import date, timedelta

ASSETS = {
    '美元指數':   'DX-Y.NYB',
    '歐元指數':   'EUR=X',
    '歐元指數2':  '^XEU',
    '美元兌日圓': 'USDJPY=X',
    '美元兌台幣': 'TWD=X',
    '美元兌台幣2':'USDTWD=X',
    '美元兌人民幣':'CNY=X',
    '美元兌人民幣2':'USDCNY=X',
    '紐約黃金':   'GC=F',
    '金蟲指數':   'HUI',
    '金蟲指數2':  'GDX',
    '金蟲指數3':  '^HUI',
    'CRB指數':    '^CRBQ',
    'CRB指數2':   'CRBQ',
    'CRB指數3':   '^CRY',
    '布蘭特原油': 'BZ=F',
    '紐約原油':   'CL=F',
}

start = (date.today() - timedelta(days=5)).isoformat()
end   = date.today().isoformat()

print(f"{'資產':<15} {'代碼':<20} {'狀態':<10} {'最新值':<15} {'日期'}")
print("-" * 75)

for name, symbol in ASSETS.items():
    try:
        df = yf.Ticker(symbol).history(start=start, end=end, interval='1d', auto_adjust=False)
        if df.empty:
            print(f"{name:<15} {symbol:<20} {'⚠️ EMPTY':<10}")
        else:
            latest = df.iloc[-1]
            print(f"{name:<15} {symbol:<20} {'✅ OK':<10} {latest['Close']:<15.4f} {df.index[-1].strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"{name:<15} {symbol:<20} {'❌ ERROR':<10} {str(e)[:30]}")

print("\n完成！")
