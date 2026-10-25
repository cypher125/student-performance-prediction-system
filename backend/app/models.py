"""The five entities of the ERD (Figure 3.2): Student, AcademicRecord, Prediction, Alert, User."""
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

ROLES = ("admin", "lecturer", "adviser", "student")
STAFF_ROLES = ("admin", "lecturer", "adviser")
ALERT_STATUSES = ("New", "Acknowledged", "Resolved")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    matric_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(60))
    last_name: Mapped[str] = mapped_column(String(60))
    department: Mapped[str] = mapped_column(String(80), default="Computer Science")
    programme: Mapped[str] = mapped_column(String(8))  # ND or HND
    level: Mapped[str] = mapped_column(String(8))  # current level
    session: Mapped[str] = mapped_column(String(9))  # current session
    entry_session: Mapped[str] = mapped_column(String(9))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    records: Mapped[list["AcademicRecord"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    user: Mapped["User | None"] = relationship(back_populates="student")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class AcademicRecord(Base):
    __tablename__ = "academic_records"
    __table_args__ = (UniqueConstraint("student_id", "session", "semester", name="one_record_per_semester"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    level: Mapped[str] = mapped_column(String(8))
    session: Mapped[str] = mapped_column(String(9), index=True)
    semester: Mapped[str] = mapped_column(String(8))
    attendance_pct: Mapped[float | None] = mapped_column(Float)
    ca_score: Mapped[float | None] = mapped_column(Float)
    assignment_score: Mapped[float | None] = mapped_column(Float)
    prior_gpa: Mapped[float | None] = mapped_column(Float)
    # Outcomes: empty until results are released.
    exam_score: Mapped[float | None] = mapped_column(Float)
    gpa: Mapped[float | None] = mapped_column(Float)
    performance_class: Mapped[str | None] = mapped_column(String(12))
    source: Mapped[str] = mapped_column(String(12), default="manual")  # seed, upload or manual
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    student: Mapped[Student] = relationship(back_populates="records")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="record", cascade="all, delete-orphan")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("academic_records.id", ondelete="CASCADE"), index=True)
    predicted_class: Mapped[str] = mapped_column(String(12))
    confidence_score: Mapped[float] = mapped_column(Float)  # probability of the predicted class
    fail_probability: Mapped[float] = mapped_column(Float)
    probabilities: Mapped[dict] = mapped_column(JSON)
    risk_level: Mapped[str] = mapped_column(String(8), index=True)
    explanation: Mapped[list] = mapped_column(JSON)
    recommendations: Mapped[list] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    student: Mapped[Student] = relationship(back_populates="predictions")
    record: Mapped[AcademicRecord] = relationship(back_populates="predictions")
    alert: Mapped["Alert | None"] = relationship(back_populates="prediction", cascade="all, delete-orphan")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.id", ondelete="CASCADE"), unique=True)
    alert_type: Mapped[str] = mapped_column(String(16))  # High risk or Medium risk
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="New", index=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action_taken: Mapped[str | None] = mapped_column(Text)  # the intervention log

    prediction: Mapped[Prediction] = relationship(back_populates="alert")
    acknowledged_by_user: Mapped["User | None"] = relationship()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(120), unique=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16))
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id", ondelete="SET NULL"), unique=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    student: Mapped[Student | None] = relationship(back_populates="user")
