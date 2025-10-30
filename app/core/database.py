from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import os

# Check if running in Cloud Run with Unix socket
unix_socket = os.getenv("INSTANCE_UNIX_SOCKET")

if unix_socket:
    # Cloud Run with Cloud SQL Auth Proxy (Unix socket)
    # Format: postgresql://user:password@/database?unix_socket_dir=<path>&unix_socket_name=<instance>
    db_url = f"postgresql://llm_user:anLLMUser123123@/system_llm?unix_socket_dir={unix_socket.rsplit('/', 1)[0]}&unix_socket_name={unix_socket.rsplit('/', 1)[1]}"
else:
    # Local development or direct connection
    db_url = settings.DATABASE_URL

# Create database engine with connection pooling
engine = create_engine(
    db_url,
    pool_pre_ping=True,      # Verify connections before using
    pool_size=5,             # Connection pool size
    max_overflow=10,         # Max overflow connections
    pool_recycle=3600,       # Recycle connections every hour
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
