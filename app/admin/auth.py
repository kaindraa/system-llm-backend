from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth import authenticate_user
from app.models.user import UserRole
from app.core.logging import get_logger

logger = get_logger(__name__)


class AdminAuthBackend(AuthenticationBackend):
    """
    Authentication backend for SQLAdmin
    Only allows users with ADMIN role to access the admin panel
    """

    async def login(self, request: Request) -> bool:
        """
        Handle login to admin panel

        Args:
            request: Starlette request object with form data

        Returns:
            bool: True if login successful, False otherwise
        """
        form = await request.form()
        email = form.get("username")  # SQLAdmin uses 'username' field
        password = form.get("password")

        if not email or not password:
            return False

        # Get database session
        db: Session = next(get_db())

        try:
            # Authenticate user
            user = authenticate_user(db, email, password)

            if not user:
                logger.warning(f"Failed admin login attempt for email: {email}")
                return False

            # Check if user is admin
            if user.role != UserRole.ADMIN:
                logger.warning(
                    f"Non-admin user {email} attempted to access admin panel"
                )
                return False

            # Set session
            request.session.update({
                "user_id": str(user.id),
                "email": user.email,
                "role": user.role.value,
            })

            logger.info(f"Admin user {email} logged into admin panel")
            return True

        except Exception as e:
            logger.error(f"Error during admin login: {str(e)}")
            return False
        finally:
            db.close()

    async def logout(self, request: Request) -> bool:
        """
        Handle logout from admin panel

        Args:
            request: Starlette request object

        Returns:
            bool: Always True
        """
        email = request.session.get("email", "unknown")
        request.session.clear()
        logger.info(f"Admin user {email} logged out from admin panel")
        return True

    async def authenticate(self, request: Request) -> bool:
        """
        Check if user is authenticated and has admin role

        Args:
            request: Starlette request object

        Returns:
            bool: True if authenticated as admin, False otherwise
        """
        user_id = request.session.get("user_id")
        role = request.session.get("role")

        if not user_id or role != UserRole.ADMIN.value:
            return False

        return True
