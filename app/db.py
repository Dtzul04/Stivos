"""Opens the connection to Postgres and hands a session to each request."""

import os
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

# Compose sets this. Inside Docker the host name is "db", not localhost.
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("Set DATABASE_URL before starting Stivos.")

# One shared engine for the whole app. It opens connections as they are needed.
engine = create_engine(database_url)


def create_db_and_tables() -> None:
    # Importing models registers their tables on SQLModel.metadata.
    import app.models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    # One session per request. It closes when the request finishes.
    with Session(engine) as session:
        yield session
