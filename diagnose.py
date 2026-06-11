#!/usr/bin/env python3
"""
診斷腳本：測試所有新增經濟指標的 FRED Series ID 是否可正常抓取
跑完後把 log 截圖給我確認
"""

import requests
from datetime import date, timedelta

FRED_KEY  = 'dbba37c1668a05b454005e1bcc21ac7c'
FRED_BASE = 'https://api.stlouisfed.org/fred/series/observations'

# 所有要驗證的 series
SERIES = {
    # 美國
    'US CPI':            'CPIAUCSL',
    'US Core CPI':       'CPILFESL',
    'US PCE':            'PCEPI',
    'US Core PCE':       'PCEPILFE',
    'US PPI':            'PPIACO',
    'US Nonfarm Payroll':'PAYEMS',
    'US Unemployment':   'UNRATE',
    'US Mfg PMI':        'NAPM',
    'US Svc PMI':        'NMFCI',
    'US GDP':            'GDPC1',
    'US Crude Inventory':'WCRSTUS1',
    # 歐洲
    'EU CPI':            'CP0000EZ19M086NEST',
    'EU Mfg PMI':        'PURCHMAN',
    'EU Svc PMI':        'EURAREA19PMSSVXMLM',
    # 日本
    'JP CPI':            'JPNCPIALLMINMEI',
    # 台灣
    'TW CPI':            'TWNPCPIPCPPPT',
}

start = (date.today() - timedelta(days=365*2)).isoformat()
end   = date.today().isoformat()

print(f"{'指標':<25} {'Series ID':<30} {'狀態':<10} {'最新日期':<15} {'最新值'}")
print("-" * 100)

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
            print(f"{name:<25} {sid:<30} {'✅ OK':<10} {latest['date']:<15} {latest['value']}")
        else:
            print(f"{name:<25} {sid:<30} {'⚠️ EMPTY':<10} {'—':<15} 無資料")
    except Exception as e:
        print(f"{name:<25} {sid:<30} {'❌ ERROR':<10} {str(e)[:40]}")

print("\n完成！")
