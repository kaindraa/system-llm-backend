from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,      # Verify connections before using
    pool_size=20,            # Connection pool size (increased from 5)
    max_overflow=40,         # Max overflow connections (increased from 10)
    pool_recycle=3600,       # Recycle connections every hour
    pool_timeout=60,         # Timeout 60 seconds (increased from 30)
    connect_args={
        "connect_timeout": 10,
    },
    echo=settings.DEBUG      # Log SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI routes
def get_db():
    """
    Database session dependency.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
