from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services import auth as auth_service
from app.schemas.auth import UserRegister, UserLogin, Token
from app.schemas.user import UserResponse
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new student user.

    - **email**: Valid email address
    - **password**: Minimum 8 characters
    - **full_name**: User's full name
    """
    # Check if email already exists
    existing_user = auth_service.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user (auto-assigned as student)
    user = auth_service.create_user(
        db=db,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name
    )

    return user


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with email and password to get JWT access token.

    - **email**: User email address
    - **password**: User password

    Returns JWT access token valid for 1 day (24 hours).
    """
    # Authenticate user
    user = auth_service.authenticate_user(db, login_data.email, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = auth_service.create_access_token(
        data={
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role.value
        }
    )

    print(f"[DEBUG] [Login] Returning token to client:")
    print(f"[DEBUG] [Login] Token type: {type(access_token)}")
    print(f"[DEBUG] [Login] Token length: {len(access_token)}")
    print(f"[DEBUG] [Login] Token first 50 chars: {access_token[:50]}...")
    print(f"[DEBUG] [Login] Token last 20 chars: ...{access_token[-20:]}")

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.

    Requires valid JWT token in Authorization header.
    """
    return current_user
