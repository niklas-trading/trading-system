from models import PriceData

def save_prices(session, prices):
    session.add(prices)
    session.commit()