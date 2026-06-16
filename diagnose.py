#!/usr/bin/env python3
"""
診斷腳本：測試各國官方利率 FRED series
並對照已知的最新實際值
"""

import requests
from datetime import date, timedelta

FRED_KEY  = 'dbba37c1668a05b454005e1bcc21ac7c'
FRED_BASE = 'https://api.stlouisfed.org/fred/series/observations'

SERIES = {
    '美國 聯邦基金利率':   ('FEDFUNDS',           '3.75~4.00%'),
    '歐元區 ECB利率':      ('ECBDFR',             '2.25%'),
    '日本 日銀政策利率':   ('IRSTCB01JPM156N',    '1.00% (剛升息)'),
    '英國 英格蘭銀行利率': ('IRSTCB01GBM156N',    '4.25%'),
    '澳洲 RBA現金利率':    ('IRSTCB01AUM156N',    '3.85%'),
    '韓國 央行基準利率':   ('IRSTCB01KRM156N',    '2.75%'),
    '台灣 央行重貼現率':   ('INTDSRTW01STQ',      '2.00%'),
    '台灣 備選(月度)':     ('INTDSRTW01STM',      '2.00%'),
}

start = (date.today() - timedelta(days=365*2)).isoformat()
end   = date.today().isoformat()

print(f"{'指標':<25} {'Series ID':<25} {'狀態':<10} {'FRED最新值':<12} {'FRED日期':<15} {'實際應為'}")
print("-" * 105)

for name, (sid, expected) in SERIES.items():
    try:
        r = requests.get(FRED_BASE, params={
            'series_id': sid, 'api_key': FRED_KEY,
            'file_type': 'json',
            'observation_start': start,
            'observation_end': end,
            'sort_order': 'desc', 'limit': 3
        }, timeout=30)
        r.raise_for_status()
        obs = [o for o in r.json().get('observations', []) if o['value'] != '.']
        if obs:
            latest = obs[0]
            print(f"{name:<25} {sid:<25} {'✅ OK':<10} {latest['value']:<12} {latest['date']:<15} {expected}")
        else:
            print(f"{name:<25} {sid:<25} {'⚠️ EMPTY':<10} {'—':<12} {'—':<15} {expected}")
    except Exception as e:
        print(f"{name:<25} {sid:<25} {'❌ ERROR':<10} {str(e)[:20]:<12} {'—':<15} {expected}")

print("\n完成！")
