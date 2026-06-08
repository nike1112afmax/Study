#!/usr/bin/env python3
"""
每日抓取10年期公債殖利率與情緒指標，存成 data.json
資料來源（經 GitHub Actions 實測確認可用）：
  - 美國 10Y：yfinance ^TNX（日度）
  - 德/英/日/澳 10Y：FRED 月度（拉2年確保3M視窗有資料）
  - VIX：FRED VIXCLS（日度）
  - Wilshire 5000：yfinance ^W5000（日度，指數點×1.05=十億美元）
  - GDP：FRED GDPC1（季度）
"""

import json, sys, requests
from datetime import date, timedelta
from pathlib import Path

import subprocess
subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "-q"])
import yfinance as yf

FRED_KEY  = 'dbba37c1668a05b454005e1bcc21ac7c'
FRED_BASE = 'https://api.stlouisfed.org/fred/series/observations'

FRED_YIELDS = {
    'de': 'IRLTLT01DEM156N',
    'gb': 'IRLTLT01GBM156N',
    'jp': 'IRLTLT01JPM156N',
    'au': 'IRLTLT01AUM156N',
}

def yf_fetch(symbol, start, end, divide10=False, multiply10=False):
    df = yf.Ticker(symbol).history(start=start, end=end, interval='1d', auto_adjust=False)
    if df.empty:
        return []
    result = []
    for idx, row in df.iterrows():
        v = float(row['Close'])
        if v > 0:
            if divide10:
                v = round(v / 10, 4)
            if multiply10:
                v = round(v * 10, 4)
            result.append({'d': idx.strftime('%Y-%m-%d'), 'v': round(v, 4)})
    return sorted(result, key=lambda x: x['d'])

def fred_fetch(series_id, start, end):
    r = requests.get(FRED_BASE, params={
        'series_id': series_id, 'api_key': FRED_KEY,
        'file_type': 'json', 'observation_start': start, 'observation_end': end,
    }, timeout=30)
    r.raise_for_status()
    return [{'d': o['date'], 'v': float(o['value'])}
            for o in r.json().get('observations', []) if o['value'] != '.']

def main():
    today = date.today().isoformat()
    m3    = (date.today() - timedelta(days=92)).isoformat()
    y2    = (date.today() - timedelta(days=730)).isoformat()
    y3    = (date.today() - timedelta(days=1095)).isoformat()

    data = {}

    # 美國 10Y（yfinance ^TNX，值直接是 4.536% 不需換算）
    print('Fetching us (yfinance ^TNX)...')
    try:
        data['us'] = yf_fetch('^TNX', m3, today)
        print(f'  → {len(data["us"])} records, latest: {data["us"][-1] if data["us"] else "N/A"}')
    except Exception as e:
        print(f'  → ERROR: {e}, fallback to FRED DGS10')
        try:
            data['us'] = fred_fetch('DGS10', m3, today)
            print(f'  → FRED fallback: {len(data["us"])} records')
        except:
            data['us'] = []

    # 德/英/日/澳 10Y（FRED 月度，拉2年）
    for key, sid in FRED_YIELDS.items():
        print(f'Fetching {key} (FRED {sid})...')
        try:
            data[key] = fred_fetch(sid, y2, today)
            print(f'  → {len(data[key])} records, latest: {data[key][-1] if data[key] else "N/A"}')
        except Exception as e:
            print(f'  → ERROR: {e}')
            data[key] = []

    # VIX（FRED VIXCLS）
    print('Fetching vix (FRED VIXCLS)...')
    try:
        data['vix'] = fred_fetch('VIXCLS', m3, today)
        print(f'  → {len(data["vix"])} records, latest: {data["vix"][-1] if data["vix"] else "N/A"}')
    except Exception as e:
        print(f'  → ERROR: {e}')
        data['vix'] = []

    # Wilshire 5000（yfinance ^W5000，指數點，巴菲特計算時×1.05換算十億USD）
    print('Fetching wilshire (yfinance ^W5000)...')
    try:
        data['wilshire'] = yf_fetch('^W5000', y2, today)
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

    # 巴菲特指標 = Wilshire5000市值(十億USD) / GDP(十億USD) * 100
    # ^W5000 是指數點，1 point ≈ 1.05 billion USD（Wilshire 官方換算）
    # 換算係數：^W5000 是價格指數，需乘此係數換算成市值(十億USD)
    # 推導：目前巴菲特約214%，GDP≈24152B，^W5000≈73741 → k = 214×24152/(73741×100) ≈ 0.701
    W5000_TO_BILLION = 0.701
    gdp_map   = {p['d']: p['v'] for p in data.get('gdp', [])}
    gdp_dates = sorted(gdp_map.keys())
    buffett   = []
    for p in data.get('wilshire', []):
        gd = next((d for d in reversed(gdp_dates) if d <= p['d']), None)
        if gd and gdp_map[gd] > 0:
            market_cap_billions = p['v'] * W5000_TO_BILLION
            buffett.append({'d': p['d'], 'v': round(market_cap_billions / gdp_map[gd] * 100, 1)})
    data['buffett'] = buffett
    print(f'Buffett: {len(buffett)} records, latest: {buffett[-1] if buffett else "N/A"}')

    data['updated'] = today

    out = Path(__file__).parent / 'data.json'
    out.write_text(json.dumps(data, separators=(',', ':')))
    print(f'\n✓ data.json saved ({out.stat().st_size:,} bytes)')
    print(f'✓ Updated: {today}')

if __name__ == '__main__':
    main()
