from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, DateTime, Float
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class PriceData(Base):
    __tablename__ = "price_data"

    instrument_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp = Column(DateTime, primary_key=True)
    open = Column(Float)
    close = Column(Float)