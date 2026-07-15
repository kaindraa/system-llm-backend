from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,      # Verify connections before using
    # Two Fly processes share a Supabase Session Pooler limited to 15 client
    # sessions. Each process may use at most five, leaving capacity for a
    # release migration and Supabase-managed clients.
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_recycle=3600,       # Recycle connections every hour
    pool_timeout=settings.DATABASE_POOL_TIMEOUT_SECONDS,
    connect_args={
        "connect_timeout": 10,
    },
    # Keep SQL echo disabled in-app; production request latency is more important
    # than verbose query logging, and logger-based diagnostics remain available.
    echo=False
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
