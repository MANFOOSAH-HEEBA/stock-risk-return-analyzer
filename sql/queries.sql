-- Each query starts with "-- name: <id>". Standard SQL: joins, GROUP BY, CTEs, window functions.

-- name: sector_avg_return
-- Average daily return and % of up-days by sector (JOIN + GROUP BY).
SELECT s.sector,
       COUNT(DISTINCT s.ticker)                               AS num_stocks,
       ROUND(AVG(r.daily_return) * 100, 4)                    AS avg_daily_return_pct,
       ROUND(100.0 * SUM(CASE WHEN r.daily_return > 0 THEN 1 ELSE 0 END)
             / COUNT(r.daily_return), 2)                      AS pct_up_days
FROM stocks s
JOIN daily_returns r ON r.ticker = s.ticker
WHERE r.daily_return IS NOT NULL AND s.sector <> 'Benchmark'
GROUP BY s.sector
ORDER BY avg_daily_return_pct DESC;

-- name: best_worst_month
-- Best and worst calendar month for each stock (CTEs + ROW_NUMBER + LAG window functions).
WITH month_end AS (
    SELECT ticker,
           SUBSTR(trade_date, 1, 7) AS month,
           close_price,
           ROW_NUMBER() OVER (PARTITION BY ticker, SUBSTR(trade_date, 1, 7)
                              ORDER BY trade_date DESC) AS rn
    FROM prices
),
monthly AS (
    SELECT ticker, month,
           close_price / LAG(close_price) OVER (PARTITION BY ticker ORDER BY month) - 1 AS month_return
    FROM month_end WHERE rn = 1
),
ranked AS (
    SELECT ticker, month, month_return,
           ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY month_return DESC) AS best_rank,
           ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY month_return ASC)  AS worst_rank
    FROM monthly WHERE month_return IS NOT NULL
)
SELECT s.company, r.ticker,
       CASE WHEN r.best_rank = 1 THEN 'Best month' ELSE 'Worst month' END AS type,
       r.month,
       ROUND(r.month_return * 100, 2) AS month_return_pct
FROM ranked r
JOIN stocks s ON s.ticker = r.ticker
WHERE (r.best_rank = 1 OR r.worst_rank = 1) AND s.sector <> 'Benchmark'
ORDER BY s.company, type;

-- name: moving_average
-- 50-day moving average of the close price (window frame).
SELECT ticker, trade_date, close_price,
       AVG(close_price) OVER (PARTITION BY ticker ORDER BY trade_date
                              ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS ma_50
FROM prices
ORDER BY ticker, trade_date;

-- name: top_total_return
-- Total return over the full period, ranked (first/last price via ROW_NUMBER, then JOIN).
WITH ordered AS (
    SELECT ticker, close_price,
           ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY trade_date ASC)  AS rn_first,
           ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY trade_date DESC) AS rn_last
    FROM prices
),
ends AS (
    SELECT f.ticker, f.close_price AS first_price, l.close_price AS last_price
    FROM ordered f
    JOIN ordered l ON l.ticker = f.ticker AND l.rn_last = 1
    WHERE f.rn_first = 1
)
SELECT s.company, s.sector, ROUND(e.first_price, 2) AS first_price, ROUND(e.last_price, 2) AS last_price,
       ROUND((e.last_price / e.first_price - 1) * 100, 2) AS total_return_pct
FROM ends e
JOIN stocks s ON s.ticker = e.ticker
WHERE s.sector <> 'Benchmark'
ORDER BY total_return_pct DESC;

-- name: volume_by_sector
-- Average daily traded volume by sector.
SELECT s.sector, ROUND(AVG(p.volume), 0) AS avg_daily_volume
FROM prices p
JOIN stocks s ON s.ticker = p.ticker
WHERE s.sector <> 'Benchmark'
GROUP BY s.sector
ORDER BY avg_daily_volume DESC;
