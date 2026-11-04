"""Rules for who gets a spot, who waits, and who moves up after a cancel."""

from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import Session, select

from app.models import Booking, BookingStatus, Class, Student


def book_student(session: Session, student_id: int, class_id: int) -> Booking:
    # Lock this class until commit. A second booking for the same class waits,
    # then counts again, so two requests cannot both take the last spot.
    dance_class = session.exec(
        select(Class).where(Class.id == class_id).with_for_update()
    ).one_or_none()
    student = session.get(Student, student_id)
    if dance_class is None or student is None:
        raise HTTPException(status_code=404, detail="Class or student not found")

    # Count rows that currently hold a spot. Waiting rows are not in this count.
    booked_count = session.exec(
        select(func.count(Booking.id)).where(
            Booking.class_id == class_id,
            Booking.status == BookingStatus.booked,
        )
    ).one()
    status = (
        BookingStatus.booked
        if booked_count < dance_class.capacity
        else BookingStatus.waitlisted
    )
    booking = Booking(student_id=student_id, class_id=class_id, status=status)
    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking


def cancel_booking(session: Session, booking_id: int) -> Booking | None:
    booking = session.get(Booking, booking_id)
    if booking is None:
        return None
    # Cancelling twice must not promote a second person.
    if booking.status == BookingStatus.cancelled:
        return booking

    # Same class lock as booking. Two cancels wait in line, so each freed spot
    # promotes a different waiting student.
    session.exec(
        select(Class).where(Class.id == booking.class_id).with_for_update()
    ).one()

    held_a_spot = booking.status == BookingStatus.booked
    booking.status = BookingStatus.cancelled
    if held_a_spot:
        # First in line is the waiting row with the earliest created_at.
        next_in_line = session.exec(
            select(Booking)
            .where(
                Booking.class_id == booking.class_id,
                Booking.status == BookingStatus.waitlisted,
            )
            .order_by(Booking.created_at)
        ).first()
        if next_in_line is not None:
            next_in_line.status = BookingStatus.booked

    session.add(booking)
    session.commit()
    session.refresh(booking)
    return booking