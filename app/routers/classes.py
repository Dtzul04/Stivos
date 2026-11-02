"""GET /classes. Lists each class and how many spots are still open."""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlmodel import Session, select

from app.db import get_session
from app.models import Booking, BookingStatus, Class
from app.schemas import ClassRead

router = APIRouter(tags=["classes"])


@router.get("/classes", response_model=list[ClassRead])
def list_classes(session: Session = Depends(get_session)) -> list[ClassRead]:
    classes = session.exec(select(Class).order_by(Class.start_time)).all()
    response: list[ClassRead] = []
    for dance_class in classes:
        # Only status "booked" takes a spot. Waitlisted and cancelled do not.
        booked_count = session.exec(
            select(func.count(Booking.id)).where(
                Booking.class_id == dance_class.id,
                Booking.status == BookingStatus.booked,
            )
        ).one()
        response.append(
            ClassRead(
                id=dance_class.id,
                name=dance_class.name,
                instructor=dance_class.instructor,
                start_time=dance_class.start_time,
                capacity=dance_class.capacity,
                spots_remaining=dance_class.capacity - booked_count,
            )
        )
    return response
