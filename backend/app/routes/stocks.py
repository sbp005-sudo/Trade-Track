from fastapi import APIRouter

from app.services.market_data import get_market_data


router = APIRouter(
    prefix="/stock",
    tags=["Stocks"]
)


@router.get("/{symbol}/history")
def get_stock_history(symbol: str):
    return get_market_data(symbol)