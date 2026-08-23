from decimal import Decimal

from pydantic import BaseModel


class WatchlistRequest(BaseModel):
    symbol: str


class TradeRequest(BaseModel):
    symbol: str
    shares: Decimal