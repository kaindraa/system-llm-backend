from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserRole
from app.services.llm import LLMService

# HTTP Bearer scheme for JWT token
security = HTTPBearer()


def get_llm_service(request: Request) -> LLMService:
    """Get singleton LLM service from app state."""
    return request.app.state.llm_service


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.

    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    print(f"[DEBUG] [get_current_user] Credentials scheme: {credentials.scheme}")
    print(f"[DEBUG] [get_current_user] Credentials type: {type(credentials)}")

    try:
        # Decode JWT token
        token = credentials.credentials
        print(f"[DEBUG] ===== JWT Verification Start =====")
        print(f"[DEBUG] Token length: {len(token)}")
        print(f"[DEBUG] Token first 50 chars: {token[:50]}...")
        print(f"[DEBUG] Token last 20 chars: ...{token[-20:]}")
        print(f"[DEBUG] SECRET_KEY length: {len(settings.SECRET_KEY)}")
        print(f"[DEBUG] SECRET_KEY: {settings.SECRET_KEY}")
        print(f"[DEBUG] SECRET_KEY hex: {settings.SECRET_KEY.encode().hex()}")
        print(f"[DEBUG] ALGORITHM: {settings.ALGORITHM}")

        # Try to decode without verification first to inspect payload
        try:
            unverified_payload = jwt.get_unverified_claims(token)
            print(f"[DEBUG] Unverified payload: {unverified_payload}")
        except Exception as e:
            print(f"[DEBUG] Could not decode unverified payload: {str(e)}")

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        print(f"[DEBUG] Token decoded successfully. Payload: {payload}")
        user_id: str = payload.get("user_id")

        if user_id is None:
            print(f"[DEBUG] No user_id in token payload")
            raise credentials_exception

    except JWTError as e:
        print(f"[DEBUG] JWTError: {str(e)}")
        print(f"[DEBUG] JWTError type: {type(e).__name__}")
        print(f"[DEBUG] ===== JWT Verification Failed =====")
        raise credentials_exception

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to require admin role.

    Raises:
        HTTPException 403: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user


async def get_current_student(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to require student role.

    Raises:
        HTTPException 403: If user is not a student
    """
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required"
        )

    return current_user
