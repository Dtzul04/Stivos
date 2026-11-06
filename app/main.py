"""Front door of the API. Creates the app, checks Postgres, and attaches the routes."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.db import create_db_and_tables, engine
from app.routers import bookings, classes, students


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
# The Vite page runs on another port, so the browser asks permission before calling the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(classes.router)
app.include_router(students.router)
app.include_router(bookings.router)


# Confirms the process is up. This route does not query the database.
@app.get("/health")
def health():
    return {"status": "ok"}
