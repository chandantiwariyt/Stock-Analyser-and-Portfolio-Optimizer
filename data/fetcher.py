import pandas as pd
import yfinance as yf

INDIAN_SUFFIXES = (".NS", ".BO")
MARKET_SUFFIX = {
    "India (NSE)": ".NS",
    "India (BSE)": ".BO",
    "United States": "",
}


def _history_for_symbol(symbol: str, period: str, interval: str, auto_adjust: bool = True) -> pd.DataFrame:
    return yf.download(
        symbol,
        period=period,
        interval=interval,
        auto_adjust=auto_adjust,
        progress=False,
        threads=False,
    )


def _candidate_symbols(symbol: str, market: str | None = None) -> list[str]:
    cleaned = symbol.strip().upper()
    if not cleaned:
        return []

    if market in MARKET_SUFFIX:
        suffix = MARKET_SUFFIX[market]
        if suffix and not cleaned.endswith(INDIAN_SUFFIXES):
            return [f"{cleaned}{suffix}"]
        return [cleaned]

    if cleaned.endswith(INDIAN_SUFFIXES):
        return [cleaned]

    return [cleaned, f"{cleaned}.NS", f"{cleaned}.BO"]


def resolve_ticker(symbol: str, market: str | None = None, period: str = "1mo", interval: str = "1d") -> str:
    for candidate in _candidate_symbols(symbol, market):
        data = _history_for_symbol(candidate, period=period, interval=interval)
        if not data.empty:
            return candidate
    raise ValueError(f"Could not fetch market data for ticker '{symbol}'.")


def _extract_close_series(raw: pd.DataFrame, requested_symbol: str) -> pd.Series:
    if "Close" in raw.columns:
        close = raw["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        series = close.copy()
    else:
        series = raw.iloc[:, 0].copy()

    series.name = requested_symbol
    return series


def fetch_prices(tickers: list[str], period: str = "1y", interval: str = "1mo") -> pd.DataFrame:
    """
    Fetch closing prices for each ticker. Indian symbols can be entered either
    with a suffix like `.NS` / `.BO` or as a bare ticker such as `BHEL`.
    """
    price_series: list[pd.Series] = []
    resolved_symbols: dict[str, str] = {}

    for ticker in tickers:
        resolved = resolve_ticker(ticker, period="3mo", interval="1d")
        raw = _history_for_symbol(resolved, period=period, interval=interval)
        close = _extract_close_series(raw, ticker)
        price_series.append(close)
        resolved_symbols[ticker] = resolved

    prices = pd.concat(price_series, axis=1)
    prices.dropna(how="all", inplace=True)
    prices.attrs["resolved_symbols"] = resolved_symbols
    return prices


def fetch_inr_rate(base_currency: str) -> float:
    currency = (base_currency or "INR").upper()
    if currency == "INR":
        return 1.0

    fx_symbol = f"{currency}INR=X"
    fx_data = _history_for_symbol(fx_symbol, period="5d", interval="1d", auto_adjust=False)
    if fx_data.empty:
        raise ValueError(f"Could not fetch INR conversion rate for currency '{currency}'.")

    fx_close = _extract_close_series(fx_data, fx_symbol).dropna()
    if fx_close.empty:
        raise ValueError(f"INR conversion data is empty for currency '{currency}'.")

    return float(fx_close.iloc[-1])


def fetch_watchlist_prices(entries: list[dict[str, str]]) -> pd.DataFrame:
    """
    Fetch watchlist prices and convert them to INR only when the asset is not
    already quoted in INR.
    """
    rows: list[dict[str, object]] = []

    for entry in entries:
        symbol = entry["symbol"].strip().upper()
        market = entry.get("market")
        resolved = resolve_ticker(symbol, market=market, period="3mo", interval="1d")
        ticker = yf.Ticker(resolved)

        history = ticker.history(period="5d", interval="1d", auto_adjust=False)
        close = history["Close"].dropna() if "Close" in history else pd.Series(dtype=float)
        if close.empty:
            raise ValueError(f"No recent price data found for ticker '{symbol}'.")

        fast_info = getattr(ticker, "fast_info", {}) or {}
        native_currency = (
            fast_info.get("currency")
            or ticker.info.get("currency")
            or ("INR" if resolved.endswith(INDIAN_SUFFIXES) else "USD")
        ).upper()

        fx_rate = fetch_inr_rate(native_currency)
        latest_price = float(close.iloc[-1])
        previous_price = float(close.iloc[-2]) if len(close) > 1 else latest_price

        latest_inr = latest_price * fx_rate
        previous_inr = previous_price * fx_rate
        percent_change = ((latest_price - previous_price) / previous_price * 100) if previous_price else 0.0

        rows.append(
            {
                "Ticker": symbol,
                "Exchange Symbol": resolved,
                "Market": market or ("India" if resolved.endswith(INDIAN_SUFFIXES) else "United States"),
                "Native Price": latest_price,
                "Native Currency": native_currency,
                "INR FX Rate": round(fx_rate, 4),
                "Price (INR)": latest_inr,
                "Prev Close (INR)": previous_inr,
                "Change (%)": percent_change,
            }
        )

    return pd.DataFrame(rows)
