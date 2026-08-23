from fastapi import APIRouter

from app.database import get_connection


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)


@router.get("")
def get_transactions():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, symbol, transaction_type, shares, price, created_at
                FROM transactions
                WHERE portfolio_id = 1
                ORDER BY created_at DESC
            """)

            transactions = cursor.fetchall()

    return transactions