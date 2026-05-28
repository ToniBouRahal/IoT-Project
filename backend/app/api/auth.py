from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import create_access_token, get_current_user
from app.database import get_db
from app.models import User
from app.schemas.auth import LoginRequest, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/login", response_model=TokenOut)
async def login(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if user is None or not pwd_context.verify(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    token = create_access_token(user.email)
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
