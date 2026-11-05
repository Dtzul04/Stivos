"""GET /students. The page uses this list to pick who is booking."""

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import Student
from app.schemas import StudentRead

router = APIRouter(tags=["students"])


@router.get("/students", response_model=list[StudentRead])
def list_students(session: Session = Depends(get_session)) -> list[Student]:
    return list(session.exec(select(Student).order_by(Student.name)).all())
