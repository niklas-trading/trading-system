# Running market data loader
````psh
pip3 install fastapi uvicorn sqlalchemy psycopg2-binary yfinance pydantic alembic python-dotenv
````
Check if added to path.
````psh
cd trading-system/BacktestingSystem/MarketDataLoader/
uvicorn market_data_loader:app --reload
````
````psh
docker run --name trading -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password -e POSTGRES_DB=trading -p 5432:5432 -d postgres
````