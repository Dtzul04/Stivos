"""The JSON shape returned by the API. This is not a database table."""

from datetime import datetime

from pydantic import BaseModel


class ClassRead(BaseModel):
    id: int
    name: str
    instructor: str
    start_time: datetime
    capacity: int
    # Calculated in the route. It is not stored as its own column.
    spots_remaining: int
