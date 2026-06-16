#!/usr/bin/env python3
"""
測試巴菲特指標的各種計算方式
"""
import requests
from datetime import date, timedelta

FRED_KEY  = 'dbba37c1668a05b454005e1bcc21ac7c'
FRED_BASE = 'https://api.stlouisfed.org/fred/series/observations'

SERIES = {
    'Wilshire PR':        'WILL5000PR',
    'Wilshire INDFC':     'WILL5000INDFC',
    'Wilshire Full Cap':  'WILL5000PRFC',
    '名目 GDP':           'GDP',
    '實質 GDP':           'GDPC1',
    '股票市值':           'NCBEILQ027S',
    '市值備選':           'BOGZ1FL073164003Q',
}

start = (date.today() - timedelta(days=365)).isoformat()
end   = date.today().isoformat()

print(f"{'指標':<20} {'Series ID':<20} {'狀態':<10} {'最新值':<15} {'日期'}")
print("-" * 80)

for name, sid in SERIES.items():
    try:
        r = requests.get(FRED_BASE, params={
            'series_id': sid, 'api_key': FRED_KEY,
            'file_type': 'json',
            'observation_start': start,
            'observation_end': end,
            'sort_order': 'desc', 'limit': 2
        }, timeout=30)
        r.raise_for_status()
        obs = [o for o in r.json().get('observations', []) if o['value'] != '.']
        if obs:
            print(f"{name:<20} {sid:<20} {'✅ OK':<10} {obs[0]['value']:<15} {obs[0]['date']}")
        else:
            print(f"{name:<20} {sid:<20} {'⚠️ EMPTY':<10}")
    except Exception as e:
        print(f"{name:<20} {sid:<20} {'❌ ERROR':<10} {str(e)[:30]}")

print("\n完成！")
