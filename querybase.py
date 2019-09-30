query_build_price_table = \
'''CREATE TABLE IF NOT EXISTS `STOCK_PRICE`
   (ID INTEGER PRIMARY KEY   AUTOINCREMENT,
    stock_id       TEXT    NOT NULL,
    date           TEXT,
    volume         INT,
    turnover_value INT,
    open           REAL,
    high           REAL,
    low            REAL,
    close          REAL,
    spread         REAL,
    change_ratio   REAL,
    transactions   INT,
    PE_ratio        REAL,
    Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP);'''