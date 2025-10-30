from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import os

# Check if running in Cloud Run (use Cloud SQL Connector)
if os.getenv("K_SERVICE"):  # K_SERVICE env var is set in Cloud Run
    from cloud_sql_python_connector import Connector

    connector = Connector()

    def getconn():
        return connector.connect(
            "system-llm:asia-southeast2:system-llm-db",  # format: project:region:instance
            "psycopg2",
            user="llm_user",
            password="anLLMUser123123",
            db="system_llm"
        )

    engine = create_engine(
        "postgresql+psycopg2://",
        creator=getconn,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600,
        echo=settings.DEBUG
    )
else:
    # Local development or direct connection
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600,
        echo=settings.DEBUG   # Log SQL queries in debug mode
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
