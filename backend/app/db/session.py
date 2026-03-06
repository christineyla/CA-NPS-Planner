"""Session and engine helpers for database access."""

import os
from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_DATABASE_URL = "sqlite:///./local.db"


def get_database_url() -> str:
    """Resolve database URL from environment with a sqlite fallback."""

    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def get_engine() -> Engine:
    """Build SQLAlchemy engine using the configured connection string."""

    return create_engine(get_database_url(), future=True)


def get_session() -> Generator[Session, None, None]:
    """Yield database sessions for request lifecycles."""

    session_factory = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)
    with session_factory() as session:
        yield session
