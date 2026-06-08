#!/usr/bin/env python3
"""
每日抓取10年期公債殖利率與情緒指標，存成 data.json
- 10Y公債(美/德/英/日/澳) + VIX：stooq.com（日度，T-1更新）
- Wilshire5000 / GDP：FRED API（巴菲特指標用）
"""

import requests
import json
import csv
import io
from datetime import date, timedelta
from pathlib import Path

FRED_KEY  = 'dbba37c1668a05b454005e1bcc21ac7c'
FRED_BASE = 'https://api.stlouisfed.org/fred/series/observations'

# stooq 代碼對照表
STOOQ_YIELDS = {
    'us': 'us10ytj.b',  # 美國 10Y
    'de': 'de10ytj.b',  # 德國 10Y
    'gb': 'gb10ytj.b',  # 英國 10Y
    'jp': 'jp10ytj.b',  # 日本 10Y
    'au': 'au10ytj.b',  # 澳洲 10Y
}
STOOQ_VIX = '^vix'      # VIX

def stooq_fetch(symbol, start, end):
    url = f'https://stooq.com/q/d/l/?s={symbol}&d1={start.replace("-","")}&d2={end.replace("-","")}&i=d'
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    reader = csv.DictReader(io.StringIO(r.text))
    result = []
    for row in reader:
        try:
            result.append({'d': row['Date'], 'v': round(float(row['Close']), 4)})
        except (KeyError, ValueError):
            continue
    return sorted(result, key=lambda x: x['d'])

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
    y2    = (date.today() - timedelta(days=730)).isoformat()
    y3    = (date.today() - timedelta(days=1095)).isoformat()

    data = {}

    # 10Y 公債殖利率（全部用 stooq）
    for key, symbol in STOOQ_YIELDS.items():
        print(f'Fetching {key} yield (stooq {symbol})...')
        try:
            data[key] = stooq_fetch(symbol, m3, today)
            print(f'  → {len(data[key])} records, latest: {data[key][-1] if data[key] else "N/A"}')
        except Exception as e:
            print(f'  → ERROR: {e}')
            data[key] = []

    # VIX（stooq）
    print(f'Fetching vix (stooq {STOOQ_VIX})...')
    try:
        data['vix'] = stooq_fetch(STOOQ_VIX, m3, today)
        print(f'  → {len(data["vix"])} records, latest: {data["vix"][-1] if data["vix"] else "N/A"}')
    except Exception as e:
        print(f'  → ERROR: {e}')
        data['vix'] = []

    # Wilshire 5000（FRED，stooq 無此資料）
    print('Fetching wilshire (FRED WILL5000INDFC)...')
    try:
        data['wilshire'] = fred_fetch('WILL5000INDFC', y2, today)
        print(f'  → {len(data["wilshire"])} records, latest: {data["wilshire"][-1] if data["wilshire"] else "N/A"}')
    except Exception as e:
        print(f'  → ERROR: {e}')
        data['wilshire'] = []

    # GDP（FRED GDPC1，季度）
    print('Fetching gdp (FRED GDPC1)...')
    try:
        data['gdp'] = fred_fetch('GDPC1', y3, today)
        print(f'  → {len(data["gdp"])} records, latest: {data["gdp"][-1] if data["gdp"] else "N/A"}')
    except Exception as e:
        print(f'  → ERROR: {e}')
        data['gdp'] = []

    # 巴菲特指標 = Wilshire5000 / GDP * 100
    gdp_map   = {p['d']: p['v'] for p in data.get('gdp', [])}
    gdp_dates = sorted(gdp_map.keys())
    buffett   = []
    for p in data.get('wilshire', []):
        gd = next((d for d in reversed(gdp_dates) if d <= p['d']), None)
        if gd and gdp_map[gd] > 0:
            buffett.append({'d': p['d'], 'v': round(p['v'] / gdp_map[gd] * 100, 1)})
    data['buffett'] = buffett
    print(f'Buffett: {len(buffett)} records, latest: {buffett[-1] if buffett else "N/A"}')

    data['updated'] = today

    out = Path(__file__).parent / 'data.json'
    out.write_text(json.dumps(data, separators=(',', ':')))
    print(f'\n✓ data.json saved ({out.stat().st_size:,} bytes)')
    print(f'✓ Updated: {today}')

if __name__ == '__main__':
    main()
