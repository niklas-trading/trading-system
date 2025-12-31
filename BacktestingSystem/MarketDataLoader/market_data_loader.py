from fastapi import FastAPI
from db import SessionLocal
from yfinance_client import fetch_prices
from crud import save_prices
from db import engine
from models import Base
from uuid import uuid4

app = FastAPI()
Base.metadata.create_all(bind=engine)

# Get

@app.get("/__routes")
def list_routes():
    return [route.path for route in app.routes]

# Post



@app.post("/api/v1/update/prices")
def load_prices(symbol: str):
    data = fetch_prices(symbol, "1d")

    session = SessionLocal()
    try:
        save_prices(session, data, instrument_id=uuid4())
    finally:
        session.close()

    return {"status": "ok", "uuid": str(uuid4())}

