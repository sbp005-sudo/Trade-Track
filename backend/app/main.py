from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.portfolio import router as portfolio_router
from app.routes.stocks import router as stocks_router
from app.routes.transactions import router as transactions_router
from app.routes.watchlist import router as watchlist_router


app = FastAPI(
    title="TradeTrack API",
    description="Backend API for the TradeTrack paper trading platform",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(stocks_router)
app.include_router(watchlist_router)
app.include_router(portfolio_router)
app.include_router(transactions_router)


@app.get("/")
def root():
    return {
        "message": "TradeTrack API is running!"
    }