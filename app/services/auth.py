from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import verify_password, get_password_hash
from app.models.user import User, UserRole
from app.schemas.auth import TokenData


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.

    Args:
        data: Data to encode in token
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    print(f"[DEBUG] ===== Token Creation =====")
    print(f"[DEBUG] SECRET_KEY length: {len(settings.SECRET_KEY)}")
    print(f"[DEBUG] SECRET_KEY: {settings.SECRET_KEY}")
    print(f"[DEBUG] SECRET_KEY hex: {settings.SECRET_KEY.encode().hex()}")
    print(f"[DEBUG] ALGORITHM: {settings.ALGORITHM}")
    print(f"[DEBUG] Data to encode: {to_encode}")

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    print(f"[DEBUG] Token created, length: {len(encoded_jwt)}")
    print(f"[DEBUG] Token first 50 chars: {encoded_jwt[:50]}...")
    print(f"[DEBUG] Token last 20 chars: ...{encoded_jwt[-20:]}")
    print(f"[DEBUG] ===== Token Creation End =====")

    return encoded_jwt


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate user with email and password.

    Args:
        db: Database session
        email: User email
        password: Plain password

    Returns:
        User object if authentication successful, None otherwise
    """
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def create_user(db: Session, email: str, password: str, full_name: str, role: UserRole = UserRole.STUDENT) -> User:
    """
    Create a new user.

    Args:
        db: Database session
        email: User email
        password: Plain password
        full_name: User full name
        role: User role (default: student)

    Returns:
        Created user object
    """
    hashed_password = get_password_hash(password)

    user = User(
        email=email,
        password_hash=hashed_password,
        full_name=full_name,
        role=role
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get user by email.

    Args:
        db: Database session
        email: User email

    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.email == email).first()
