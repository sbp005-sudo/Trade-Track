import psycopg
from fastapi import APIRouter, HTTPException

from app.database import get_connection
from app.models.requests import WatchlistRequest


router = APIRouter(
    prefix="/watchlist",
    tags=["Watchlist"]
)


@router.get("")
def get_watchlist():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, symbol, added_at
                FROM watchlist
                ORDER BY added_at DESC
            """)

            watchlist = cursor.fetchall()

    return watchlist


@router.post("")
def add_to_watchlist(item: WatchlistRequest):
    symbol = item.symbol.strip().upper()

    if not symbol:
        raise HTTPException(
            status_code=400,
            detail="Stock symbol is required"
        )

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO watchlist (symbol)
                    VALUES (%s)
                    RETURNING id, symbol, added_at
                """, (symbol,))

                new_item = cursor.fetchone()

        return new_item

    except psycopg.errors.UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail="Stock is already in watchlist"
        )


@router.delete("/{symbol}")
def remove_from_watchlist(symbol: str):
    symbol = symbol.strip().upper()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM watchlist
                WHERE symbol = %s
                RETURNING id, symbol
            """, (symbol,))

            deleted_item = cursor.fetchone()

    if not deleted_item:
        raise HTTPException(
            status_code=404,
            detail="Stock not found in watchlist"
        )

    return {
        "message": f"{symbol} removed from watchlist"
    }