from decimal import Decimal

from fastapi import APIRouter, HTTPException

from app.database import get_connection
from app.models.requests import TradeRequest
from app.services.market_data import (
    get_cached_market_data,
    get_market_data,
)


router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"]
)


@router.get("")
def get_portfolio():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT cash
                FROM portfolio
                WHERE id = 1
            """)

            portfolio = cursor.fetchone()

            if not portfolio:
                raise HTTPException(
                    status_code=404,
                    detail="Portfolio not found"
                )

            cash = portfolio["cash"]

            cursor.execute("""
                SELECT symbol, shares, average_price
                FROM holdings
                WHERE portfolio_id = 1
                ORDER BY symbol
            """)

            holdings = cursor.fetchall()

    holdings_data = []
    total_holdings_value = Decimal("0")
    total_unrealized_pnl = Decimal("0")

    for holding in holdings:
        symbol = holding["symbol"]
        shares = holding["shares"]
        average_price = holding["average_price"]

        cached_data = get_cached_market_data(symbol)

        if cached_data:
            current_price = Decimal(
                str(cached_data["quote"]["price"])
            )
        else:
            current_price = average_price

        market_value = current_price * shares
        cost_basis = average_price * shares
        unrealized_pnl = market_value - cost_basis

        total_holdings_value += market_value
        total_unrealized_pnl += unrealized_pnl

        holdings_data.append({
            "symbol": symbol,
            "shares": float(shares),
            "average_price": float(average_price),
            "current_price": float(current_price),
            "market_value": float(market_value),
            "unrealized_pnl": float(unrealized_pnl)
        })

    total_value = cash + total_holdings_value

    return {
        "cash": float(cash),
        "holdings_value": float(total_holdings_value),
        "total_value": float(total_value),
        "unrealized_pnl": float(total_unrealized_pnl),
        "holdings": holdings_data
    }


@router.post("/buy")
def buy_stock(trade: TradeRequest):
    symbol = trade.symbol.strip().upper()
    shares = trade.shares

    if not symbol:
        raise HTTPException(
            status_code=400,
            detail="Stock symbol is required"
        )

    if shares <= 0:
        raise HTTPException(
            status_code=400,
            detail="Shares must be greater than 0"
        )

    market_data = get_market_data(symbol)

    price = Decimal(
        str(market_data["quote"]["price"])
    )

    total_cost = price * shares

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT cash
                FROM portfolio
                WHERE id = 1
                FOR UPDATE
            """)

            portfolio = cursor.fetchone()

            if not portfolio:
                raise HTTPException(
                    status_code=404,
                    detail="Portfolio not found"
                )

            cash = portfolio["cash"]

            if total_cost > cash:
                raise HTTPException(
                    status_code=400,
                    detail="Not enough cash to complete purchase"
                )

            cursor.execute("""
                SELECT shares, average_price
                FROM holdings
                WHERE portfolio_id = 1
                AND symbol = %s
                FOR UPDATE
            """, (symbol,))

            holding = cursor.fetchone()

            if holding:
                old_shares = holding["shares"]
                old_average_price = holding["average_price"]

                new_shares = old_shares + shares

                new_average_price = (
                    (old_shares * old_average_price)
                    + (shares * price)
                ) / new_shares

                cursor.execute("""
                    UPDATE holdings
                    SET shares = %s,
                        average_price = %s
                    WHERE portfolio_id = 1
                    AND symbol = %s
                """, (
                    new_shares,
                    new_average_price,
                    symbol
                ))

            else:
                cursor.execute("""
                    INSERT INTO holdings (
                        portfolio_id,
                        symbol,
                        shares,
                        average_price
                    )
                    VALUES (1, %s, %s, %s)
                """, (
                    symbol,
                    shares,
                    price
                ))

            cursor.execute("""
                UPDATE portfolio
                SET cash = cash - %s
                WHERE id = 1
            """, (total_cost,))

            cursor.execute("""
                INSERT INTO transactions (
                    portfolio_id,
                    symbol,
                    transaction_type,
                    shares,
                    price
                )
                VALUES (1, %s, 'BUY', %s, %s)
            """, (
                symbol,
                shares,
                price
            ))

    return {
        "message": "Purchase successful",
        "symbol": symbol,
        "shares": shares,
        "price": price,
        "total_cost": total_cost
    }


@router.post("/sell")
def sell_stock(trade: TradeRequest):
    symbol = trade.symbol.strip().upper()
    shares = trade.shares

    if not symbol:
        raise HTTPException(
            status_code=400,
            detail="Stock symbol is required"
        )

    if shares <= 0:
        raise HTTPException(
            status_code=400,
            detail="Shares must be greater than 0"
        )

    market_data = get_market_data(symbol)

    price = Decimal(
        str(market_data["quote"]["price"])
    )

    sale_value = price * shares

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT shares
                FROM holdings
                WHERE portfolio_id = 1
                AND symbol = %s
                FOR UPDATE
            """, (symbol,))

            holding = cursor.fetchone()

            if not holding:
                raise HTTPException(
                    status_code=400,
                    detail="You do not own this stock"
                )

            owned_shares = holding["shares"]

            if shares > owned_shares:
                raise HTTPException(
                    status_code=400,
                    detail="Not enough shares to sell"
                )

            remaining_shares = owned_shares - shares

            if remaining_shares == 0:
                cursor.execute("""
                    DELETE FROM holdings
                    WHERE portfolio_id = 1
                    AND symbol = %s
                """, (symbol,))

            else:
                cursor.execute("""
                    UPDATE holdings
                    SET shares = %s
                    WHERE portfolio_id = 1
                    AND symbol = %s
                """, (
                    remaining_shares,
                    symbol
                ))

            cursor.execute("""
                UPDATE portfolio
                SET cash = cash + %s
                WHERE id = 1
            """, (sale_value,))

            cursor.execute("""
                INSERT INTO transactions (
                    portfolio_id,
                    symbol,
                    transaction_type,
                    shares,
                    price
                )
                VALUES (1, %s, 'SELL', %s, %s)
            """, (
                symbol,
                shares,
                price
            ))

    return {
        "message": "Sale successful",
        "symbol": symbol,
        "shares": shares,
        "price": price,
        "sale_value": sale_value
    }