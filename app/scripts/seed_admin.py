"""
Seed script to create the first admin user.

Usage:
    docker exec system-llm-api python -m app.scripts.seed_admin

Environment variables (optional):
    ADMIN_EMAIL: Admin email (default: admin@example.com)
    ADMIN_PASSWORD: Admin password (default: admin123)
    ADMIN_FULL_NAME: Admin full name (default: System Administrator)
"""

import os
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash


def create_admin():
    """Create first admin user"""
    db: Session = SessionLocal()

    try:
        # Get admin credentials from environment or use defaults
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com").strip()
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123").strip()
        admin_full_name = os.getenv("ADMIN_FULL_NAME", "System Administrator").strip()

        # Validate admin email
        if not admin_email or "@" not in admin_email:
            print("❌ Invalid admin email format!")
            return

        # Check if admin already exists with same email
        existing_admin = db.query(User).filter(User.email == admin_email).first()

        if existing_admin:
            print("ℹ️  Admin user already exists!")
            print(f"   Email: {existing_admin.email}")
            print(f"   Full Name: {existing_admin.full_name}")
            print(f"   Role: {existing_admin.role.value}")
            print(f"   Created: {existing_admin.created_at}")
            return

        # Check if any admin exists at all
        any_admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if any_admin:
            print("⚠️  Admin user already exists in database!")
            print(f"   Email: {any_admin.email}")
            print(f"   To create additional admin, change ADMIN_EMAIL environment variable")
            return

        # Create admin user
        admin = User(
            email=admin_email,
            password_hash=get_password_hash(admin_password),
            full_name=admin_full_name,
            role=UserRole.ADMIN
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("✅ Admin user created successfully!")
        print(f"   Email: {admin.email}")
        print(f"   Full Name: {admin.full_name}")
        print(f"   Role: {admin.role.value}")
        print("\n⚠️  IMPORTANT: Change the password after first login!")

    except Exception as e:
        print(f"❌ Error creating admin: {e}")
        db.rollback()

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
