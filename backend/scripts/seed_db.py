"""Create database tables and seed deterministic mock records for local development."""

from app.db import Base, get_engine
from app import models  # noqa: F401  # Ensure SQLAlchemy model metadata is registered.
from app.db.session import get_database_url
from app.services import seed_database
from sqlalchemy.orm import Session


def main() -> None:
    engine = get_engine()

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        seed_database(session)

    print(f"Seed complete using DATABASE_URL={get_database_url()}")


if __name__ == "__main__":
    main()
