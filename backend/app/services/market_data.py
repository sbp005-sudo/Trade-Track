import os

import requests
from dotenv import load_dotenv
from fastapi import HTTPException
from psycopg.types.json import Jsonb

from app.database import get_connection


load_dotenv()

TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")


def get_cached_market_data(symbol):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT data
                FROM market_cache
                WHERE symbol = %s
                AND fetched_at > NOW() - INTERVAL '24 hours'
                """,
                (symbol,)
            )

            result = cursor.fetchone()

    if result:
        return result["data"]

    return None


def save_market_data_to_cache(symbol, data):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO market_cache (symbol, data, fetched_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (symbol)
                DO UPDATE SET
                    data = EXCLUDED.data,
                    fetched_at = CURRENT_TIMESTAMP
                """,
                (symbol, Jsonb(data))
            )


def get_market_data(symbol):
    symbol = symbol.strip().upper()

    # Check PostgreSQL cache first
    cached_data = get_cached_market_data(symbol)

    if cached_data:
        print(f"Returning cached data for {symbol}")
        return cached_data

    print(f"No cache found for {symbol}. Calling Twelve Data.")

    if not TWELVE_DATA_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Twelve Data API key is not configured"
        )

    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": symbol,
        "interval": "1day",
        "outputsize": 100,
        "apikey": TWELVE_DATA_API_KEY,
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()
        data = response.json()

    except requests.RequestException as error:
        print("TWELVE DATA REQUEST ERROR:", error)

        raise HTTPException(
            status_code=502,
            detail="Unable to connect to market data provider"
        )

    values = data.get("values")

    if not values:
        print("TWELVE DATA ERROR:", data)

        message = data.get(
            "message",
            "Market data provider did not return historical data"
        )

        raise HTTPException(
            status_code=502,
            detail=message
        )

    history = []

    for item in values:
        history.append({
            "date": item["datetime"].split(" ")[0],
            "open": float(item["open"]),
            "high": float(item["high"]),
            "low": float(item["low"]),
            "close": float(item["close"]),
            "volume": int(item.get("volume") or 0)
        })

    # Newest date first
    history.sort(
        key=lambda item: item["date"],
        reverse=True
    )

    latest = history[0]

    if len(history) > 1:
        previous = history[1]
        previous_close = previous["close"]
    else:
        previous_close = latest["close"]

    change = latest["close"] - previous_close

    if previous_close != 0:
        change_percent = (
            change / previous_close
        ) * 100
    else:
        change_percent = 0

    result = {
        "symbol": symbol,
        "quote": {
            "price": latest["close"],
            "open": latest["open"],
            "high": latest["high"],
            "low": latest["low"],
            "volume": latest["volume"],
            "latest_trading_day": latest["date"],
            "previous_close": previous_close,
            "change": change,
            "change_percent": change_percent
        },
        "history": history
    }

    save_market_data_to_cache(symbol, result)

    return result