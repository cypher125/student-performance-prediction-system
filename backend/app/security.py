"""Authentication and role-based access control (3.12.4).

Sessions are signed JWTs in an httpOnly, SameSite=Lax cookie, so page scripts cannot
read them and other sites cannot send them; API clients may send the same token as a
Bearer header. Passwords are stored only as Argon2 hashes.
"""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request, Response, status
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import STAFF_ROLES, User
from .settings import get_settings

_hasher = PasswordHash.recommended()
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _hasher.verify(password, password_hash)


def create_token(user: User) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    claims = {"sub": str(user.id), "role": user.role, "iat": now, "exp": now + timedelta(hours=settings.token_hours)}
    return jwt.encode(claims, settings.signing_key(), algorithm=ALGORITHM)


def set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(settings.cookie_name, token, httponly=True, samesite="lax", secure=settings.cookie_secure,
                        max_age=settings.token_hours * 3600, path="/")


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(get_settings().cookie_name, path="/")


def _token_from(request: Request) -> str | None:
    token = request.cookies.get(get_settings().cookie_name)
    if token:
        return token
    header = request.headers.get("Authorization", "")
    return header[7:] if header.lower().startswith("bearer ") else None


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    settings = get_settings()
    token = _token_from(request)
    user = None
    if token:
        try:
            payload = jwt.decode(token, settings.signing_key(), algorithms=[ALGORITHM])
            user = db.get(User, int(payload["sub"]))
        except (jwt.PyJWTError, KeyError, ValueError):
            user = None
    elif settings.demo_auto_login:
        user = db.scalar(select(User).where(User.username == settings.demo_auto_login))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Please sign in.")
    return user


def require_roles(*roles: str):
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have permission to do this.")
        return user

    return dependency


require_staff = require_roles(*STAFF_ROLES)
require_admin = require_roles("admin")
