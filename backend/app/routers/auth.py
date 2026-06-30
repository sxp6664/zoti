"""Login → JWT. Seeded users live in seed.py."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import create_token, verify_password
from app.models import User
from app.schemas import LoginIn, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(401, "bad credentials")
    token = create_token(sub=user.email, role=user.role.value)
    return TokenOut(access_token=token, role=user.role.value)
