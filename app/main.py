"""Front door of the API. Creates the app, checks Postgres, and attaches the routes."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.db import create_db_and_tables, engine
from app.routers import bookings, classes


# Code before yield runs at startup. Code after yield runs at shutdown.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail immediately if Postgres cannot be reached.
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    # Create classes, students, and bookings when those tables are missing.
    create_db_and_tables()
    yield


# title is the name shown on the /docs page.
app = FastAPI(title="Stivos", lifespan=lifespan)
app.include_router(classes.router)
app.include_router(bookings.router)


# Confirms the process is up. This route does not query the database.
@app.get("/health")
def health():
    return {"status": "ok"}
