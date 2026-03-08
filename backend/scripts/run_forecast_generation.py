"""Run forecast generation and crowd calendar refresh for all in-scope parks."""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models  # noqa: F401
from app.db import Base, get_engine
from app.jobs import ForecastGenerationJob
from app.models import Park
from app.services import seed_database


def main() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        park_count = session.scalar(select(func.count()).select_from(Park)) or 0
        if park_count == 0:
            seed_database(session)

        written = ForecastGenerationJob().run(session=session)
        print(f"Generated {written} forecast rows and refreshed crowd calendar records")


if __name__ == "__main__":
    main()
