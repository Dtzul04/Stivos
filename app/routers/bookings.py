"""Routes that create and change bookings."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.schemas import BookingCreate, BookingRead
from app.services.booking import book_student, cancel_booking

router = APIRouter(tags=["bookings"])


@router.post("/bookings", response_model=BookingRead)
def create_booking(
    body: BookingCreate,
    session: Session = Depends(get_session),
) -> BookingRead:
    # The body only names who and which class. The service picks the status.
    return book_student(session, body.student_id, body.class_id)
    
@router.post("/bookings/{booking_id}/cancel", response_model=BookingRead)
def cancel(
    booking_id: int,
    session: Session = Depends(get_session),
) -> BookingRead:
    booking = cancel_booking(session, booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking