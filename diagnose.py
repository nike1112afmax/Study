#!/usr/bin/env python3
"""
診斷腳本：各國官方利率 FRED series（第三輪測試）
"""
import requests
from datetime import date, timedelta

FRED_KEY  = 'dbba37c1668a05b454005e1bcc21ac7c'
FRED_BASE = 'https://api.stlouisfed.org/fred/series/observations'

SERIES = {
    '美國 FEDFUNDS':       ('FEDFUNDS',         '3.75%'),
    '歐元區 ECBDFR':       ('ECBDFR',           '2.25%'),
    '英國 IUDSOIA':        ('IUDSOIA',          '3.75%'),
    '日本 IMF折現率':      ('INTDSRJPM193N',    '1.00%'),
    '日本 overnight':      ('IRSTCB01JPM156N',  '1.00%'),
    '澳洲 IMF折現率':      ('INTDSRAUM193N',    '4.35%'),
    '澳洲 interbank':      ('IR3TIB01AUM156N',  '4.35%'),
    '韓國 IMF折現率':      ('INTDSRKRM193N',    '2.75%'),
    '台灣 IMF折現率':      ('INTDSRTW01STM',    '2.00%'),
    '台灣 備選':           ('TWNREINTDSGDP',    '2.00%'),
}

start = (date.today() - timedelta(days=365*2)).isoformat()
end   = date.today().isoformat()

print(f"{'指標':<20} {'Series ID':<22} {'狀態':<10} {'FRED值':<10} {'FRED日期':<15} {'實際應為'}")
print("-" * 90)

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
            print(f"{name:<20} {sid:<22} {'✅ OK':<10} {obs[0]['value']:<10} {obs[0]['date']:<15} {expected}")
        else:
            print(f"{name:<20} {sid:<22} {'⚠️ EMPTY':<10} {'—':<10} {'—':<15} {expected}")
    except Exception as e:
        print(f"{name:<20} {sid:<22} {'❌ ERROR':<10} {str(e)[:12]:<10} {'—':<15} {expected}")

print("\n完成！")
