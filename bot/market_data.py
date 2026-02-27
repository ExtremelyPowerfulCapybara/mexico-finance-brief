# ─────────────────────────────────────────────
#  market_data.py  —  Tickers, FX, Weather
# ─────────────────────────────────────────────

import os
import requests
from config import (
    TICKER_SYMBOLS, CURRENCY_PAIRS,
    WEATHER_LAT, WEATHER_LON, WEATHER_CITY
)

BANXICO_TOKEN  = os.environ.get("BANXICO_API_KEY", "")
CETES_SERIES   = "SF43936"   # CETES 28 días tasa de rendimiento


# ── Banxico CETES ─────────────────────────────

def fetch_cetes() -> dict:
    """
    Fetches the latest CETES 28D rate from Banxico SIE API.
    Returns a ticker dict. Falls back to "—" if token missing or call fails.
    """
    if not BANXICO_TOKEN:
        return {"label": "CETES 28D", "value": "—", "change": "", "direction": "flat"}
    try:
        url     = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{CETES_SERIES}/datos/oportuno"
        headers = {"Bmx-Token": BANXICO_TOKEN}
        data    = requests.get(url, headers=headers, timeout=8).json()
        datos   = data["bmx"]["series"][0]["datos"]

        # Latest and previous observation
        latest   = float(datos[-1]["dato"])
        previous = float(datos[-2]["dato"]) if len(datos) >= 2 else latest
        chg      = latest - previous
        direction = "up" if chg >= 0 else "down"
        chg_str   = f"{'▲' if chg >= 0 else '▼'} {abs(chg):.2f}pp"

        return {
            "label":     "CETES 28D",
            "value":     f"{latest:.2f}%",
            "change":    chg_str,
            "direction": direction,
        }
    except Exception as e:
        print(f"  [market] CETES fetch failed: {e}")
        return {"label": "CETES 28D", "value": "—", "change": "", "direction": "flat"}


# ── Tickers ───────────────────────────────────

def fetch_tickers() -> list[dict]:
    """
    Fetches market data for each ticker in config using Yahoo Finance.
    CETES 28D is fetched from Banxico SIE API.
    Returns list of dicts with label, value, change, direction.
    """
    results = []
    for label, symbol in TICKER_SYMBOLS:
     if symbol is None:
        results.append({"label": label, "value": "—", "change": "", "direction": "flat"})
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

            if "IBEX" in label or "DAX" in label:
                val_str = f"{price:,.2f}"
            elif label == "S&P 500":
                val_str = f"{price:,.0f}"
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

def _fetch_yahoo_rate(symbol: str) -> tuple[float, float, float] | None:
    """
    Returns (current_rate, prev_day, prev_week) for a Yahoo Finance symbol.
    Returns None on failure.
    """
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
        return rate, prev_day, prev_week
    except Exception as e:
        print(f"  [currency] Yahoo fetch failed for {symbol}: {e}")
        return None


def fetch_currency_table() -> list[dict]:
    rows = []
    pairs = {
        "USD": "EURUSD=X",
        "GBP": "EURGBP=X",
        "CHF": "EURCHF=X",
        "JPY": "EURJPY=X",
    }
    for currency, symbol in pairs.items():
        try:
            result = _fetch_yahoo_rate(symbol)
            if not result:
                raise ValueError(f"No data for {symbol}")
            rate, prev_day, prev_week = result

            chg_1d = ((rate - prev_day)  / prev_day  * 100) if prev_day  else 0
            chg_1w = ((rate - prev_week) / prev_week * 100) if prev_week else 0

            def fmt_chg(val):
                arrow = "▲" if val >= 0 else "▼"
                cls   = "chg-up" if val >= 0 else ("chg-down" if val < 0 else "chg-flat")
                return {"text": f"{arrow} {abs(val):.2f}%", "cls": cls}

            rows.append({
                "pair":   f"EUR / {currency}",
                "rate":   f"{rate:.4f}",
                "chg_1d": fmt_chg(chg_1d),
                "chg_1w": fmt_chg(chg_1w),
            })
        except Exception as e:
            print(f"  [currency] Failed EUR/{currency}: {e}")
            rows.append({
                "pair":   f"EUR / {currency}",
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
            f"&timezone=Europe/Madrid&forecast_days=1"
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
            "humidity": f"Humedad {humidity}%",
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
    if code == 0:               return "Cielo despejado"
    if code in (1, 2, 3):       return "Parcialmente nublado"
    if code in (45, 48):        return "Niebla"
    if code in (51, 53, 55):    return "Llovizna"
    if code in (61, 63, 65):    return "Lluvia"
    if code in (71, 73, 75):    return "Nieve"
    if code in (80, 81, 82):    return "Chubascos"
    if code in (95, 96, 99):    return "Tormenta"
    return "Condiciones variables"
