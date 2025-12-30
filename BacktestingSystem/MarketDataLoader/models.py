from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Date, DateTime, Float, Boolean

Base = declarative_base()

class PriceData(Base):
    __tablename__ = "price_data"

    instrument_id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, primary_key=True)
    open = Column(Float)
    close = Column(Float)