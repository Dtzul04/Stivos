"""The JSON shape returned by the API. This is not a database table."""

from datetime import datetime

from app.models import BookingStatus
from pydantic import BaseModel, ConfigDict


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str


class ClassRead(BaseModel):
    id: int
    name: str
    instructor: str
    start_time: datetime
    capacity: int
    # Calculated in the route. It is not stored as its own column.
    spots_remaining: int

class BookingCreate(BaseModel):
    student_id: int
    class_id: int
    
class BookingRead(BaseModel):
    # Lets FastAPI read the fields off the database row.
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    class_id: int
    status: BookingStatus
    created_at: datetime

