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

SERIES = {
    'us':      'DGS10',
    'de':      'IRLTLT01DEM156N',
    'gb':      'IRLTLT01GBM156N',
    'jp':      'IRLTLT01JPM156N',
    'au':      'IRLTLT01AUM156N',
    'vix':     'VIXCLS',
    'wilshire':'WILL5000INDFC',
    'gdp':     'GDP',
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
    y2    = (date.today() - timedelta(days=730)).isoformat()

    data = {}
    for key, sid in SERIES.items():
        start = y2 if key in ('wilshire', 'gdp') else m3
        print(f'Fetching {key} ({sid})...')
        try:
            data[key] = fred_fetch(sid, start, today)
            print(f'  → {len(data[key])} records')
        except Exception as e:
            print(f'  → ERROR: {e}')
            data[key] = []

    # 計算巴菲特指標
    gdp_map = {p['d']: p['v'] for p in data.get('gdp', [])}
    gdp_dates = sorted(gdp_map.keys())
    buffett = []
    for p in data.get('wilshire', []):
        gd = next((d for d in reversed(gdp_dates) if d <= p['d']), None)
        if gd:
            buffett.append({'d': p['d'], 'v': round(p['v'] / gdp_map[gd] * 100, 1)})
    data['buffett'] = buffett

    data['updated'] = today

    out = Path(__file__).parent / 'data.json'
    out.write_text(json.dumps(data, separators=(',', ':')))
    print(f'\n✓ data.json saved ({out.stat().st_size:,} bytes)')
    print(f'✓ Updated: {today}')

if __name__ == '__main__':
    main()
