"""Booking rules against the Postgres database inside Docker."""

from datetime import datetime, timedelta, timezone
from threading import Barrier, Thread

import pytest
from fastapi import HTTPException
from sqlmodel import Session, select

from app.db import engine
from app.models import Booking, BookingStatus, Class, Student
from app.services.booking import book_student, cancel_booking


def _add_class(session: Session, capacity: int) -> Class:
    dance_class = Class(
        name="Test class",
        instructor="Test instructor",
        start_time=datetime(2026, 12, 1, 18, 0, tzinfo=timezone.utc),
        capacity=capacity,
    )
    session.add(dance_class)
    session.commit()
    session.refresh(dance_class)
    return dance_class


def _add_student(session: Session, name: str) -> Student:
    student = Student(name=name, email=f"{name}@booking-test.example")
    session.add(student)
    session.commit()
    session.refresh(student)
    return student


def _cleanup(class_id: int, student_ids: list[int]) -> None:
    with Session(engine) as session:
        bookings = session.exec(
            select(Booking).where(Booking.class_id == class_id)
        ).all()
        for booking in bookings:
            session.delete(booking)
        dance_class = session.get(Class, class_id)
        if dance_class is not None:
            session.delete(dance_class)
        for student_id in student_ids:
            student = session.get(Student, student_id)
            if student is not None:
                session.delete(student)
        session.commit()


def test_booking_when_spots_remain_is_booked() -> None:
    with Session(engine) as session:
        dance_class = _add_class(session, capacity=2)
        student = _add_student(session, "spots-remain")
        class_id, student_id = dance_class.id, student.id
    assert class_id is not None and student_id is not None
    try:
        with Session(engine) as session:
            booking = book_student(session, student_id, class_id)
        assert booking.status == BookingStatus.booked
    finally:
        _cleanup(class_id, [student_id])


def test_booking_when_class_is_full_is_waitlisted() -> None:
    with Session(engine) as session:
        dance_class = _add_class(session, capacity=1)
        first = _add_student(session, "full-first")
        second = _add_student(session, "full-second")
        class_id = dance_class.id
        first_id, second_id = first.id, second.id
    assert class_id is not None and first_id is not None and second_id is not None
    try:
        with Session(engine) as session:
            book_student(session, first_id, class_id)
        with Session(engine) as session:
            booking = book_student(session, second_id, class_id)
        assert booking.status == BookingStatus.waitlisted
    finally:
        _cleanup(class_id, [first_id, second_id])


def test_cancel_booked_promotes_oldest_waitlisted() -> None:
    start = datetime(2026, 12, 2, 12, 0, tzinfo=timezone.utc)
    with Session(engine) as session:
        dance_class = _add_class(session, capacity=1)
        holder = _add_student(session, "cancel-holder")
        older = _add_student(session, "cancel-older")
        newer = _add_student(session, "cancel-newer")
        class_id = dance_class.id
        holder_id, older_id, newer_id = holder.id, older.id, newer.id
        assert class_id is not None
        session.add(Booking(
            student_id=holder_id,
            class_id=class_id,
            status=BookingStatus.booked,
            created_at=start,
        ))
        older_booking = Booking(
            student_id=older_id,
            class_id=class_id,
            status=BookingStatus.waitlisted,
            created_at=start + timedelta(minutes=1),
        )
        newer_booking = Booking(
            student_id=newer_id,
            class_id=class_id,
            status=BookingStatus.waitlisted,
            created_at=start + timedelta(minutes=2),
        )
        session.add(older_booking)
        session.add(newer_booking)
        session.commit()
        session.refresh(older_booking)
        session.refresh(newer_booking)
        held_id = session.exec(
            select(Booking).where(
                Booking.class_id == class_id,
                Booking.status == BookingStatus.booked,
            )
        ).one().id
        older_booking_id, newer_booking_id = older_booking.id, newer_booking.id
    assert held_id is not None
    try:
        with Session(engine) as session:
            cancel_booking(session, held_id)
        with Session(engine) as session:
            promoted = session.get(Booking, older_booking_id)
            still_waiting = session.get(Booking, newer_booking_id)
        assert promoted is not None and promoted.status == BookingStatus.booked
        assert still_waiting is not None and still_waiting.status == BookingStatus.waitlisted
    finally:
        _cleanup(class_id, [holder_id, older_id, newer_id])


def test_cancel_waitlisted_promotes_nobody() -> None:
    with Session(engine) as session:
        dance_class = _add_class(session, capacity=1)
        holder = _add_student(session, "wait-holder")
        waiting = _add_student(session, "wait-waiting")
        class_id = dance_class.id
        holder_id, waiting_id = holder.id, waiting.id
        assert class_id is not None
        session.add(Booking(
            student_id=holder_id,
            class_id=class_id,
            status=BookingStatus.booked,
        ))
        waiting_booking = Booking(
            student_id=waiting_id,
            class_id=class_id,
            status=BookingStatus.waitlisted,
        )
        session.add(waiting_booking)
        session.commit()
        session.refresh(waiting_booking)
        waiting_booking_id = waiting_booking.id
        held = session.exec(
            select(Booking).where(
                Booking.class_id == class_id,
                Booking.student_id == holder_id,
            )
        ).one()
    assert waiting_booking_id is not None and held.id is not None
    try:
        with Session(engine) as session:
            cancel_booking(session, waiting_booking_id)
        with Session(engine) as session:
            still_booked = session.get(Booking, held.id)
        assert still_booked is not None and still_booked.status == BookingStatus.booked
    finally:
        _cleanup(class_id, [holder_id, waiting_id])


def test_missing_student_or_class_is_404() -> None:
    with Session(engine) as session:
        dance_class = _add_class(session, capacity=1)
        student = _add_student(session, "missing-pair")
        class_id, student_id = dance_class.id, student.id
    assert class_id is not None and student_id is not None
    try:
        with Session(engine) as session:
            with pytest.raises(HTTPException) as missing_student:
                book_student(session, 9_999_999, class_id)
            with pytest.raises(HTTPException) as missing_class:
                book_student(session, student_id, 9_999_999)
        assert missing_student.value.status_code == 404
        assert missing_class.value.status_code == 404
    finally:
        _cleanup(class_id, [student_id])


def test_two_bookings_racing_for_the_last_spot() -> None:
    with Session(engine) as session:
        dance_class = _add_class(session, capacity=1)
        first = _add_student(session, "race-first")
        second = _add_student(session, "race-second")
        class_id = dance_class.id
        first_id, second_id = first.id, second.id
    assert class_id is not None and first_id is not None and second_id is not None
    barrier = Barrier(2)
    errors: list[BaseException] = []

    def book(student_id: int) -> None:
        try:
            barrier.wait()
            with Session(engine) as session:
                book_student(session, student_id, class_id)
        except BaseException as exc:
            errors.append(exc)

    threads = [Thread(target=book, args=(student_id,)) for student_id in (first_id, second_id)]
    try:
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert errors == []
        with Session(engine) as session:
            rows = session.exec(select(Booking).where(Booking.class_id == class_id)).all()
        statuses = sorted(row.status for row in rows)
        assert statuses == [BookingStatus.booked, BookingStatus.waitlisted]
    finally:
        _cleanup(class_id, [first_id, second_id])
