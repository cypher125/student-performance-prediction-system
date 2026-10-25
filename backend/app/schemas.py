"""Request bodies. Pydantic rejects malformed input before it reaches the database."""
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

Level = Literal["ND1", "ND2", "HND1", "HND2"]
Role = Literal["admin", "lecturer", "adviser", "student"]


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class PasswordIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class RecordIn(BaseModel):
    """One student's record for one semester, as typed into the manual entry form."""
    student_code: str = Field(min_length=1, max_length=32)
    level: str = Field(min_length=1, max_length=12)
    session: str = Field(min_length=7, max_length=12)
    semester: str = Field(min_length=1, max_length=16)
    attendance_pct: float | None = Field(None, ge=0, le=100)
    ca_score: float | None = Field(None, ge=0, le=100)
    assignment_score: float | None = Field(None, ge=0, le=100)
    prior_gpa: float | None = Field(None, ge=0, le=4)
    exam_score: float | None = Field(None, ge=0, le=100)
    gpa: float | None = Field(None, ge=0, le=4)


class StudentIn(BaseModel):
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    matric_number: str = Field(min_length=3, max_length=32)
    level: Level
    session: str = Field(pattern=r"^\d{4}/\d{4}$")


class AlertUpdate(BaseModel):
    status: Literal["New", "Acknowledged", "Resolved"]
    action_taken: str | None = Field(None, max_length=2000)


class UserIn(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr | None = None
    role: Role
    password: str = Field(min_length=8, max_length=128)
    student_code: str | None = Field(None, max_length=32)


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=120)
    email: EmailStr | None = None
    role: Role | None = None
    is_active: bool | None = None
    password: str | None = Field(None, min_length=8, max_length=128)
