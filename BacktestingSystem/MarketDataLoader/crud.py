from uuid import UUID
from models import PriceData


def save_prices(session, df, instrument_id:UUID):
    objects = []

    for timestamp, row in df.iterrows():
        obj = PriceData(
            instrument_id =instrument_id,
            timestamp = timestamp.to_pydatetime(),
            open = float(row["Open"]),
            close = float(row["Close"])
        )
        objects.append(obj)

        session.bulk_save_objects(objects)
        session.commit()


