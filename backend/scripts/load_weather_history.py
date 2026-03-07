"""Load real Meteostat daily weather history into park_weather_history."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models  # noqa: F401
from app.db import Base, get_engine
from app.jobs import MeteostatWeatherETL
from app.models import Park
from app.services import seed_database


def main() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        park_count = session.scalar(select(func.count()).select_from(Park)) or 0
        if park_count == 0:
            seed_database(session)

        inserted = MeteostatWeatherETL().run(session=session)
        print(f"Loaded {inserted} daily weather rows from Meteostat Point Daily")


if __name__ == "__main__":
    main()
