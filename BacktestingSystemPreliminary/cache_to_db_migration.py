import os

import pyarrow.parquet as pq
import pyarrow
import psycopg


with psycopg.connect("dbname=backtest_data user=postgres") as conn:
    with conn.cursor() as cursor:
        base_path: str = "./cache/"
        for file_name in os.listdir(base_path):
            # load  and prepare data
            apple_data: pyarrow.Table = pq.read_table(base_path + file_name)
            open: list = apple_data.column(0).to_pylist()
            high: list = apple_data.column(1).to_pylist()
            low: list = apple_data.column(2).to_pylist()
            close: list = apple_data.column(3).to_pylist()
            volume: list = apple_data.column(4).to_pylist()
            datetime: list = apple_data.column(5).to_pylist()
            ticker: str = file_name.split("__")[0]
            params: list[tuple] = [(dt, ticker, o, h, l, c, v) for dt, o, h, l, c, v in zip(datetime, open, high, low, close, volume)]

            # save data
            sql_insert_ohlcv_1h: str = "INSERT INTO ohlcv_1h(datetime, ticker, open, high, low, close, volume) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (datetime, ticker) DO NOTHING"
            sql_insert_ticker: str = "INSERT INTO ticker(ticker, exchange, currency) VALUES (%s, %s, %s) ON CONFLICT (ticker) DO NOTHING"
            cursor.execute(sql_insert_ticker, (ticker, "NASDAQ", "usd"))
            cursor.executemany(sql_insert_ohlcv_1h, params)

        conn.commit()