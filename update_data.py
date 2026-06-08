#!/usr/bin/env python3
"""
每日從 FRED API 抓取公債殖利率與情緒指標，存成 data.json
供 10Ydashboard.html 讀取
"""

import requests
import json
from datetime import date, timedelta
from pathlib import Path

FRED_KEY = 'dbba37c1668a05b454005e1bcc21ac7c'
FRED_BASE = 'https://api.stlouisfed.org/fred/series/observations'

# 全部改用日度資料，避免月度資料稀疏問題
# 德國/英國/日本/澳洲改用 OECD 日度 series
SERIES = {
    'us':       ('DGS10',            'daily'),   # 美國 10Y 日度
    'de':       ('IRLTLT01DEM156N',  'monthly'), # 德國 10Y 月度（OECD）
    'gb':       ('IRLTLT01GBM156N',  'monthly'), # 英國 10Y 月度（OECD）
    'jp':       ('IRLTLT01JPM156N',  'monthly'), # 日本 10Y 月度（OECD）
    'au':       ('IRLTLT01AUM156N',  'monthly'), # 澳洲 10Y 月度（OECD）
    'vix':      ('VIXCLS',           'daily'),   # VIX 日度
    'wilshire': ('WILL5000INDFC',    'daily'),   # Wilshire 5000 日度
    'gdp':      ('GDPC1',            'quarterly'),# 實質 GDP 季度（比 GDP 更新快）
}

def fred_fetch(series_id, start, end):
    r = requests.get(FRED_BASE, params={
        'series_id': series_id,
        'api_key': FRED_KEY,
        'file_type': 'json',
        'observation_start': start,
        'observation_end': end,
    }, timeout=30)
    r.raise_for_status()
    obs = r.json().get('observations', [])
    return [{'d': o['date'], 'v': float(o['value'])}
            for o in obs if o['value'] != '.']

def main():
    today = date.today().isoformat()
    m3    = (date.today() - timedelta(days=92)).isoformat()
    m6    = (date.today() - timedelta(days=183)).isoformat()
    y2    = (date.today() - timedelta(days=730)).isoformat()
    y3    = (date.today() - timedelta(days=1095)).isoformat()

    data = {}
    for key, (sid, freq) in SERIES.items():
        # 月度資料拉更長以確保3個月內有資料點
        if freq == 'monthly':
            start = y2        # 2年確保有足夠月度點
        elif freq == 'quarterly':
            start = y3        # 3年確保有足夠季度點
        elif key == 'wilshire':
            start = y2
        else:
            start = m3

        print(f'Fetching {key} ({sid}, {freq})...')
        try:
            data[key] = fred_fetch(sid, start, today)
            print(f'  → {len(data[key])} records, latest: {data[key][-1]["d"] if data[key] else "N/A"}')
        except Exception as e:
            print(f'  → ERROR: {e}')
            data[key] = []

    # 計算巴菲特指標
    # Wilshire 5000（市值，十億美元）/ 實質 GDP（十億美元）* 100
    gdp_map = {p['d']: p['v'] for p in data.get('gdp', [])}
    gdp_dates = sorted(gdp_map.keys())
    buffett = []
    for p in data.get('wilshire', []):
        # 找最近一個季度 GDP
        gd = next((d for d in reversed(gdp_dates) if d <= p['d']), None)
        if gd and gdp_map[gd] > 0:
            ratio = round(p['v'] / gdp_map[gd] * 100, 1)
            buffett.append({'d': p['d'], 'v': ratio})

    data['buffett'] = buffett
    print(f'Buffett indicator: {len(buffett)} records, latest: {buffett[-1] if buffett else "N/A"}')

    data['updated'] = today

    out = Path(__file__).parent / 'data.json'
    out.write_text(json.dumps(data, separators=(',', ':')))
    print(f'\n✓ data.json saved ({out.stat().st_size:,} bytes)')
    print(f'✓ Updated: {today}')

if __name__ == '__main__':
    main()
