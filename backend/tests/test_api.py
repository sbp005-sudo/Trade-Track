import os
import requests
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from decimal import Decimal

from app.main import app


client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "TradeTrack API is running!"
    }
def test_get_watchlist():
    mock_cursor = MagicMock()

    mock_cursor.fetchall.return_value = [
        {
            "id": 1,
            "symbol": "AAPL",
            "added_at": "2026-08-23T00:00:00"
        },
        {
            "id": 2,
            "symbol": "MSFT",
            "added_at": "2026-08-22T00:00:00"
        }
    ]

    mock_connection = MagicMock()

    mock_connection.__enter__.return_value = mock_connection

    mock_connection.cursor.return_value.__enter__.return_value = (
        mock_cursor
    )

    with patch(
        "app.routes.watchlist.get_connection",
        return_value=mock_connection
    ):
        response = client.get("/watchlist")

    assert response.status_code == 200

    assert response.json() == [
        {
            "id": 1,
            "symbol": "AAPL",
            "added_at": "2026-08-23T00:00:00"
        },
        {
            "id": 2,
            "symbol": "MSFT",
            "added_at": "2026-08-22T00:00:00"
        }
    ]
def test_add_empty_symbol_to_watchlist():
    response = client.post(
        "/watchlist",
        json={
            "symbol": ""
        }
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Stock symbol is required"
    }
load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

url = "https://www.alphavantage.co/query"

params = {
    "function": "TIME_SERIES_DAILY",
    "symbol": "AAPL",
    "apikey": API_KEY
}

response = requests.get(url, params=params)

print("Status:", response.status_code)
print("Response:")
print(response.json())
def test_buy_stock_with_insufficient_cash():
    mock_market_data = {
        "quote": {
            "price": 100.00
        }
    }

    mock_cursor = MagicMock()

    # The fake portfolio only has $50
    mock_cursor.fetchone.return_value = {
        "cash": Decimal("50.00")
    }

    mock_connection = MagicMock()
    mock_connection.__enter__.return_value = mock_connection

    mock_connection.cursor.return_value.__enter__.return_value = (
        mock_cursor
    )

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

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Not enough cash to complete purchase"
    }
def test_sell_more_shares_than_owned():
    mock_market_data = {
        "quote": {
            "price": 100.00
        }
    }

    mock_cursor = MagicMock()

    mock_cursor.fetchone.return_value = {
        "shares": Decimal("2")
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
                "shares": 5
            }
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Not enough shares to sell"
    }
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