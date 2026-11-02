"""Loads fake classes and students. Safe to run every time the container starts."""

import time
from datetime import datetime, timezone

from sqlalchemy import text
from sqlmodel import Session, select

from app.db import create_db_and_tables, engine
from app.models import Class, Student

# Times are UTC. No bookings are seeded, so every class starts with open spots.
CLASSES = [
    {
        "name": "Beginner Salsa",
        "instructor": "Maya Ortiz",
        "start_time": datetime(2026, 11, 10, 18, 0, tzinfo=timezone.utc),
        "capacity": 12,
    },
    {
        "name": "Hip Hop Foundations",
        "instructor": "Jordan Lee",
        "start_time": datetime(2026, 11, 11, 19, 0, tzinfo=timezone.utc),
        "capacity": 16,
    },
    {
        "name": "Contemporary Flow",
        "instructor": "Ava Singh",
        "start_time": datetime(2026, 11, 12, 17, 30, tzinfo=timezone.utc),
        "capacity": 10,
    },
    {
        "name": "Ballet Basics",
        "instructor": "Elena Petrova",
        "start_time": datetime(2026, 11, 13, 10, 0, tzinfo=timezone.utc),
        "capacity": 8,
    },
]

STUDENTS = [
    {"name": "Sam Rivera", "email": "sam.rivera@example.com"},
    {"name": "Priya Shah", "email": "priya.shah@example.com"},
    {"name": "Chris Nguyen", "email": "chris.nguyen@example.com"},
    {"name": "Lina Alvarez", "email": "lina.alvarez@example.com"},
    {"name": "Noah Bennett", "email": "noah.bennett@example.com"},
]


def wait_for_database() -> None:
    # Postgres can be a moment behind "healthy". Try for 30 seconds.
    last_error: Exception | None = None
    for _ in range(30):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"Database not ready: {last_error}")


def seed() -> None:
    wait_for_database()
    create_db_and_tables()
    with Session(engine) as session:
        # Skip a class or student that is already stored, so restarts do not duplicate rows.
        for item in CLASSES:
            exists = session.exec(
                select(Class).where(Class.name == item["name"])
            ).first()
            if exists is None:
                session.add(Class(**item))
        for item in STUDENTS:
            exists = session.exec(
                select(Student).where(Student.email == item["email"])
            ).first()
            if exists is None:
                session.add(Student(**item))
        session.commit()
        class_count = len(session.exec(select(Class)).all())
        student_count = len(session.exec(select(Student)).all())
    print(f"Seed complete: {class_count} classes, {student_count} students.")


if __name__ == "__main__":
    seed()
