"""
programmatic_analysis_dhan_final.py

Final full script adapted to the Dhan client methods you have:
- Uses intraday_minute_data / ohlc_data / ticker_data where available
- Normalizes responses to OHLCV DataFrame
- Runs IsolationForest anomaly detection
- Aggregates options PUT volume
- Saves final plot PNG
"""

import os
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest

# Try import dhanhq SDK
try:
    from dhanhq import dhanhq
except Exception:
    dhanhq = None

# ---------------------------
# Config - update these
# ---------------------------
DHAN_CLIENT_ID = os.environ.get('DHAN_CLIENT_ID', 'YOUR_CLIENT_ID_HERE')
DHAN_ACCESS_TOKEN = os.environ.get('DHAN_ACCESS_TOKEN', 'YOUR_ACCESS_TOKEN_HERE')
TARGET_DATE = "2024-01-17"
STOCK_NAME = "BANKNIFTY"

INSTRUMENTS = {
    'spot': {'security_id': '26001', 'exchange_segment': 'NSE_IDX'},
    'futures': {'security_id': '50123', 'exchange_segment': 'NSE_FNO'},
    'options': [
        {'security_id': '86683', 'strike': 48000, 'type': 'PE'},
        {'security_id': '86682', 'strike': 47500, 'type': 'PE'},
        {'security_id': '86681', 'strike': 47000, 'type': 'PE'},
    ]
}

INTERVAL_MINUTES = 5
SLEEP_BETWEEN_CALLS = 1
CANDIDATE_INTRA_METHOD = 'intraday_minute_data'
CANDIDATE_OHLC_METHOD = 'ohlc_data'
CANDIDATE_TICKER = 'ticker_data'
CANDIDATE_OPTION_CHAIN = 'option_chain'

# ---------------------------
# Utility: try many signatures for a method
# ---------------------------
def _try_call_various_signatures(func, kwargs_variants):
    """
    Try calling func with several kwargs combos until one works.
    Return response or None.
    """
    for kw in kwargs_variants:
        try:
            resp = func(**kw)
            return resp
        except TypeError as te:
            # signature mismatch -> try next
            # print minimal debug
            # print("TypeError for signature:", kw, "|", te)
            continue
        except Exception as e:
            # Other runtime error -> log and continue
            print("  > call raised exception for signature", kw, ":", e)
            continue
    return None

# ---------------------------
# Normalizer (same robust normalize as before)
# ---------------------------
def _normalize_response_to_df(resp):
    if resp is None:
        return None
    raw = None
    # possible wrappers
    if isinstance(resp, dict):
        if 'data' in resp and isinstance(resp['data'], (list, tuple)):
            raw = resp['data']
        elif 'result' in resp and isinstance(resp['result'], (list, tuple)):
            raw = resp['result']
        elif 'values' in resp and isinstance(resp['values'], (list, tuple)):
            raw = resp['values']
        elif 'ohlc' in resp and isinstance(resp['ohlc'], (list, tuple)):
            raw = resp['ohlc']
        else:
            # try json_normalize
            try:
                df_try = pd.json_normalize(resp)
                if df_try.empty:
                    return None
                ts_candidates = [c for c in df_try.columns if 'time' in c.lower() or 'start' in c.lower() or 'timestamp' in c.lower()]
                if ts_candidates:
                    ts = ts_candidates[0]
                    df_try['timestamp'] = pd.to_datetime(df_try[ts], unit='ms', errors='coerce').fillna(pd.to_datetime(df_try[ts], errors='coerce'))
                    df_try.set_index('timestamp', inplace=True)
                    # normalize OHLCV names
                    col_map = {c: c.lower() for c in df_try.columns}
                    df_try.rename(columns=col_map, inplace=True)
                    for req in ['open','high','low','close','volume']:
                        if req not in df_try.columns:
                            df_try[req] = np.nan
                    return df_try[['open','high','low','close','volume']].sort_index()
            except Exception:
                return None
    elif isinstance(resp, (list, tuple)):
        raw = resp
    else:
        # maybe it's already a DataFrame
        if isinstance(resp, pd.DataFrame):
            df = resp.copy()
            df.index = pd.to_datetime(df.index, errors='coerce')
            cols_lower = {c: c.lower() for c in df.columns}
            df.rename(columns=cols_lower, inplace=True)
            for req in ['open','high','low','close','volume']:
                if req not in df.columns:
                    df[req] = np.nan
            return df[['open','high','low','close','volume']].sort_index()
        return None

    if not raw:
        return None
    try:
        df = pd.DataFrame(raw)
        if df.empty:
            return None
        ts_candidates = [c for c in df.columns if 'time' in c.lower() or 'start' in c.lower() or 'timestamp' in c.lower()]
        if ts_candidates:
            ts_col = ts_candidates[0]
            df['timestamp'] = pd.to_datetime(df[ts_col], unit='ms', errors='coerce').fillna(pd.to_datetime(df[ts_col], errors='coerce'))
        else:
            try:
                df.index = pd.to_datetime(df.index, errors='coerce')
                if df.index.is_monotonic_increasing:
                    df['timestamp'] = df.index
            except Exception:
                pass
        if 'timestamp' not in df.columns:
            return None
        df.set_index('timestamp', inplace=True)
        # normalize names
        rename_map = {}
        for c in df.columns:
            lc = c.lower()
            if lc in ('open','o'): rename_map[c] = 'open'
            elif lc in ('high','h'): rename_map[c] = 'high'
            elif lc in ('low','l'): rename_map[c] = 'low'
            elif lc in ('close','c','last','price'): rename_map[c] = 'close'
            elif 'vol' in lc: rename_map[c] = 'volume'
        df.rename(columns=rename_map, inplace=True)
        for req in ['open','high','low','close','volume']:
            if req not in df.columns:
                df[req] = np.nan
        df = df[['open','high','low','close','volume']].sort_index()
        return df
    except Exception as e:
        print("  > Error normalizing response to DataFrame:", e)
        return None

# ---------------------------
# Fetcher that tries intraday_minute_data / ohlc_data / ticker_data
# ---------------------------
def fetch_intraday_using_available_methods(dhan_client, security_id, exchange_segment, from_date, to_date, interval_minutes=5):
    print(f"Fetching {interval_minutes}-min data for Security ID: {security_id}...")

    # 1) Try intraday_minute_data with several possible kw signatures
    if hasattr(dhan_client, CANDIDATE_INTRA_METHOD):
        func = getattr(dhan_client, CANDIDATE_INTRA_METHOD)
        # common possible kw sets observed across SDKs
        variants = [
            {'security_id': security_id, 'exchange_segment': exchange_segment, 'from_date': from_date, 'to_date': to_date, 'interval': f"{interval_minutes}m"},
            {'security_id': security_id, 'segment': exchange_segment, 'from_date': from_date, 'to_date': to_date, 'interval': f"{interval_minutes}m"},
            {'security_id': security_id, 'exchange_segment': exchange_segment, 'start': from_date, 'end': to_date, 'interval': f"{interval_minutes}m"},
            {'security_id': security_id, 'exchange_segment': exchange_segment, 'start': from_date, 'end': to_date},
            {'security_id': security_id, 'from_date': from_date, 'to_date': to_date, 'interval': f"{interval_minutes}m"},
        ]
        resp = _try_call_various_signatures(func, variants)
        df = _normalize_response_to_df(resp)
        if df is not None:
            print(f"  > intraday_minute_data succeeded (normalized).")
            return df
        else:
            print(f"  > intraday_minute_data returned empty or couldn't be normalized.")

    # 2) Try ohlc_data (some SDKs expose OHLC fetcher)
    if hasattr(dhan_client, CANDIDATE_OHLC_METHOD):
        func = getattr(dhan_client, CANDIDATE_OHLC_METHOD)
        variants = [
            {'security_id': security_id, 'start': from_date, 'end': to_date, 'interval': f"{interval_minutes}m"},
            {'security_id': security_id, 'from_date': from_date, 'to_date': to_date, 'interval': f"{interval_minutes}m"},
            {'security_id': security_id, 'exchange_segment': exchange_segment, 'from_date': from_date, 'to_date': to_date},
        ]
        resp = _try_call_various_signatures(func, variants)
        df = _normalize_response_to_df(resp)
        if df is not None:
            print("  > ohlc_data succeeded (normalized).")
            return df
        else:
            print("  > ohlc_data returned empty or couldn't be normalized.")

    # 3) Try ticker_data (some SDKs return timeseries under ticker)
    if hasattr(dhan_client, CANDIDATE_TICKER):
        func = getattr(dhan_client, CANDIDATE_TICKER)
        variants = [
            {'security_id': security_id, 'from_date': from_date, 'to_date': to_date, 'interval': f"{interval_minutes}m"},
            {'security_id': security_id, 'start': from_date, 'end': to_date},
            {'security_id': security_id},
        ]
        resp = _try_call_various_signatures(func, variants)
        df = _normalize_response_to_df(resp)
        if df is not None:
            print("  > ticker_data succeeded (normalized).")
            return df
        else:
            print("  > ticker_data returned empty or couldn't be normalized.")

    # 4) If option_chain exists and security_id refers to an option, you might need option_chain -> but we'll skip here
    print("  > All client-method attempts failed to return usable data for this security.")
    return None

# ---------------------------
# Analysis helpers (same as prior)
# ---------------------------
def analyze_anomalies(df, data_name):
    if df is None or df.empty:
        print(f"Skipping anomaly detection for {data_name}: no data.")
        return None
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    df['Price_Change'] = df['close'].pct_change() * 100.0
    df['Volume_MA'] = df['volume'].rolling(window=10, min_periods=1).mean()
    df['Volume_Spike'] = df['volume'] / (df['Volume_MA'].replace(0, np.nan))
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.fillna(0, inplace=True)
    try:
        model = IsolationForest(contamination=0.05, random_state=42)
        X = df[['Price_Change', 'Volume_Spike']].astype(float).fillna(0.0)
        df['Anomaly'] = model.fit_predict(X)
        print(f"  > Anomaly detection complete. {int((df['Anomaly']==-1).sum())} anomalies flagged.")
    except Exception as e:
        print("  > IsolationForest failed:", e)
        df['Anomaly'] = 0
    return df

def analyze_suspicious_options(options_df_list):
    if not options_df_list:
        print("No options data available to analyze.")
        return None
    try:
        combined = pd.concat(options_df_list)
    except Exception as e:
        print("  > concat failed for options list:", e)
        return None
    combined.index = pd.to_datetime(combined.index, errors='coerce')
    combined = combined.dropna(subset=['close'])
    try:
        morning = combined.between_time('09:15', '12:30')
    except Exception:
        morning = combined
    put_volume_by_time = morning.groupby(morning.index)['volume'].sum()
    if put_volume_by_time.empty:
        print("No aggregated PUT option volume found for the morning session.")
        return None
    mean_v = put_volume_by_time.mean()
    std_v = put_volume_by_time.std()
    threshold = mean_v + 3 * (std_v if not np.isnan(std_v) else 0.0)
    suspicious = put_volume_by_time[put_volume_by_time > threshold]
    print("\n--- Suspicious Options Activity Report ---")
    print(f"Average 5-min Aggregated PUT Volume: {mean_v:,.0f}")
    print(f"Anomaly Threshold (Mean + 3 StdDev): {threshold:,.0f}")
    print(f"Found {len(suspicious)} suspicious intervals.")
    return suspicious

def plot_full_analysis(stock_df, futures_df, suspicious_options, stock_name, target_date, output_dir="."):
    if stock_df is None or stock_df.empty:
        print("Cannot create plot: Spot data is missing.")
        return None
    stock_df.index = pd.to_datetime(stock_df.index)
    day_mask = stock_df.index.date == pd.to_datetime(target_date).date()
    df_day = stock_df.loc[day_mask]
    if df_day.empty:
        print("No spot rows for specified date.")
        return None
    fig, (ax1, ax2, ax3) = plt.subplots(3,1, figsize=(18,12), sharex=True, gridspec_kw={'height_ratios':[3,1,1]})
    fig.suptitle(f'Programmatic Analysis for {stock_name} - {target_date}', fontsize=16)
    ax1.plot(df_day.index, df_day['close'], label='Spot Price', linewidth=1.2)
    anomalies = df_day[df_day['Anomaly']==-1]
    if not anomalies.empty:
        ax1.scatter(anomalies.index, anomalies['close'], color='red', s=70, label='Spot Anomaly', zorder=5)
    if suspicious_options is not None and not suspicious_options.empty:
        for ts in suspicious_options.index:
            ts = pd.to_datetime(ts)
            ax1.axvspan(ts, ts + pd.Timedelta(minutes=INTERVAL_MINUTES), color='purple', alpha=0.25)
    ax1.set_ylabel('Price')
    ax1.legend()
    ax1.grid(True, linestyle='--', linewidth=0.4)
    ax2.bar(df_day.index, df_day['volume'], width=pd.Timedelta(minutes=4), align='center', alpha=0.7)
    ax2.set_ylabel('Spot Volume')
    ax2.grid(True, linestyle='--', linewidth=0.4)
    if futures_df is not None:
        futures_df.index = pd.to_datetime(futures_df.index)
        fut_day = futures_df[futures_df.index.date == pd.to_datetime(target_date).date()]
        if not fut_day.empty:
            ax3.bar(fut_day.index, fut_day['volume'], width=pd.Timedelta(minutes=4), align='center', alpha=0.7, color='darkorange')
    ax3.set_ylabel('Futures Volume')
    ax3.set_xlabel('Time')
    ax3.grid(True, linestyle='--', linewidth=0.4)
    plt.tight_layout(rect=[0,0.03,1,0.95])
    output_filename = os.path.join(output_dir, f'{stock_name}_Programmatic_Analysis_{target_date}.png')
    plt.savefig(output_filename, dpi=150)
    plt.close(fig)
    print(f"Analysis complete. Chart saved as '{output_filename}'")
    return output_filename

# ---------------------------
# Main
# ---------------------------
def main():
    if DHAN_CLIENT_ID in (None, "", "YOUR_CLIENT_ID_HERE") or DHAN_ACCESS_TOKEN in (None, "", "YOUR_ACCESS_TOKEN_HERE"):
        print("ERROR: Please set DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN in the script.")
        return
    if dhanhq is None:
        print("ERROR: dhanhq SDK not installed/available. Install it or adapt to REST.")
        return

    dhan = dhanhq(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)
    print("Dhan client created. Inspecting available methods (sample):")
    client_methods = [m for m in dir(dhan) if not m.startswith("_")]
    print(client_methods[:120])

    # Fetch spot
    spot_df = fetch_intraday_using_available_methods(dhan,
                                                    INSTRUMENTS['spot']['security_id'],
                                                    INSTRUMENTS['spot']['exchange_segment'],
                                                    TARGET_DATE, TARGET_DATE,
                                                    interval_minutes=INTERVAL_MINUTES)
    time.sleep(SLEEP_BETWEEN_CALLS)

    # Fetch futures
    futures_df = fetch_intraday_using_available_methods(dhan,
                                                      INSTRUMENTS['futures']['security_id'],
                                                      INSTRUMENTS['futures']['exchange_segment'],
                                                      TARGET_DATE, TARGET_DATE,
                                                      interval_minutes=INTERVAL_MINUTES)
    time.sleep(SLEEP_BETWEEN_CALLS)

    options_df_list = []
    for opt in INSTRUMENTS['options']:
        df = fetch_intraday_using_available_methods(dhan,
                                                   opt['security_id'],
                                                   'NSE_FNO',
                                                   TARGET_DATE, TARGET_DATE,
                                                   interval_minutes=INTERVAL_MINUTES)
        if df is not None:
            options_df_list.append(df)
        time.sleep(SLEEP_BETWEEN_CALLS)

    processed_spot = analyze_anomalies(spot_df, "Spot") if spot_df is not None else None
    suspicious_options = analyze_suspicious_options(options_df_list)

    out = plot_full_analysis(processed_spot, futures_df, suspicious_options, STOCK_NAME, TARGET_DATE)
    if out:
        print("Saved report to:", out)
    else:
        print("No report saved (insufficient data).")
        # Helpful next-step hints
        print("\nHINTS:")
        print(" - If spot/futures returned empty, check the security IDs (use fetch_security_list or option_chain to verify).")
        print(" - You can print sample of client methods above and share them if you want me to specialise calls.")
        print(" - If API rate limits/errors occur, try smaller date ranges or check your access token / account permissions.")

if __name__ == "__main__":
    main()
