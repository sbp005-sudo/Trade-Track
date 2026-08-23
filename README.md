# TradeTrack

TradeTrack is a full-stack paper trading application that lets users search stocks, view historical market data, create a persistent watchlist, and simulate buying and selling stocks with a virtual portfolio.

## Features

- Search for stocks by ticker symbol
- View historical stock price charts
- View open, high, low, close, volume, and daily price change
- Add and remove stocks from a persistent watchlist
- Buy and sell stocks using virtual cash
- Support fractional shares
- Track portfolio value, cash, and holdings
- Calculate unrealized profit and loss
- View a history of buy and sell transactions
- Cache market data in PostgreSQL to reduce external API requests
- Automated backend tests for API and trading logic

## Tech Stack

**Frontend:** React, JavaScript, Vite, Recharts, CSS

**Backend:** Python, FastAPI, PostgreSQL, Psycopg

**Market Data:** Alpha Vantage API

**Testing:** pytest, FastAPI TestClient, unittest.mock

## Project Structure

```text
tradetrack/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   └── requests.py
│   │   ├── routes/
│   │   │   ├── portfolio.py
│   │   │   ├── stocks.py
│   │   │   ├── transactions.py
│   │   │   └── watchlist.py
│   │   └── services/
│   │       └── market_data.py
│   ├── tests/
│   │   └── test_api.py
│   └── requirements.txt
│
└── frontend/
    └── src/
        ├── App.jsx
        ├── App.css
        ├── index.css
        └── main.jsx
```

## Backend Architecture

The FastAPI backend is organized into separate layers:

- **Routes** handle API requests for stocks, watchlists, portfolios, and transactions.
- **Services** handle external market-data retrieval and caching.
- **Models** define request schemas using Pydantic.
- **Database utilities** manage PostgreSQL connections.

Market data is cached in PostgreSQL to reduce unnecessary calls to the external stock-data API.

## Running TradeTrack Locally

### Backend

Navigate to the backend:

```bash
cd backend
```

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file inside the `backend` folder with:

```env
ALPHA_VANTAGE_API_KEY=your_api_key_here
DATABASE_URL=dbname=tradetrack
```

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

The backend runs at:

```text
http://127.0.0.1:8000
```

Interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

### Frontend

Open another terminal and navigate to the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend runs at:

```text
http://localhost:5173
```

## Testing

Backend tests use pytest and FastAPI's TestClient.

Run the test suite from the `backend` directory:

```bash
python -m pytest -v
```

Tests currently cover API health, watchlist behavior, invalid trades, insufficient cash, selling more shares than owned, and successful buy and sell operations.

Database and market-data dependencies are mocked where appropriate so tests do not modify the real portfolio.

## API Endpoints

```text
GET    /stock/{symbol}/history
GET    /watchlist
POST   /watchlist
DELETE /watchlist/{symbol}

GET    /portfolio
POST   /portfolio/buy
POST   /portfolio/sell

GET    /transactions
```

## Future Improvements

- User authentication
- Individual portfolios for multiple users
- More frequent market-price updates
- Realized profit and loss tracking
- Portfolio performance charts
- Additional automated tests
- Cloud deployment

## Disclaimer

TradeTrack is a paper-trading project for educational purposes. Trades use virtual funds and do not execute real financial transactions.
