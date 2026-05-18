# Stock Snapshot

Daily JSON snapshots for **RKLB** and **APLD**, auto-generated at 7 AM ET on weekdays via GitHub Actions.

## What it does

- Pulls price data, technicals, analyst targets, and news via `yfinance`
- Calculates flags: volume divergence warnings, proximity to 52-week high, high beta
- Saves clean JSON files to `/snapshots/`
- Commits and pushes automatically

## Setup

### 1. Fork / clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/stock-snapshot.git
cd stock-snapshot
```

### 2. Add the GitHub Secret

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|------|-------|
| `GH_TOKEN` | A GitHub Personal Access Token with `repo` (read + write) scope |

To create a PAT: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token. Select `repo` scope.

### 3. Enable Actions

Go to the **Actions** tab in your repo and enable workflows if prompted.

The workflow runs automatically at 11:00 UTC (7 AM EDT in summer / 6 AM EST in winter — always pre-market) Monday–Friday. You can also trigger it manually from the Actions tab using "Run workflow."

### 4. Run locally (optional)

```bash
pip install -r requirements.txt
python snapshot.py
```

For local git push to work, make sure you have git credentials configured (SSH key or HTTPS with stored credentials).

---

## Reading the JSON

Each file follows this structure:

```json
{
  "ticker": "RKLB",
  "generated_at": "2026-05-17 07:00 ET",
  "price_data": {
    "current_price": 24.77,
    "open": 24.10,
    "day_high": 25.30,
    "day_low": 23.90,
    "volume": 8200000,
    "avg_volume_30d": 9400000,
    "52w_high": 28.45,
    "52w_low": 4.12,
    "market_cap": 11000000000,
    "ps_ratio": 22.4,
    "analyst_target_mean": 31.00,
    "ma_50d": 21.80,
    "ma_200d": 15.60,
    "beta": 2.4
  },
  "technicals": {
    "vs_ma50": "above",
    "vs_ma50_pct": 13.62,
    "vs_ma200": "above",
    "vs_ma200_pct": 58.97,
    "dist_from_52w_high_pct": -12.93,
    "dist_from_52w_low_pct": 501.70,
    "change_5d_pct": 8.2,
    "change_20d_pct": 19.4,
    "volume_ratio": 0.87
  },
  "flags": {
    "volume_divergence_warning": false,
    "near_52w_high_warning": false,
    "high_beta_warning": true,
    "analyst_upside": 25.05
  },
  "news": [
    {
      "headline": "Rocket Lab wins NASA contract...",
      "source": "Reuters",
      "timestamp": "2026-05-16 14:32 ET"
    }
  ]
}
```

**Key fields to check each morning:**

| Field | What it means |
|-------|---------------|
| `change_5d_pct` | Price momentum over the past week |
| `volume_ratio` | Today's volume vs 30-day average. Below 1.0 = low conviction |
| `volume_divergence_warning` | Price up 5%+ on below-average volume — possible weak breakout |
| `near_52w_high_warning` | Within 5% of the 52-week high — potential resistance |
| `high_beta_warning` | Beta above 2.0 — moves amplify market swings |
| `analyst_upside` | % gap between current price and analyst mean target |
| `dist_from_52w_high_pct` | Negative = how far below the 52w high (e.g. -13% means 13% below) |

---

## Pasting into Grok for analysis

Open `snapshots/RKLB_snapshot.json`, copy the contents, and use this prompt:

```
Here is a stock snapshot JSON for RKLB.
Based on this data suggest entry points,
stop loss, and price targets with risk management.
Flag any warnings in the data.

[paste JSON here]
```

You can paste both ticker JSONs in one message for a comparative view:

```
Here are morning snapshots for RKLB and APLD.
Compare momentum, volume conviction, and risk.
Which has a stronger setup today and why?

RKLB: [paste]
APLD: [paste]
```
