import pandas as pd
import numpy as np
import json

# ── Load data ──────────────────────────────────────────────────────────────────
fg = pd.read_csv('fear_greed_index.csv')
tr = pd.read_csv('historical_data.csv')

# ── Parse & merge ──────────────────────────────────────────────────────────────
tr['date'] = pd.to_datetime(tr['Timestamp IST'], dayfirst=True).dt.date.astype(str)
fg['date'] = fg['date'].astype(str)
merged = tr.merge(fg[['date', 'value', 'classification']], on='date', how='left')
merged = merged[merged['classification'].notna()].copy()
closed_trades = merged[merged['Closed PnL'] != 0].copy()

SENT_ORDER = ['Extreme Fear', 'Fear', 'Neutral', 'Greed', 'Extreme Greed']

# ── 1. PnL by sentiment ────────────────────────────────────────────────────────
pnl_by_sent = closed_trades.groupby('classification').agg(
    total_pnl=('Closed PnL', 'sum'),
    avg_pnl=('Closed PnL', 'mean'),
    median_pnl=('Closed PnL', 'median'),
    trades=('Closed PnL', 'count'),
    win_rate=('Closed PnL', lambda x: (x > 0).mean() * 100)
).reindex(SENT_ORDER)
print("=== PnL by Sentiment ===")
print(pnl_by_sent.round(2))

# ── 2. Long/Short ratio by sentiment ──────────────────────────────────────────
ls = merged[merged['Direction'].isin(['Open Long', 'Open Short'])].copy()
ls_ratio = ls.groupby(['classification', 'Direction']).size().unstack(fill_value=0)
ls_ratio['long_pct'] = ls_ratio['Open Long'] / (ls_ratio['Open Long'] + ls_ratio['Open Short']) * 100
print("\n=== Long/Short Ratio by Sentiment ===")
print(ls_ratio.reindex(SENT_ORDER).round(2))

# ── 3. Volume by sentiment ─────────────────────────────────────────────────────
vol_by_sent = merged.groupby('classification').agg(
    total_volume=('Size USD', 'sum'),
    avg_trade_size=('Size USD', 'mean'),
    num_trades=('Size USD', 'count')
).reindex(SENT_ORDER)
print("\n=== Volume by Sentiment ===")
print(vol_by_sent.round(2))

# ── 4. Account performance ─────────────────────────────────────────────────────
acc_perf = closed_trades.groupby('Account').agg(
    total_pnl=('Closed PnL', 'sum'),
    trades=('Closed PnL', 'count'),
    win_rate=('Closed PnL', lambda x: (x > 0).mean() * 100)
).sort_values('total_pnl', ascending=False)
print("\n=== Top 5 Accounts ===")
print(acc_perf.head(5).round(2))
print("\n=== Bottom 5 Accounts ===")
print(acc_perf.tail(5).round(2))

# ── 5. Top coin performance ────────────────────────────────────────────────────
coin_pnl = closed_trades.groupby('Coin').agg(
    total_pnl=('Closed PnL', 'sum'),
    trades=('Closed PnL', 'count')
).sort_values('total_pnl', ascending=False).head(15)
print("\n=== Top 15 Coins by PnL ===")
print(coin_pnl.round(2))

# ── 6. Save processed analysis ─────────────────────────────────────────────────
output = {
    'pnl_by_sentiment': pnl_by_sent.round(2).to_dict(),
    'ls_ratio': ls_ratio.reindex(SENT_ORDER).round(2).to_dict(),
    'vol_by_sentiment': vol_by_sent.round(2).to_dict(),
    'account_performance': acc_perf.round(2).to_dict(),
    'top_coins': coin_pnl.round(2).to_dict()
}
with open('analysis_output.json', 'w') as f:
    json.dump(output, f, indent=2)
print("\n✓ Saved analysis_output.json")
