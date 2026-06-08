#!/usr/bin/env python3
"""
每日抓取10年期公債殖利率與情緒指標，存成 data.json
- 10Y公債(美/德/英/日/澳) + VIX：stooq.com（日度）
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

STOOQ_YIELDS = {
    'us': 'us10ytj.b',
    'de': 'de10ytj.b',
    'gb': 'gb10ytj.b',
    'jp': 'jp10ytj.b',
    'au': 'au10ytj.b',
}

def stooq_fetch(symbol, start, end):
    url = f'https://stooq.com/q/d/l/?s={symbol}&d1={start.replace("-","")}&d2={end.replace("-","")}&i=d'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    reader = csv.DictReader(io.StringIO(r.text))
    result = []
    for row in reader:
        try:
            v = float(row['Close'])
            result.append({'d': row['Date'], 'v': v})
        except (KeyError, ValueError):
            continue
    result = sorted(result, key=lambda x: x['d'])

    # 自動偵測單位：若最大值 < 2，代表是小數格式（0.044 = 4.4%），乘以100換算
    if result:
        max_v = max(p['v'] for p in result)
        if max_v < 2.0:
            result = [{'d': p['d'], 'v': round(p['v'] * 100, 4)} for p in result]
            print(f'  → unit conversion applied (max was {max_v:.4f}, multiplied by 100)')

    return result

def stooq_fetch_vix(start, end):
    """VIX 用獨立函式，不做單位換算"""
    url = f'https://stooq.com/q/d/l/?s=^vix&d1={start.replace("-","")}&d2={end.replace("-","")}&i=d'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    reader = csv.DictReader(io.StringIO(r.text))
    result = []
    for row in reader:
        try:
            result.append({'d': row['Date'], 'v': round(float(row['Close']), 2)})
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

    # 10Y 公債殖利率（stooq）
    for key, symbol in STOOQ_YIELDS.items():
        print(f'Fetching {key} yield (stooq {symbol})...')
        try:
            data[key] = stooq_fetch(symbol, m3, today)
            if data[key]:
                print(f'  → {len(data[key])} records, latest: {data[key][-1]}')
            else:
                print(f'  → NO DATA')
        except Exception as e:
            print(f'  → ERROR: {e}')
            data[key] = []

    # VIX（stooq）
    print('Fetching vix (stooq ^vix)...')
    try:
        data['vix'] = stooq_fetch_vix(m3, today)
        if data['vix']:
            print(f'  → {len(data["vix"])} records, latest: {data["vix"][-1]}')
        else:
            print(f'  → NO DATA')
    except Exception as e:
        print(f'  → ERROR: {e}')
        # VIX fallback: FRED
        print('  → Fallback to FRED VIXCLS...')
        try:
            data['vix'] = fred_fetch('VIXCLS', m3, today)
            print(f'  → FRED fallback: {len(data["vix"])} records, latest: {data["vix"][-1] if data["vix"] else "N/A"}')
        except Exception as e2:
            print(f'  → FRED fallback ERROR: {e2}')
            data['vix'] = []

    # Wilshire 5000（FRED）
    print('Fetching wilshire (FRED WILL5000INDFC)...')
    try:
        data['wilshire'] = fred_fetch('WILL5000INDFC', y2, today)
        print(f'  → {len(data["wilshire"])} records, latest: {data["wilshire"][-1] if data["wilshire"] else "N/A"}')
    except Exception as e:
        print(f'  → ERROR: {e}')
        data['wilshire'] = []

    # GDP（FRED GDPC1）
    print('Fetching gdp (FRED GDPC1)...')
    try:
        data['gdp'] = fred_fetch('GDPC1', y3, today)
        print(f'  → {len(data["gdp"])} records, latest: {data["gdp"][-1] if data["gdp"] else "N/A"}')
    except Exception as e:
        print(f'  → ERROR: {e}')
        data['gdp'] = []

    # 巴菲特指標
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
