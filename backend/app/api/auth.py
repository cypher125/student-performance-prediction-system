from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User, utcnow
from ..queries import iso
from ..schemas import LoginIn, PasswordIn
from ..security import (clear_session_cookie, create_token, current_user, hash_password, set_session_cookie,
                        verify_password)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def user_json(user: User):
    return {
        "id": user.id, "username": user.username, "full_name": user.full_name, "email": user.email,
        "role": user.role, "is_active": user.is_active, "last_login": iso(user.last_login),
        "student_code": user.student.student_code if user.student else None,
    }


@router.post("/login", summary="Sign in and start a session")
def login(body: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == body.username.strip().lower()))
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect username or password.")
    user.last_login = utcnow()
    db.commit()
    set_session_cookie(response, create_token(user))
    return user_json(user)


@router.post("/logout", summary="End the session")
def logout(response: Response):
    clear_session_cookie(response)
    return {"ok": True}


@router.get("/me", summary="The signed-in user")
def me(user: User = Depends(current_user)):
    return user_json(user)


@router.post("/password", summary="Change your password")
def change_password(body: PasswordIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Your current password is incorrect.")
    db_user = db.get(User, user.id)
    db_user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"ok": True}
