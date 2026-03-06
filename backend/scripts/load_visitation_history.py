"""Load real NPS monthly visitation history into park_visitation_history."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models  # noqa: F401
from app.db import Base, get_engine
from app.jobs import NPSVisitationETL
from app.models import Park
from app.services import seed_database


def main() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        park_count = session.scalar(select(func.count()).select_from(Park)) or 0
        if park_count == 0:
            seed_database(session)

        inserted = NPSVisitationETL().run(session=session)
        print(f"Loaded {inserted} monthly visitation rows from NPS source")


if __name__ == "__main__":
    main()
