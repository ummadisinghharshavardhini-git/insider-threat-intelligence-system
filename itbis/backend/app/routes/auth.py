from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import bcrypt

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserLogin


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    return bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password: str, stored_password: str) -> bool:
    # New bcrypt password
    if stored_password.startswith(("$2a$", "$2b$", "$2y$")):
        return bcrypt.checkpw(
            password.encode("utf-8"),
            stored_password.encode("utf-8")
        )

    # Existing old plain-text password
    return stored_password == password


@router.post("/register")
def register(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    new_user = User(
        email=user.email,
        password=hash_password(user.password),
        role="employee"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "email": new_user.email,
        "role": new_user.role
    }


@router.post("/login")
def login(
    user: UserLogin,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        user.password,
        existing_user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Upgrade old plain-text password to bcrypt
    if not existing_user.password.startswith(
        ("$2a$", "$2b$", "$2y$")
    ):
        existing_user.password = hash_password(user.password)
        db.commit()

    return {
        "message": "Login successful",
        "email": existing_user.email,
        "role": existing_user.role
    }
