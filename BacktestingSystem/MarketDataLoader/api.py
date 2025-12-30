from fastapi import APIRouter
from db import SessionLocal
from yfinance_client import fetch_prices
from crud import save_prices

router = APIRouter()

@router.post("/update/prices")
def load_prices(symbol: str):
    data = fetch_prices(symbol, "1d")

    session = SessionLocal()
    try:
        save_prices(session, [])
    finally:
        session.close()