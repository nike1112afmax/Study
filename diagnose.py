#!/usr/bin/env python3
"""
診斷腳本 v2：測試修正後的 Series ID
"""

import requests
from datetime import date, timedelta

FRED_KEY  = 'dbba37c1668a05b454005e1bcc21ac7c'
FRED_BASE = 'https://api.stlouisfed.org/fred/series/observations'

# 修正後的 series（只測試上次失敗 / 空的項目）
SERIES = {
    # PMI - 用 S&P Global Markit 系列（FRED 上有完整資料）
    'US Mfg PMI':        'MANEMP',          # 先試這個
    'US Mfg PMI (ISM)':  'USNAPMFG',        # 備選
    'US Mfg PMI (Markit)':'USMFGPM',        # 備選
    'US Svc PMI':        'USNAPMNO',        # ISM Non-Mfg
    'US Svc PMI (Markit)':'USSRVPM',        # 備選
    # 原油庫存 - WCRSTUS1 是對的但可能需要不同參數
    'Crude Inv (WCRSTUS1)': 'WCRSTUS1',
    'Crude Inv (WCESTUS1)': 'WCESTUS1',     # 不含SPR
    # 日本 CPI - 改用不同的 OECD series
    'JP CPI (JPNCPIALLMINMEI)': 'JPNCPIALLMINMEI',  # 原本的，確認為何空
    'JP CPI (CPALTT01JPM661S)': 'CPALTT01JPM661S',  # 備選
    # EU PMI
    'EU Mfg PMI (DEUMFGPMISMMT)': 'DEUMFGPMISMMT',  # 德國製造業PMI
    'EU Svc PMI (DEUSRVPMISMMT)': 'DEUSRVPMISMMT',  # 德國服務業PMI
}

start = (date.today() - timedelta(days=365*2)).isoformat()
end   = date.today().isoformat()

print(f"{'指標':<35} {'Series ID':<30} {'狀態':<10} {'最新日期':<15} {'最新值'}")
print("-" * 110)

for name, sid in SERIES.items():
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
            print(f"{name:<35} {sid:<30} {'✅ OK':<10} {latest['date']:<15} {latest['value']}")
        else:
            print(f"{name:<35} {sid:<30} {'⚠️ EMPTY':<10} {'—':<15} 無資料")
    except Exception as e:
        print(f"{name:<35} {sid:<30} {'❌ ERROR':<10} {str(e)[:40]}")

print("\n完成！")
