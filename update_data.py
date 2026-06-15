#!/usr/bin/env python3
"""
每日抓取10年期公債殖利率、情緒指標與經濟數據，存成 data.json
資料來源（經 GitHub Actions 實測確認可用）：
  - 美國 10Y：yfinance ^TNX（日度）
  - 德/英/日/澳 10Y：FRED 月度
  - VIX：FRED VIXCLS（日度）
  - Wilshire 5000：yfinance ^W5000（日度）
  - GDP：FRED GDPC1（季度）
  - 經濟指標：FRED 月度/季度
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

# 經濟指標 FRED series（已驗證可用）
FRED_ECON = {
    'us_cpi':        'CPIAUCSL',
    'us_core_cpi':   'CPILFESL',
    'us_pce':        'PCEPI',
    'us_core_pce':   'PCEPILFE',
    'us_ppi':        'PPIFID',
    'us_payroll':    'PAYEMS',
    'us_unemployment':'UNRATE',
    'us_gdp':        'GDPC1',
    'us_michigan':   'UMCSENT',
    'eu_cpi':        'CP0000EZ19M086NEST',
    'tw_cpi':        'TWNPCPIPCPPPT',
}


def yf_fetch_realtime(symbol):
    """用 fast_info 抓即時報價，回傳單筆最新數據"""
    try:
        info = yf.Ticker(symbol).fast_info
        price = getattr(info, 'last_price', None)
        if price and float(price) > 0:
            return float(price)
    except:
        pass
    return None

def yf_fetch(symbol, start, end):
    df = yf.Ticker(symbol).history(start=start, end=end, interval='1d', auto_adjust=False)
    if df.empty:
        return []
    result = []
    for idx, row in df.iterrows():
        v = float(row['Close'])
        if v > 0:
            result.append({'d': idx.strftime('%Y-%m-%d'), 'v': round(v, 4)})
    return sorted(result, key=lambda x: x['d'])

def fred_fetch(series_id, start, end):
    r = requests.get(FRED_BASE, params={
        'series_id': series_id, 'api_key': FRED_KEY,
        'file_type': 'json', 'observation_start': start, 'observation_end': end,
    }, timeout=30)
    r.raise_for_status()
    result = []
    for o in r.json().get('observations', []):
        if o['value'] == '.': continue
        row = {'d': o['date'], 'v': float(o['value'])}
        if o.get('realtime_start'):
            row['p'] = o['realtime_start']  # p = publish date（實際公布日）
        result.append(row)
    return result

def main():
    today = date.today().isoformat()
    y2    = (date.today() - timedelta(days=730)).isoformat()
    y20   = (date.today() - timedelta(days=365*20)).isoformat()

    data = {}

    # 美國 10Y（yfinance ^TNX + fast_info 即時）
    print('Fetching us (yfinance ^TNX)...')
    try:
        arr = yf_fetch('^TNX', y20, today)
        realtime = yf_fetch_realtime('^TNX')
        if realtime:
            rt_date = date.today().isoformat()
            if not arr or arr[-1]['d'] < rt_date:
                arr.append({'d': rt_date, 'v': round(realtime, 4)})
            else:
                arr[-1]['v'] = round(realtime, 4)
        data['us'] = arr
        print(f'  → {len(data["us"])} records, latest: {data["us"][-1] if data["us"] else "N/A"}')
    except Exception as e:
        print(f'  → ERROR: {e}, fallback to FRED DGS10')
        try:
            data['us'] = fred_fetch('DGS10', y20, today)
        except:
            data['us'] = []

    # 德/英/日/澳 10Y
    for key, sid in FRED_YIELDS.items():
        print(f'Fetching {key} (FRED {sid})...')
        try:
            data[key] = fred_fetch(sid, y20, today)
            print(f'  → {len(data[key])} records, latest: {data[key][-1] if data[key] else "N/A"}')
        except Exception as e:
            print(f'  → ERROR: {e}')
            data[key] = []

    # VIX（yfinance ^VIX + fast_info 即時）
    print('Fetching vix (yfinance ^VIX)...')
    try:
        arr = yf_fetch('^VIX', y20, today)
        arr = [p for p in arr if p['v'] == p['v'] and p['v'] > 0]
        realtime = yf_fetch_realtime('^VIX')
        if realtime:
            rt_date = date.today().isoformat()
            if not arr or arr[-1]['d'] < rt_date:
                arr.append({'d': rt_date, 'v': round(realtime, 4)})
            else:
                arr[-1]['v'] = round(realtime, 4)
        data['vix'] = arr
        print(f'  → {len(data["vix"])} records, latest: {data["vix"][-1] if data["vix"] else "N/A"}')
    except Exception as e:
        print(f'  → ERROR: {e}, fallback to FRED VIXCLS')
        try:
            data['vix'] = fred_fetch('VIXCLS', y20, today)
            print(f'  → FRED fallback: {len(data["vix"])} records')
        except:
            data['vix'] = []

    # Wilshire 5000
    print('Fetching wilshire (yfinance ^W5000)...')
    try:
        data['wilshire'] = yf_fetch('^W5000', y20, today)
        print(f'  → {len(data["wilshire"])} records, latest: {data["wilshire"][-1] if data["wilshire"] else "N/A"}')
    except Exception as e:
        print(f'  → ERROR: {e}')
        data['wilshire'] = []

    # GDP（實質 GDP）
    print('Fetching gdp (FRED GDPC1)...')
    try:
        data['gdp'] = fred_fetch('GDPC1', y20, today)
        print(f'  → {len(data["gdp"])} records, latest: {data["gdp"][-1] if data["gdp"] else "N/A"}')
    except Exception as e:
        print(f'  → ERROR: {e}')
        data['gdp'] = []

    # 巴菲特指標 = Wilshire5000市值(十億USD) / GDP(十億USD) * 100
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

    # 經濟指標（全部拉 20 年歷史）
    for key, sid in FRED_ECON.items():
        print(f'Fetching {key} (FRED {sid})...')
        try:
            data[key] = fred_fetch(sid, y20, today)
            print(f'  → {len(data[key])} records, latest: {data[key][-1] if data[key] else "N/A"}')
        except Exception as e:
            print(f'  → ERROR: {e}')
            data[key] = []


    # 重要資產價格（yfinance，近20年）
    ASSET_SYMBOLS = {
        'asset_dxy':    'DX-Y.NYB',
        'asset_eurusd': 'EURUSD=X',
        'asset_usdjpy': 'USDJPY=X',
        'asset_usdtwd': 'TWD=X',
        'asset_usdcny': 'CNY=X',
        'asset_gold':   'GC=F',
        'asset_hui':    '^HUI',
        'asset_brent':  'BZ=F',
        'asset_wti':    'CL=F',
        'asset_iron':   'TIO=F',
    }
    for key, symbol in ASSET_SYMBOLS.items():
        print(f'Fetching {key} (yfinance {symbol})...')
        try:
            # 先抓歷史資料
            arr = yf_fetch(symbol, y20, today)
            arr = [p for p in arr if p['v'] == p['v'] and p['v'] > 0]
            # 再用 fast_info 補上最新即時價
            realtime = yf_fetch_realtime(symbol)
            if realtime:
                rt_date = date.today().isoformat()
                # 如果最後一筆不是今天，加入今天的即時價
                if not arr or arr[-1]['d'] < rt_date:
                    arr.append({'d': rt_date, 'v': round(realtime, 4)})
                else:
                    # 更新今天的數值為即時價
                    arr[-1]['v'] = round(realtime, 4)
            data[key] = arr
            print(f'  → {len(data[key])} records, latest: {data[key][-1] if data[key] else "N/A"}')
        except Exception as e:
            print(f'  → ERROR: {e}')
            data[key] = []

    data['updated'] = today

    out = Path(__file__).parent / 'data.json'
    out.write_text(json.dumps(data, separators=(',', ':')))
    print(f'\n✓ data.json saved ({out.stat().st_size:,} bytes)')
    print(f'✓ Updated: {today}')

if __name__ == '__main__':
    main()
