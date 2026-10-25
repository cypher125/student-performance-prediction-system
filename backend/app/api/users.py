from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models as m
from ..db import get_db
from ..schemas import UserIn, UserUpdate
from ..security import hash_password, require_admin
from .auth import user_json

router = APIRouter(prefix="/api/users", tags=["User management"])


@router.get("", summary="All user accounts (administrators only)")
def list_users(_user: m.User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.scalars(select(m.User).order_by(m.User.role, m.User.username)).all()
    return {"count": len(users), "users": [user_json(u) for u in users]}


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a user account")
def create_user(body: UserIn, _user: m.User = Depends(require_admin), db: Session = Depends(get_db)):
    username = body.username.strip().lower()
    if db.scalar(select(m.User).where(m.User.username == username)):
        raise HTTPException(status.HTTP_409_CONFLICT, f"The username {username} is taken.")
    student_id = None
    if body.role == "student":
        student = db.scalar(select(m.Student).where(m.Student.student_code == (body.student_code or "").upper()))
        if student is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "A student account needs a valid student code.")
        if student.user is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "That student already has an account.")
        student_id = student.id
    user = m.User(username=username, full_name=body.full_name.strip(), email=body.email, role=body.role,
                  password_hash=hash_password(body.password), student_id=student_id)
    db.add(user)
    _commit(db)
    return user_json(user)


def _commit(db: Session):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "That email address is already used by another account.") from None


@router.patch("/{user_id}", summary="Update or deactivate a user account")
def update_user(user_id: int, body: UserUpdate, admin: m.User = Depends(require_admin),
                db: Session = Depends(get_db)):
    user = db.get(m.User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")
    if user.id == admin.id and (body.is_active is False or (body.role and body.role != "admin")):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot deactivate or demote your own account.")
    for field in ("full_name", "email", "role", "is_active"):
        value = getattr(body, field)
        if value is not None:
            setattr(user, field, value)
    if body.password:
        user.password_hash = hash_password(body.password)
    _commit(db)
    return user_json(user)
