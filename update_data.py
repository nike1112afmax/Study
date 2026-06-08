#!/usr/bin/env python3
"""
每日抓取10年期公債殖利率與情緒指標，存成 data.json
- 全部改用 yfinance（Yahoo Finance），GitHub Actions 可正常存取
- GDP 維持用 FRED（唯一沒有替代的季度資料）
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    print("Installing yfinance...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance"])
    import yfinance as yf

import requests

FRED_KEY  = 'dbba37c1668a05b454005e1bcc21ac7c'
FRED_BASE = 'https://api.stlouisfed.org/fred/series/observations'

# Yahoo Finance 代碼
YF_YIELDS = {
    'us': '^TNX',           # 美國 10Y（× 直接是 % 值）
    'de': '^TMBMKDE-10Y',   # 德國 10Y
    'gb': '^TMBMKGB-10Y',   # 英國 10Y
    'jp': '^TMBMKJP-10Y',   # 日本 10Y
    'au': '^TMBMKAU-10Y',   # 澳洲 10Y
}

def yf_fetch(symbol, start, end):
    """用 yfinance 抓歷史收盤價"""
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, end=end, interval='1d', auto_adjust=False)
    if df.empty:
        return []
    result = []
    for idx, row in df.iterrows():
        d = idx.strftime('%Y-%m-%d')
        v = round(float(row['Close']), 4)
        if v > 0:
            result.append({'d': d, 'v': v})
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
    today     = date.today().isoformat()
    m3        = (date.today() - timedelta(days=92)).isoformat()
    y2        = (date.today() - timedelta(days=730)).isoformat()
    y3        = (date.today() - timedelta(days=1095)).isoformat()

    data = {}

    # 10Y 公債殖利率（Yahoo Finance）
    for key, symbol in YF_YIELDS.items():
        print(f'Fetching {key} ({symbol})...')
        try:
            result = yf_fetch(symbol, m3, today)
            # ^TNX 是 ×10 的值（44.7 = 4.47%），需除以 10
            if key == 'us' and result and result[-1]['v'] > 20:
                result = [{'d': p['d'], 'v': round(p['v'] / 10, 4)} for p in result]
                print(f'  → TNX unit correction applied (/10)')
            data[key] = result
            print(f'  → {len(result)} records, latest: {result[-1] if result else "N/A"}')
        except Exception as e:
            print(f'  → ERROR: {e}')
            data[key] = []

    # VIX（Yahoo Finance）
    print('Fetching vix (^VIX)...')
    try:
        data['vix'] = yf_fetch('^VIX', m3, today)
        print(f'  → {len(data["vix"])} records, latest: {data["vix"][-1] if data["vix"] else "N/A"}')
    except Exception as e:
        print(f'  → ERROR: {e}')
        # fallback: FRED
        try:
            data['vix'] = fred_fetch('VIXCLS', m3, today)
            print(f'  → FRED fallback: {len(data["vix"])} records')
        except:
            data['vix'] = []

    # Wilshire 5000（Yahoo Finance ^W5000）
    print('Fetching wilshire (^W5000)...')
    try:
        data['wilshire'] = yf_fetch('^W5000', y2, today)
        print(f'  → {len(data["wilshire"])} records, latest: {data["wilshire"][-1] if data["wilshire"] else "N/A"}')
    except Exception as e:
        print(f'  → ERROR: {e}, fallback to FRED...')
        try:
            data['wilshire'] = fred_fetch('WILL5000INDFC', y2, today)
            print(f'  → FRED fallback: {len(data["wilshire"])} records')
        except Exception as e2:
            print(f'  → FRED fallback ERROR: {e2}')
            data['wilshire'] = []

    # GDP（FRED，唯一沒有替代的）
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
