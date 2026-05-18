import yfinance as yf
import json
import subprocess
import os
import sys
from datetime import datetime, date

try:
    import pytz
    ET = pytz.timezone("US/Eastern")
    def now_et():
        return datetime.now(ET).strftime("%Y-%m-%d %H:%M ET")
    def ts_to_et(ts):
        return datetime.fromtimestamp(ts, tz=ET).strftime("%Y-%m-%d %H:%M ET") if ts else None
except ImportError:
    def now_et():
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    def ts_to_et(ts):
        return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M UTC") if ts else None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TICKERS = ["RKLB", "APLD"]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SNAPSHOTS_DIR = os.path.join(SCRIPT_DIR, "snapshots")


def pct(a, b):
    try:
        return round((a - b) / b * 100, 2)
    except (TypeError, ZeroDivisionError):
        return None


def calc_rsi(ticker, period=14):
    try:
        hist = ticker.history(period="3mo")
        if len(hist) < period + 1:
            return None
        delta = hist["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
        avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(float(rsi.iloc[-1]), 1)
    except Exception:
        return None


def get_earnings(ticker):
    try:
        cal = ticker.calendar
        dates = cal.get("Earnings Date", [])
        if not dates:
            return None, None
        next_date = dates[0]
        days_away = (next_date - date.today()).days
        return str(next_date), days_away
    except Exception:
        return None, None


def get_snapshot(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)

    try:
        info = ticker.info
    except Exception as e:
        raise RuntimeError(f"Failed to fetch info for {ticker_symbol}: {e}")

    current_price = (
        info.get("currentPrice")
        or info.get("regularMarketPrice")
        or info.get("previousClose")
    )

    if not current_price:
        raise RuntimeError(f"No price data returned for {ticker_symbol} — ticker may be invalid or delisted")

    ma50         = info.get("fiftyDayAverage")
    ma200        = info.get("twoHundredDayAverage")
    high_52w     = info.get("fiftyTwoWeekHigh")
    low_52w      = info.get("fiftyTwoWeekLow")
    volume       = info.get("regularMarketVolume") or info.get("volume")
    avg_vol_30d  = info.get("averageVolume") or info.get("averageDailyVolume3Month")
    beta         = info.get("beta")
    analyst_target = info.get("targetMeanPrice")

    # Price changes from history
    change_5d = change_20d = None
    try:
        h5 = ticker.history(period="5d")
        if len(h5) >= 2:
            change_5d = pct(current_price, float(h5["Close"].iloc[0]))
    except Exception:
        pass

    try:
        h20 = ticker.history(period="1mo")
        if len(h20) >= 2:
            change_20d = pct(current_price, float(h20["Close"].iloc[0]))
    except Exception:
        pass

    vol_ratio = None
    try:
        if volume and avg_vol_30d:
            vol_ratio = round(volume / avg_vol_30d, 2)
    except (TypeError, ZeroDivisionError):
        pass

    # RSI
    rsi = calc_rsi(ticker)

    # Earnings
    next_earnings_date, days_to_earnings = get_earnings(ticker)

    # Revenue growth: API returns decimal (1.393 = 139.3%)
    rev_growth_raw = info.get("revenueGrowth")
    rev_growth_pct = round(rev_growth_raw * 100, 1) if rev_growth_raw is not None else None

    # Analyst data
    analyst_target_rounded = round(analyst_target, 2) if analyst_target else None
    analyst_upside = pct(analyst_target, current_price) if analyst_target else None
    recommendation = info.get("recommendationKey")
    analyst_count  = info.get("numberOfAnalystOpinions")

    # Short interest
    short_pct_float = info.get("shortPercentOfFloat")
    short_ratio     = info.get("shortRatio")
    if short_pct_float is not None:
        short_pct_float = round(short_pct_float * 100, 1)  # decimal → %

    # Flags
    vol_divergence = False
    if change_5d is not None and vol_ratio is not None:
        vol_divergence = (change_5d >= 5.0) and (vol_ratio < 1.0)

    near_52w_high = False
    if high_52w and current_price:
        near_52w_high = (high_52w - current_price) / high_52w * 100 <= 5.0

    flags = {
        "volume_divergence_warning": vol_divergence,
        "near_52w_high_warning": near_52w_high,
        "high_beta_warning": bool(beta and beta > 2.0),
    }

    # News
    news = []
    try:
        for item in (ticker.news or [])[:5]:
            content = item.get("content", item)
            pub_ts = content.get("pubDate") or item.get("providerPublishTime")
            if isinstance(pub_ts, str):
                readable_ts = pub_ts[:16].replace("T", " ") + " ET"
            elif isinstance(pub_ts, (int, float)):
                readable_ts = ts_to_et(pub_ts)
            else:
                readable_ts = None
            provider = content.get("provider", {})
            news.append({
                "headline": content.get("title") or item.get("title"),
                "source": (
                    provider.get("displayName")
                    if isinstance(provider, dict)
                    else item.get("publisher")
                ),
                "timestamp": readable_ts,
            })
    except Exception as e:
        news = [{"error": str(e)}]

    def ma_dir(price, ma):
        if price is None or ma is None:
            return None
        return "above" if price > ma else "below"

    return {
        "ticker": ticker_symbol,
        "generated_at": now_et(),
        "price_data": {
            "current_price": current_price,
            "open": info.get("regularMarketOpen") or info.get("open"),
            "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
            "day_low": info.get("dayLow") or info.get("regularMarketDayLow"),
            "volume": volume,
            "avg_volume_30d": avg_vol_30d,
            "52w_high": high_52w,
            "52w_low": low_52w,
            "market_cap": info.get("marketCap"),
            "market_cap_b": round(info.get("marketCap") / 1e9, 2) if info.get("marketCap") else None,
            "ps_ratio": round(info.get("priceToSalesTrailing12Months"), 2) if info.get("priceToSalesTrailing12Months") else None,
            "revenue_growth_yoy_pct": rev_growth_pct,
            "analyst_target_mean": analyst_target_rounded,
            "analyst_upside_pct": analyst_upside,
            "analyst_recommendation": recommendation,
            "analyst_count": analyst_count,
            "short_pct_float": short_pct_float,
            "short_ratio": short_ratio,
            "next_earnings_date": next_earnings_date,
            "days_to_earnings": days_to_earnings,
            "ma_50d": ma50,
            "ma_200d": ma200,
            "beta": beta,
        },
        "technicals": {
            "rsi_14": rsi,
            "vs_ma50": ma_dir(current_price, ma50),
            "vs_ma50_pct": pct(current_price, ma50),
            "vs_ma200": ma_dir(current_price, ma200),
            "vs_ma200_pct": pct(current_price, ma200),
            "dist_from_52w_high_pct": pct(current_price, high_52w),
            "dist_from_52w_low_pct": pct(current_price, low_52w),
            "change_5d_pct": change_5d,
            "change_20d_pct": change_20d,
            "volume_ratio": vol_ratio,
        },
        "flags": flags,
        "news": news,
    }


def save_snapshot(snapshot):
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    path = os.path.join(SNAPSHOTS_DIR, f"{snapshot['ticker']}_snapshot.json")
    with open(path, "w") as f:
        json.dump(snapshot, f, indent=2)
    return path


def git_commit_push():
    try:
        result = subprocess.run(
            ["git", "diff", "--quiet", "snapshots/"],
            cwd=SCRIPT_DIR,
            capture_output=True,
        )
        if result.returncode == 0:
            untracked = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard", "snapshots/"],
                cwd=SCRIPT_DIR,
                capture_output=True, text=True,
            )
            if not untracked.stdout.strip():
                print("No changes to commit — skipping git push.")
                return True

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        cmds = [
            ["git", "add", "snapshots/"],
            ["git", "commit", "-m", f"Snapshot update {now}"],
            ["git", "push", "origin", "main"],
        ]
        for cmd in cmds:
            r = subprocess.run(cmd, cwd=SCRIPT_DIR, capture_output=True, text=True)
            if r.returncode != 0:
                print(f"Git error ({' '.join(cmd)}): {r.stderr.strip()}")
                return False
        return True
    except Exception as e:
        print(f"Git commit/push failed: {e}")
        return False


def flag_summary(flags):
    warnings = []
    if flags.get("volume_divergence_warning"):
        warnings.append("volume divergence")
    if flags.get("near_52w_high_warning"):
        warnings.append("near 52w high")
    if flags.get("high_beta_warning"):
        warnings.append("high beta")
    return (" | " + " | ".join(f"⚠️  {w}" for w in warnings)) if warnings else ""


def main():
    results = []
    errors = []

    for symbol in TICKERS:
        try:
            snapshot = get_snapshot(symbol)
            save_snapshot(snapshot)

            p     = snapshot["price_data"]
            t     = snapshot["technicals"]
            flags = snapshot["flags"]

            price_str  = f"${p['current_price']:.2f}"
            change_str = f"{t['change_5d_pct']:+.1f}%" if t["change_5d_pct"] is not None else "N/A"
            vol_str    = f"{t['volume_ratio']:.2f}" if t["volume_ratio"] is not None else "N/A"
            rsi_str    = f"RSI {t['rsi_14']}" if t["rsi_14"] is not None else ""
            earn_str   = f"earnings in {p['days_to_earnings']}d" if p["days_to_earnings"] is not None else ""

            extras = " | ".join(x for x in [rsi_str, earn_str] if x)
            extra_part = f" | {extras}" if extras else ""

            line = f"✅ {symbol:<6} — {price_str:<10} | 5d: {change_str:<8} | Vol ratio: {vol_str}{extra_part}{flag_summary(flags)}"
            results.append(line)

        except Exception as e:
            errors.append(f"❌ {symbol} — ERROR: {e}")

    print()
    for line in results:
        print(line)
    for line in errors:
        print(line)

    if results:
        print("Snapshots saved to /snapshots/")
        pushed = git_commit_push()
        if pushed:
            print("Committed to GitHub ✅")
        else:
            print("Git push failed — snapshots saved locally.")
    print()

    sys.exit(1 if errors and not results else 0)


if __name__ == "__main__":
    main()
