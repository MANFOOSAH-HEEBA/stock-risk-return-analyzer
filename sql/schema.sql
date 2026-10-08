-- Works on SQLite and MySQL 8+. Dates are stored as 'YYYY-MM-DD' text.
DROP VIEW IF EXISTS daily_returns;
DROP TABLE IF EXISTS prices;
DROP TABLE IF EXISTS stocks;

CREATE TABLE stocks (
    ticker  VARCHAR(20)  PRIMARY KEY,
    company VARCHAR(100) NOT NULL,
    sector  VARCHAR(50)  NOT NULL
);

CREATE TABLE prices (
    ticker      VARCHAR(20) NOT NULL,
    trade_date  VARCHAR(10) NOT NULL,
    close_price DOUBLE      NOT NULL,
    volume      BIGINT,
    PRIMARY KEY (ticker, trade_date),
    FOREIGN KEY (ticker) REFERENCES stocks (ticker)
);

CREATE VIEW daily_returns AS
SELECT ticker,
       trade_date,
       close_price,
       close_price / LAG(close_price) OVER (PARTITION BY ticker ORDER BY trade_date) - 1 AS daily_return
FROM prices;
