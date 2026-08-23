import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import "./App.css";

function App() {
  const [symbol, setSymbol] = useState("AAPL");
  const [stock, setStock] = useState(null);
  const [history, setHistory] = useState([]);
  const [range, setRange] = useState("1M");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [watchlist, setWatchlist] = useState([]);
  const [watchlistMessage, setWatchlistMessage] = useState("");
  const [portfolio, setPortfolio] = useState(null);
  const [buyShares, setBuyShares] = useState("1");
  const [tradeMessage, setTradeMessage] = useState("");
  const [transactions, setTransactions] = useState([]);

  // Load the saved watchlist when the page first opens
  useEffect(() => {
  loadWatchlist();
  loadPortfolio();
  loadTransactions();
}, []);

  // Format prices to 2 decimal places
  function formatPrice(value) {
    return Number(value).toFixed(2);
  }

  // Format large volume numbers
  function formatVolume(value) {
    const number = Number(value);

    if (number >= 1_000_000_000) {
      return `${(number / 1_000_000_000).toFixed(1)}B`;
    }

    if (number >= 1_000_000) {
      return `${(number / 1_000_000).toFixed(1)}M`;
    }

    if (number >= 1_000) {
      return `${(number / 1_000).toFixed(1)}K`;
    }

    return number.toLocaleString();
  }

  // Decide how much historical data to show
  function getChartData() {
    let numberOfDays;

    if (range === "1M") {
      numberOfDays = 22;
    } else if (range === "3M") {
      numberOfDays = 66;
    } else {
      numberOfDays = history.length;
    }

    return history
      .slice(0, numberOfDays)
      .reverse();
  }

  // Get watchlist from PostgreSQL through FastAPI
  async function loadWatchlist() {
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/watchlist"
      );

      if (!response.ok) {
        throw new Error("Unable to load watchlist.");
      }

      const data = await response.json();
      setWatchlist(data);
    } catch (error) {
      console.error(error);
    }
  }
  async function loadPortfolio() {
  try {
    const response = await fetch(
      "http://127.0.0.1:8000/portfolio"
    );

    if (!response.ok) {
      throw new Error("Unable to load portfolio.");
    }

    const data = await response.json();

    setPortfolio(data);
  } catch (error) {
    console.error(error);
  }
}
async function loadTransactions() {
  try {
    const response = await fetch(
      "http://127.0.0.1:8000/transactions"
    );

    if (!response.ok) {
      throw new Error("Unable to load transactions.");
    }

    const data = await response.json();
    setTransactions(data);
  } catch (error) {
    console.error(error);
  }
}

  // Search for a stock
  async function searchStock(event) {
    if (event) {
      event.preventDefault();
    }

    const cleanedSymbol = symbol.trim().toUpperCase();

    if (!cleanedSymbol) {
      setError("Please enter a stock symbol.");
      return;
    }

    setLoading(true);
    setError("");
    setWatchlistMessage("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/stock/${cleanedSymbol}/history`
      );

      if (!response.ok) {
        throw new Error("Unable to retrieve stock data.");
      }

      const data = await response.json();

      setStock({
        symbol: data.symbol,
        ...data.quote,
      });

      setHistory(data.history);
    } catch (error) {
      setError(error.message);
      setStock(null);
      setHistory([]);
    } finally {
      setLoading(false);
    }
  }

  // Add the currently displayed stock to the watchlist
  async function addToWatchlist() {
    if (!stock) {
      return;
    }

    setWatchlistMessage("");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/watchlist",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            symbol: stock.symbol,
          }),
        }
      );

      if (response.status === 409) {
        setWatchlistMessage(
          `${stock.symbol} is already in your watchlist.`
        );
        return;
      }

      if (!response.ok) {
        throw new Error("Unable to add stock to watchlist.");
      }

      await loadWatchlist();

      setWatchlistMessage(
        `${stock.symbol} added to your watchlist.`
      );
    } catch (error) {
      setWatchlistMessage(error.message);
    }
  }

  // Remove a stock from the watchlist
  async function removeFromWatchlist(symbolToRemove) {
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/watchlist/${symbolToRemove}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        throw new Error("Unable to remove stock.");
      }

      await loadWatchlist();

      setWatchlistMessage(
        `${symbolToRemove} removed from your watchlist.`
      );
    } catch (error) {
      setWatchlistMessage(error.message);
    }
  }
  async function buyStock() {
  if (!stock) {
    return;
  }

  const shares = Number(buyShares);

  if (!shares || shares <= 0) {
    setTradeMessage("Enter a valid number of shares.");
    return;
  }

  setTradeMessage("");

  try {
    const response = await fetch(
      "http://127.0.0.1:8000/portfolio/buy",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          symbol: stock.symbol,
          shares: shares,
        }),
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Unable to complete purchase.");
    }

    setTradeMessage(
      `Bought ${shares} share${shares === 1 ? "" : "s"} of ${stock.symbol}.`
    );

    await loadPortfolio();
    await loadTransactions();
  } catch (error) {
    setTradeMessage(error.message);
  }
}
async function sellStock() {
  if (!stock) {
    return;
  }

  const shares = Number(buyShares);

  if (!shares || shares <= 0) {
    setTradeMessage("Enter a valid number of shares.");
    return;
  }

  setTradeMessage("");

  try {
    const response = await fetch(
      "http://127.0.0.1:8000/portfolio/sell",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          symbol: stock.symbol,
          shares: shares,
        }),
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Unable to complete sale.");
    }

    setTradeMessage(
      `Sold ${shares} share${shares === 1 ? "" : "s"} of ${stock.symbol}.`
    );

    await loadPortfolio();
    await loadTransactions();
  } catch (error) {
    setTradeMessage(error.message);
  }
}

  const chartData = getChartData();

  return (
    <div className="app">
      <header>
        <h1>TradeTrack</h1>

        <p className="subtitle">
          Your personal stock tracking dashboard.
        </p>
      </header>

      <form className="search" onSubmit={searchStock}>
        <input
          value={symbol}
          onChange={(event) =>
            setSymbol(event.target.value.toUpperCase())
          }
          placeholder="Enter stock symbol"
        />

        <button type="submit" disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      {error && <p className="error">{error}</p>}
      {portfolio && (
  <div className="portfolio-card">
    <div className="portfolio-header">
      <div>
        <p className="portfolio-label">Portfolio Value</p>

        <h2>
          ${formatPrice(portfolio.total_value)}
        </h2>
      </div>

      <div
        className={
          portfolio.unrealized_pnl >= 0
            ? "portfolio-pnl positive"
            : "portfolio-pnl negative"
        }
      >
        {portfolio.unrealized_pnl >= 0 ? "+" : ""}
        ${formatPrice(portfolio.unrealized_pnl)}
      </div>
    </div>

    <div className="portfolio-summary">
      <div className="portfolio-stat">
        <span>Cash</span>
        <strong>
          ${formatPrice(portfolio.cash)}
        </strong>
      </div>

      <div className="portfolio-stat">
        <span>Invested</span>
        <strong>
          ${formatPrice(portfolio.holdings_value)}
        </strong>
      </div>

      <div className="portfolio-stat">
        <span>Unrealized P&L</span>
        <strong>
          ${formatPrice(portfolio.unrealized_pnl)}
        </strong>
      </div>
    </div>

    <div className="holdings-section">
      <h3>Holdings</h3>

      {portfolio.holdings.length === 0 ? (
        <p className="empty-holdings">
          You don't own any stocks yet.
        </p>
      ) : (
        <div className="holdings-list">
          {portfolio.holdings.map((holding) => (
            <div
              className="holding-row"
              key={holding.symbol}
            >
              <div>
                <strong>{holding.symbol}</strong>
                <p>
                  {holding.shares} shares
                </p>
              </div>

              <div className="holding-price">
                <strong>
                  ${formatPrice(holding.market_value)}
                </strong>

                <p>
                  Avg. ${formatPrice(
                    holding.average_price
                  )}
                </p>
              </div>

              <div
                className={
                  holding.unrealized_pnl >= 0
                    ? "holding-pnl positive"
                    : "holding-pnl negative"
                }
              >
                {holding.unrealized_pnl >= 0
                  ? "+"
                  : ""}
                ${formatPrice(
                  holding.unrealized_pnl
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  </div>
)}
<div className="transactions-card">
  <h2>Recent Transactions</h2>

  {transactions.length === 0 ? (
    <p className="empty-transactions">
      No transactions yet.
    </p>
  ) : (
    <div className="transactions-list">
      {transactions.map((transaction) => (
        <div
          className="transaction-row"
          key={transaction.id}
        >
          <div>
            <strong>{transaction.symbol}</strong>
            <p>
              {new Date(
                transaction.created_at
              ).toLocaleString()}
            </p>
          </div>

          <div
            className={
              transaction.transaction_type === "BUY"
                ? "transaction-type buy"
                : "transaction-type sell"
            }
          >
            {transaction.transaction_type}
          </div>

          <div>
            {Number(transaction.shares)} shares
          </div>

          <div className="transaction-price">
            ${formatPrice(transaction.price)}
          </div>
        </div>
      ))}
    </div>
  )}
</div>


      {stock && (
        <>
          <div className="stock-card">
            <div className="stock-header">
              <div>
                <h2>{stock.symbol}</h2>

                <div className="price">
                  ${formatPrice(stock.price)}
                </div>

                <div
                  className={
                    Number(stock.change) >= 0
                      ? "change positive"
                      : "change negative"
                  }
                >
                  {Number(stock.change) >= 0 ? "+" : ""}
                  {formatPrice(stock.change)} (
                  {Number(stock.change_percent) >= 0 ? "+" : ""}
                  {formatPrice(stock.change_percent)}%)
                </div>
              </div>

              <div className="trading-day">
                As of {stock.latest_trading_day}
              </div>
            </div>

            <button
              className="watchlist-button"
              onClick={addToWatchlist}
            >
              + Add to Watchlist
            </button>

            <div className="stock-details">
              <div className="stat">
                <span>Open</span>
                <strong>${formatPrice(stock.open)}</strong>
              </div>

              <div className="stat">
                <span>High</span>
                <strong>${formatPrice(stock.high)}</strong>
              </div>

              <div className="stat">
                <span>Low</span>
                <strong>${formatPrice(stock.low)}</strong>
              </div>

              <div className="stat">
                <span>Previous Close</span>
                <strong>
                  ${formatPrice(stock.previous_close)}
                </strong>
              </div>

              <div className="stat">
                <span>Volume</span>
                <strong>
                  {formatVolume(stock.volume)}
                </strong>
              </div>
            </div>
            <div className="trade-box">
              <h3>Paper Trade</h3>

              <div className="trade-controls">
                <input
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={buyShares}
                  onChange={(event) => setBuyShares(event.target.value)}
                />

                <button
                  className="buy-button"
                  onClick={buyStock}
                >
                  Buy {stock.symbol}
                </button>

                <button
                  className="sell-button"
                  onClick={sellStock}
                >
                  Sell {stock.symbol}
                </button>
              </div>

              {tradeMessage && (
                <p className="trade-message">
                  {tradeMessage}
                </p>
              )}
            </div>
            
          </div>

          <div className="chart-card">
            <div className="chart-header">
              <h2>Price History</h2>

              <div className="range-buttons">
                {["1M", "3M", "ALL"].map((option) => (
                  <button
                    key={option}
                    className={
                      range === option ? "active" : ""
                    }
                    onClick={() => setRange(option)}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>

            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />

                <XAxis
                  dataKey="date"
                  tickFormatter={(date) => date.slice(5)}
                />

                <YAxis
                  domain={["auto", "auto"]}
                  tickFormatter={(value) => `$${value}`}
                />

                <Tooltip
                  formatter={(value) => [
                    `$${Number(value).toFixed(2)}`,
                    "Close",
                  ]}
                />

                <Line
                  type="monotone"
                  dataKey="close"
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      <div className="watchlist-card">
        <h2>Watchlist</h2>

        {watchlistMessage && (
          <p className="watchlist-message">
            {watchlistMessage}
          </p>
        )}

        {watchlist.length === 0 ? (
          <p className="empty-watchlist">
            No stocks saved yet.
          </p>
        ) : (
          <div className="watchlist-items">
            {watchlist.map((item) => (
              <div
                className="watchlist-item"
                key={item.id}
              >
                <strong>{item.symbol}</strong>

                <button
                  onClick={() =>
                    removeFromWatchlist(item.symbol)
                  }
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;