-- Stock Market DWH - Analytical Queries
-- Run these in AWS Athena against the stock_market_dwh database

-- Query 1: Top performing stocks by average daily return
SELECT ticker, 
       ROUND(avg_daily_return, 4) as avg_return,
       ROUND(best_day_return, 4) as best_day,
       ROUND(worst_day_return, 4) as worst_day,
       positive_day_pct
FROM stock_market_dwh.top_performers
ORDER BY avg_daily_return DESC;

-- Query 2: Market sentiment by day
SELECT DATE(date) as trading_date,
       ROUND(avg_return, 4) as avg_return,
       positive_stocks,
       total_stocks,
       market_sentiment
FROM stock_market_dwh.market_overview
ORDER BY trading_date DESC;

-- Query 3: Most volatile stocks
SELECT ticker,
       ROUND(best_day_return, 4) as best_day_pct,
       ROUND(worst_day_return, 4) as worst_day_pct,
       ROUND(avg_price_range, 4) as avg_price_range,
       total_volume
FROM stock_market_dwh.top_performers
ORDER BY best_day_return DESC;

-- Query 4: Most actively traded stocks
SELECT ticker,
       total_volume,
       ROUND(avg_daily_return, 4) as avg_return,
       positive_days,
       total_days
FROM stock_market_dwh.top_performers
ORDER BY total_volume DESC
LIMIT 3;