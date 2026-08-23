import os

import requests
from dotenv import load_dotenv
from fastapi import HTTPException
from psycopg.types.json import Jsonb

from app.database import get_connection


load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")


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

    print(f"No cache found for {symbol}. Calling Alpha Vantage.")

    url = "https://www.alphavantage.co/query"

    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

    except requests.RequestException:
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to market data provider"
        )

    time_series = data.get("Time Series (Daily)")

    if not time_series:
        print("ALPHA VANTAGE ERROR:", data)

        raise HTTPException(
            status_code=502,
            detail="Market data provider did not return historical data"
        )

    history = []

    for date, values in time_series.items():
        history.append({
            "date": date,
            "open": float(values["1. open"]),
            "high": float(values["2. high"]),
            "low": float(values["3. low"]),
            "close": float(values["4. close"]),
            "volume": int(values["5. volume"])
        })

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
def test_successful_buy():
    mock_market_data = {
        "quote": {
            "price": 100.00
        }
    }

    mock_cursor = MagicMock()

    # First fetchone() = portfolio cash
    # Second fetchone() = existing holding (None means we don't own AAPL yet)
    mock_cursor.fetchone.side_effect = [
        {
            "cash": Decimal("1000.00")
        },
        None
    ]

    mock_connection = MagicMock()
    mock_connection.__enter__.return_value = mock_connection
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    with patch(
        "app.routes.portfolio.get_market_data",
        return_value=mock_market_data
    ), patch(
        "app.routes.portfolio.get_connection",
        return_value=mock_connection
    ):
        response = client.post(
            "/portfolio/buy",
            json={
                "symbol": "AAPL",
                "shares": 2
            }
        )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Purchase successful"
    assert data["symbol"] == "AAPL"
    assert data["shares"] == 2
    assert data["price"] == 100.0
    assert data["total_cost"] == 200.0

def test_successful_sell():
    mock_market_data = {
        "quote": {
            "price": 100.00
        }
    }

    mock_cursor = MagicMock()

    # Pretend we currently own 5 shares
    mock_cursor.fetchone.return_value = {
        "shares": Decimal("5")
    }

    mock_connection = MagicMock()
    mock_connection.__enter__.return_value = mock_connection
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    with patch(
        "app.routes.portfolio.get_market_data",
        return_value=mock_market_data
    ), patch(
        "app.routes.portfolio.get_connection",
        return_value=mock_connection
    ):
        response = client.post(
            "/portfolio/sell",
            json={
                "symbol": "AAPL",
                "shares": 2
            }
        )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Sale successful"
    assert data["symbol"] == "AAPL"
    assert data["shares"] == 2
    assert data["price"] == 100.0
    assert data["sale_value"] == 200.0