from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services import auth as auth_service
from app.schemas.auth import UserRegister, UserLogin, Token
from app.schemas.user import UserResponse, UserProfileUpdate
from app.models.user import User
from app.core.logging import get_logger

logger = get_logger(__name__)

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
    Returns user profile including task, persona, and mission_objective.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's learning profile.

    Allows user to update:
    - **task**: Learning task or current focus
    - **persona**: Preferred AI persona/role
    - **mission_objective**: Learning goal or objective

    All fields are optional. Omitted fields are not updated.
    """
    try:
        # Get the user from database
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update fields if provided
        if profile_update.task is not None:
            user.task = profile_update.task
            logger.info(f"Updated task for user {user.id}")

        if profile_update.persona is not None:
            user.persona = profile_update.persona
            logger.info(f"Updated persona for user {user.id}")

        if profile_update.mission_objective is not None:
            user.mission_objective = profile_update.mission_objective
            logger.info(f"Updated mission_objective for user {user.id}")

        # Save changes
        db.commit()
        db.refresh(user)

        logger.info(f"User profile updated: {user.id}")
        return user

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user profile: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user profile: {str(e)}"
        )
