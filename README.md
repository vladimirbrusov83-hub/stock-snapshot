# Stock Snapshot

Daily morning briefing for **RKLB** and **APLD** — auto-generated at 11:00 UTC (7 AM EDT) every weekday via GitHub Actions, committed back to this repo, and served as a live dashboard on GitHub Pages.

**100% free. No API keys. No paid services.**

---

## Dashboard

**https://vladimirbrusov83-hub.github.io/stock-snapshot/**

Open this link each morning. It auto-loads the latest snapshot. Each ticker card has a **Copy JSON for Grok** button — one click copies everything, ready to paste.

---

## How it works

```
7 AM ET (weekdays)
  └── GitHub Actions runs snapshot.py
        └── yfinance pulls live data from Yahoo Finance (free, no key)
              └── Saves RKLB_snapshot.json + APLD_snapshot.json to /snapshots/
                    └── Commits + pushes to this repo
                          └── Dashboard at GitHub Pages auto-serves the new files
```

No paid APIs. No external services. No accounts needed beyond GitHub (which you already have).

---

## Free tier confirmation

| Service | Plan | Cost |
|---------|------|------|
| GitHub repo | Public | Free |
| GitHub Actions | Public repo — unlimited minutes | Free |
| GitHub Pages | Public repo | Free |
| Yahoo Finance (via yfinance) | No key required | Free |

---

## What's in each snapshot

### `price_data`

| Field | Description |
|-------|-------------|
| `current_price` | Last closing price |
| `open` | Today's open |
| `day_high` / `day_low` | Today's range |
| `volume` | Today's volume |
| `avg_volume_30d` | 30-day average volume |
| `52w_high` / `52w_low` | 52-week range |
| `market_cap` | Raw market cap (integer) |
| `market_cap_b` | Market cap in billions (e.g. `72.21`) |
| `ps_ratio` | Price-to-sales (trailing 12 months) |
| `revenue_growth_yoy_pct` | Year-over-year revenue growth % |
| `analyst_target_mean` | Mean analyst price target |
| `analyst_upside_pct` | % gap between current price and analyst target |
| `analyst_recommendation` | Consensus label (e.g. `buy`, `strong_buy`) |
| `analyst_count` | Number of analysts covering the stock |
| `short_pct_float` | Short interest as % of float |
| `short_ratio` | Days to cover (short ratio) |
| `next_earnings_date` | Date of next earnings report |
| `days_to_earnings` | Calendar days until next earnings |
| `ma_50d` / `ma_200d` | 50-day and 200-day moving averages |
| `beta` | Volatility vs S&P 500 |

### `technicals`

| Field | Description |
|-------|-------------|
| `rsi_14` | RSI (14-period). Above 70 = overbought, below 30 = oversold |
| `vs_ma50` | `"above"` or `"below"` the 50-day MA |
| `vs_ma50_pct` | % distance from the 50-day MA |
| `vs_ma200` | `"above"` or `"below"` the 200-day MA |
| `vs_ma200_pct` | % distance from the 200-day MA |
| `dist_from_52w_high_pct` | % below the 52-week high (negative = below) |
| `dist_from_52w_low_pct` | % above the 52-week low |
| `change_5d_pct` | Price change over past 5 trading days |
| `change_20d_pct` | Price change over past 20 trading days (~1 month) |
| `volume_ratio` | Today's volume ÷ 30-day average. Below 1.0 = low conviction |

### `flags`

| Field | Fires when… |
|-------|------------|
| `volume_divergence_warning` | Price up 5%+ in 5 days AND volume below 30-day average |
| `near_52w_high_warning` | Price within 5% of the 52-week high |
| `high_beta_warning` | Beta above 2.0 |

### `news`

5 most recent headlines with source and timestamp.

---

## Pasting into Grok

Click **Copy JSON for Grok** on the dashboard, then use this prompt:

```
Here is a morning stock snapshot for RKLB.
Based on this data suggest entry points, stop loss, and price targets with risk management.
Flag any warnings in the data.

[paste JSON here]
```

For a side-by-side comparison, copy both and paste together:

```
Here are morning snapshots for RKLB and APLD.
Compare momentum, volume conviction, and risk.
Which has a stronger setup today and why?

RKLB: [paste]
APLD: [paste]
```

---

## Setup (already done — for reference)

### GitHub Secret required

Go to repo → **Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|------|-------|
| `GH_TOKEN` | GitHub Personal Access Token with `repo` + `workflow` scopes |

The workflow uses this token to commit the updated JSON files back to the repo after each run.

### Schedule

Runs automatically at **11:00 UTC** (7 AM EDT in summer / 6 AM EST in winter) Monday–Friday.
Can also be triggered manually: Actions tab → Daily Stock Snapshot → Run workflow.

### Run locally

```bash
pip install -r requirements.txt
python snapshot.py
```

Saves JSON to `/snapshots/` and commits + pushes if the repo is configured.
