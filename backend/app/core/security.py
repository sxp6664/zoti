"""Auth + RBAC.

`create_token` mints a JWT carrying the user's role. `require_roles(...)`
returns a FastAPI dependency that rejects any request whose token role
isn't in the allowed set — this is the single enforcement point for
role-based access control across the API.
"""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from app.core.config import settings
from app.models import Role

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(p: str) -> str:
    return pwd.hash(p)


def verify_password(p: str, hashed: str) -> bool:
    return pwd.verify(p, hashed)


def create_token(sub: str, role: str) -> str:
    payload = {
        "sub": sub,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MIN),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def current_claims(token: str = Depends(oauth2)) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token")


def require_roles(*allowed: Role):
    allowed_set = {r.value for r in allowed}

    def checker(claims: dict = Depends(current_claims)) -> dict:
        if claims.get("role") not in allowed_set:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "insufficient role")
        return claims

    return checker
