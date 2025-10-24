"""
Seed script to create the first admin user.

Usage:
    docker exec system-llm-api python -m app.scripts.seed_admin
"""

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash


def create_admin():
    """Create first admin user"""
    db: Session = SessionLocal()

    try:
        # Check if admin already exists
        admin = db.query(User).filter(User.email == "admin@example.com").first()

        if admin:
            print("❌ Admin user already exists!")
            print(f"   Email: {admin.email}")
            print(f"   Role: {admin.role.value}")
            return

        # Create admin user
        admin = User(
            email="admin@example.com",
            password_hash=get_password_hash("admin123"),
            full_name="System Administrator",
            role=UserRole.ADMIN
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("✅ Admin user created successfully!")
        print(f"   Email: {admin.email}")
        print(f"   Password: admin123")
        print(f"   Role: {admin.role.value}")
        print("\n⚠️  IMPORTANT: Change the password after first login!")

    except Exception as e:
        print(f"❌ Error creating admin: {e}")
        db.rollback()

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
