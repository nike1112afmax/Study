#!/usr/bin/env python3
"""
診斷版 update_data.py
測試 yfinance / stooq / FRED 哪些在 GitHub Actions 上可以存取
"""

import json, sys, requests, csv, io
from datetime import date, timedelta
from pathlib import Path

# 安裝 yfinance
import subprocess
subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "-q"])
import yfinance as yf

FRED_KEY  = 'dbba37c1668a05b454005e1bcc21ac7c'
FRED_BASE = 'https://api.stlouisfed.org/fred/series/observations'

today = date.today().isoformat()
m3    = (date.today() - timedelta(days=92)).isoformat()

print("="*60)
print(f"Date range: {m3} ~ {today}")
print("="*60)

# ── 1. 測試 yfinance ──────────────────────────────────────────
print("\n[1] yfinance tests:")
yf_symbols = {
    'us_TNX':   '^TNX',
    'de_10Y':   '^TMBMKDE-10Y',
    'vix':      '^VIX',
    'wilshire': '^W5000',
}
for name, sym in yf_symbols.items():
    try:
        df = yf.Ticker(sym).history(start=m3, end=today, interval='1d', auto_adjust=False)
        if df.empty:
            print(f'  [{name}] NO DATA')
        else:
            c = df.iloc[-1]['Close']
            print(f'  [{name}] OK - {len(df)} records, latest close={c:.4f} ({df.index[-1].strftime("%Y-%m-%d")})')
    except Exception as e:
        print(f'  [{name}] ERROR: {e}')

# ── 2. 測試 stooq ─────────────────────────────────────────────
print("\n[2] stooq tests:")
stooq_symbols = {
    'us_stooq': 'us10ytj.b',
    'de_stooq': 'de10ytj.b',
    'vix_stooq': '^vix',
}
for name, sym in stooq_symbols.items():
    url = f'https://stooq.com/q/d/l/?s={sym}&d1={m3.replace("-","")}&d2={today.replace("-","")}&i=d'
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        lines = r.text.strip().split('\n')
        if r.status_code == 200 and len(lines) > 2:
            print(f'  [{name}] OK - {len(lines)-1} records, last: {lines[-1]}')
        else:
            print(f'  [{name}] FAIL - status={r.status_code}, body={r.text[:60]}')
    except Exception as e:
        print(f'  [{name}] ERROR: {e}')

# ── 3. 測試 FRED ──────────────────────────────────────────────
print("\n[3] FRED tests:")
fred_series = {
    'DGS10':        'US 10Y',
    'VIXCLS':       'VIX',
    'WILL5000INDFC':'Wilshire5000',
    'GDPC1':        'GDP',
}
for sid, name in fred_series.items():
    try:
        r = requests.get(FRED_BASE, params={
            'series_id': sid, 'api_key': FRED_KEY, 'file_type': 'json',
            'observation_start': m3, 'observation_end': today,
            'limit': 3, 'sort_order': 'desc'
        }, timeout=15)
        obs = [o for o in r.json().get('observations', []) if o['value'] != '.']
        if obs:
            print(f'  [{sid}] OK - latest: {obs[0]["date"]} = {obs[0]["value"]}')
        else:
            print(f'  [{sid}] NO DATA (status={r.status_code})')
    except Exception as e:
        print(f'  [{sid}] ERROR: {e}')

print("\n" + "="*60)
print("Diagnosis complete.")

# 存一個空的 data.json 避免 git commit 失敗
Path('data.json').write_text(json.dumps({'updated': today, '_note': 'diagnosis run'}))
