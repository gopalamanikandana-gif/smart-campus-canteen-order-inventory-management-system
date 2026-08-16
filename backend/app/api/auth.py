from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..auth import create_access_token, get_current_user, hash_password, verify_password
from ..database import get_db
from ..models import User
from ..schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    email = request.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        name=request.name.strip(),
        email=email,
        password_hash=hash_password(request.password),
        role="STUDENT",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenResponse(access_token=create_access_token(user), user=user)


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email.lower()).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return TokenResponse(access_token=create_access_token(user), user=user)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user
