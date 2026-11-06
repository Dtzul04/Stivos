"""Front door of the API. Creates the app, checks Postgres, and attaches the routes."""

import os
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


# Local Vite ports, plus any origins listed in CORS_ORIGINS (comma-separated).
# Example on Railway: CORS_ORIGINS=https://stivos.vercel.app
cors_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    *[
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "").split(",")
        if origin.strip()
    ],
]

# title is the name shown on the /docs page.
app = FastAPI(title="Stivos", lifespan=lifespan)
# The browser page runs on another host, so it must be listed here.
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    # Vercel preview and production hosts until a custom domain is set.
    allow_origin_regex=r"https://.*\.vercel\.app",
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
