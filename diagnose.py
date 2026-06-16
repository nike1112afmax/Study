#!/usr/bin/env python3
"""
診斷腳本：測試各國官方利率 FRED series（修正版）
"""

import requests
from datetime import date, timedelta

FRED_KEY  = 'dbba37c1668a05b454005e1bcc21ac7c'
FRED_BASE = 'https://api.stlouisfed.org/fred/series/observations'

SERIES = {
    '美國 聯邦基金利率':   ('FEDFUNDS',       '3.75~4.00%'),
    '歐元區 ECB利率':      ('ECBDFR',         '2.25%'),
    '日本 日銀政策利率1':  ('IRSTCB01JPM156N','1.00%'),
    '日本 日銀政策利率2':  ('IRPOLT01JPM156N','1.00%'),
    '英國 BoE利率':        ('BOERUKM',        '3.75%'),
    '英國 備選':           ('IUDSOIA',        '3.75%'),
    '澳洲 RBA利率':        ('RBATCTR',        '4.35%'),
    '澳洲 備選':           ('IRSTCB01AUM156N','4.35%'),
    '韓國 央行利率':       ('KORR',           '2.75%'),
    '韓國 備選':           ('IRSTCB01KRM156N','2.75%'),
    '台灣 重貼現率':       ('INTDSRTW01STQ',  '2.00%'),
    '台灣 備選月度':       ('TWNREINTDSGDP',  '2.00%'),
}

start = (date.today() - timedelta(days=365*2)).isoformat()
end   = date.today().isoformat()

print(f"{'指標':<22} {'Series ID':<22} {'狀態':<10} {'FRED值':<10} {'FRED日期':<15} {'實際應為'}")
print("-" * 95)

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
            print(f"{name:<22} {sid:<22} {'✅ OK':<10} {latest['value']:<10} {latest['date']:<15} {expected}")
        else:
            print(f"{name:<22} {sid:<22} {'⚠️ EMPTY':<10} {'—':<10} {'—':<15} {expected}")
    except Exception as e:
        print(f"{name:<22} {sid:<22} {'❌ ERROR':<10} {str(e)[:15]:<10} {'—':<15} {expected}")

print("\n完成！")
