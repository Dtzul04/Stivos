"""The three database tables. This file describes them. It does not book anyone."""

from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    # SQLModel rejects datetimes that have no timezone.
    return datetime.now(timezone.utc)


class BookingStatus(str, Enum):
    booked = "booked"
    waitlisted = "waitlisted"
    cancelled = "cancelled"


class Class(SQLModel, table=True):
    # "class" is a reserved word, so the table is named classes.
    __tablename__ = "classes"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    instructor: str
    start_time: datetime
    capacity: int


class Student(SQLModel, table=True):
    __tablename__ = "students"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    # One row per email. The index makes that lookup fast.
    email: str = Field(unique=True, index=True)


class Booking(SQLModel, table=True):
    __tablename__ = "bookings"

    id: int | None = Field(default=None, primary_key=True)
    # These point at students.id and classes.id.
    student_id: int = Field(foreign_key="students.id")
    class_id: int = Field(foreign_key="classes.id")
    status: BookingStatus
    created_at: datetime = Field(default_factory=utc_now)
