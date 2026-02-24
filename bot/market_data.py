# ─────────────────────────────────────────────
#  market_data.py  —  Tickers, FX, Weather
# ─────────────────────────────────────────────

import requests
from config import (
    TICKER_SYMBOLS, CURRENCY_PAIRS,
    WEATHER_LAT, WEATHER_LON, WEATHER_CITY
)

# ── Tickers ───────────────────────────────────

def fetch_tickers() -> list[dict]:
    """
    Fetches market data for each ticker in config using Yahoo Finance.
    Returns list of dicts with label, value, change, direction.
    """
    results = []
    for label, symbol in TICKER_SYMBOLS:
        if symbol is None:
            # CETES placeholder — you can wire Banxico API here later
            results.append({
                "label":     label,
                "value":     "—",
                "change":    "",
                "direction": "flat",
            })
            continue
        try:
            url  = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
            headers = {"User-Agent": "Mozilla/5.0"}
            data = requests.get(url, headers=headers, timeout=8).json()
            meta = data["chart"]["result"][0]["meta"]

            price     = meta.get("regularMarketPrice", 0)
            prev      = meta.get("chartPreviousClose", price)
            pct_chg   = ((price - prev) / prev * 100) if prev else 0
            direction = "up" if pct_chg >= 0 else "down"

            # Format value
            if "MXN" in label or "IPC" in label:
                val_str = f"{price:,.2f}"
            elif label == "S&P 500":
                val_str = f"{price:,.0f}"
            elif "Oil" in label:
                val_str = f"${price:.1f}"
            else:
                val_str = f"{price:.4f}"

            chg_str = f"{'▲' if direction == 'up' else '▼'} {abs(pct_chg):.1f}%"

            results.append({
                "label":     label,
                "value":     val_str,
                "change":    chg_str,
                "direction": direction,
            })
        except Exception as e:
            print(f"  [market] Failed {label}: {e}")
            results.append({
                "label":     label,
                "value":     "—",
                "change":    "",
                "direction": "flat",
            })

    return results


# ── Currency table ────────────────────────────

def fetch_currency_table() -> list[dict]:
    """
    Fetches MXN vs each currency in CURRENCY_PAIRS.
    Returns list of dicts per pair.
    """
    rows = []
    for currency in CURRENCY_PAIRS:
        symbol = f"MXN{currency}=X" if currency != "USD" else "MXN=X"
        try:
            url     = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
            headers = {"User-Agent": "Mozilla/5.0"}
            data    = requests.get(url, headers=headers, timeout=8).json()
            result  = data["chart"]["result"][0]
            meta    = result["meta"]
            closes  = result["indicators"]["quote"][0]["close"]
            closes  = [c for c in closes if c is not None]

            rate      = meta.get("regularMarketPrice", 0)
            prev_day  = closes[-2] if len(closes) >= 2 else rate
            prev_week = closes[0]  if len(closes) >= 5 else rate

            chg_1d = ((rate - prev_day)  / prev_day  * 100) if prev_day  else 0
            chg_1w = ((rate - prev_week) / prev_week * 100) if prev_week else 0

            def fmt_chg(val):
                arrow = "▲" if val >= 0 else "▼"
                cls   = "chg-up" if val >= 0 else ("chg-down" if val < 0 else "chg-flat")
                return {"text": f"{arrow} {abs(val):.2f}%", "cls": cls}

            rows.append({
                "pair":   f"MXN / {currency}",
                "rate":   f"{rate:.4f}",
                "chg_1d": fmt_chg(chg_1d),
                "chg_1w": fmt_chg(chg_1w),
            })
        except Exception as e:
            print(f"  [currency] Failed MXN/{currency}: {e}")
            rows.append({
                "pair":   f"MXN / {currency}",
                "rate":   "—",
                "chg_1d": {"text": "—", "cls": "chg-flat"},
                "chg_1w": {"text": "—", "cls": "chg-flat"},
            })
    return rows


# ── Weather ───────────────────────────────────

def fetch_weather() -> dict:
    """
    Fetches current weather from Open-Meteo (no API key needed).
    """
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={WEATHER_LAT}&longitude={WEATHER_LON}"
            f"&current=temperature_2m,relative_humidity_2m,weather_code"
            f"&daily=temperature_2m_max,temperature_2m_min"
            f"&timezone=America/Mexico_City&forecast_days=1"
        )
        data    = requests.get(url, timeout=8).json()
        current = data["current"]
        daily   = data["daily"]

        temp     = round(current["temperature_2m"])
        humidity = current["relative_humidity_2m"]
        code     = current["weather_code"]
        temp_max = round(daily["temperature_2m_max"][0])
        temp_min = round(daily["temperature_2m_min"][0])
        desc     = _weather_description(code)

        return {
            "city":     WEATHER_CITY,
            "temp":     f"{temp}°C",
            "high_low": f"{temp_max}°C / {temp_min}°C",
            "humidity": f"Humidity {humidity}%",
            "desc":     desc,
        }
    except Exception as e:
        print(f"  [weather] Failed: {e}")
        return {
            "city":     WEATHER_CITY,
            "temp":     "—",
            "high_low": "—",
            "humidity": "—",
            "desc":     "Weather unavailable",
        }


def _weather_description(code: int) -> str:
    if code == 0:               return "Clear skies"
    if code in (1, 2, 3):       return "Partly cloudy"
    if code in (45, 48):        return "Foggy"
    if code in (51, 53, 55):    return "Light drizzle"
    if code in (61, 63, 65):    return "Rain"
    if code in (71, 73, 75):    return "Snow"
    if code in (80, 81, 82):    return "Rain showers"
    if code in (95, 96, 99):    return "Thunderstorms"
    return "Mixed conditions"
