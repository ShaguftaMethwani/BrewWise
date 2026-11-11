from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from brewwise.db.session import get_db
from brewwise.models.user import UserModel
from brewwise.services.auth.jwt_service import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_user_optional
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: str

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check if email exists
    stmt = select(UserModel).where(UserModel.email == req.email.lower())
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    pwd_hash, salt = hash_password(req.password)
    user = UserModel(
        email=req.email.lower(),
        display_name=req.display_name.strip(),
        password_hash=pwd_hash,
        salt=salt
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user_id=user.id, email=user.email)
    return AuthResponse(
        token=token,
        user=UserResponse(id=user.id, email=user.email, display_name=user.display_name)
    )


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(UserModel).where(UserModel.email == req.email.lower())
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not verify_password(req.password, user.password_hash, user.salt):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token(user_id=user.id, email=user.email)
    return AuthResponse(
        token=token,
        user=UserResponse(id=user.id, email=user.email, display_name=user.display_name)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: UserModel = Depends(get_current_user)):
    return UserResponse(id=user.id, email=user.email, display_name=user.display_name)
