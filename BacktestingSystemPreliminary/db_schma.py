import psycopg

with psycopg.connect("dbname=backtest_data user=postgres") as conn:
    with conn.cursor() as cursor:
        cursor.execute("""CREATE EXTENSION IF NOT EXISTS timescaledb;""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS ticker
                          (
                              ticker   text PRIMARY KEY,
                              exchange text,
                              currency text
                          );
                       """)

        cursor.execute("INSERT INTO ticker(ticker, exchange, currency) VALUES (%s, %s, %s) ON CONFLICT (ticker) DO NOTHING",
                       ("AAPL", "NASDAQ", "usd"))

        cursor.execute("""CREATE TABLE IF NOT EXISTS earnings 
                          (
                            ticker text NOT NULL,
                            earnings_date date NOT NULL,
                            fiscal_quarter text NOT NULL,
                            PRIMARY KEY(ticker, earnings_date)
                          );
        """)


        cursor.execute("""CREATE TABLE IF NOT EXISTS ohlcv_1h
                          (
                              datetime timestamptz      NOT NULL,
                              ticker   text             NOT NULL,

                              open     double precision NULL,
                              high     double precision NULL,
                              low      double precision NULL,
                              close    double precision NULL,
                              volume   double precision NULL,

                              PRIMARY KEY (datetime, ticker)
                          );
        """)
        cursor.execute("""SELECT create_hypertable
                          (
                            'ohlcv_1h',
                            'datetime',
                            'ticker',
                            number_partitions => 8,
                            if_not_exists => true
                        );
        """)