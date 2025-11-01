from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqladmin import Admin
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.database import engine
from app.api.v1.endpoints import auth, chat, prompt, user, file
from app.middleware import RequestLoggingMiddleware, ErrorLoggingMiddleware
from app.admin.auth import AdminAuthBackend
from app.admin import (
    UserAdmin,
    ModelAdmin,
    PromptAdmin,
    DocumentAdmin,
    DocumentChunkAdmin,
    ChatSessionAdmin,
)
from app.services.file_service import initialize_storage_provider

# Setup logging first
setup_logging()
logger = get_logger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="LLM-based Learning System with RAG capabilities",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add session middleware (required for SQLAdmin authentication)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="admin_session",
    max_age=3600,  # 1 hour
)

# Add logging middleware (order matters - add error logging first)
app.add_middleware(ErrorLoggingMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Required for Server-Sent Events (SSE)
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(chat.router, prefix=settings.API_V1_PREFIX)
app.include_router(prompt.router, prefix=settings.API_V1_PREFIX)
app.include_router(user.router, prefix=settings.API_V1_PREFIX)
app.include_router(file.router, prefix=settings.API_V1_PREFIX)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API status check"""
    return {
        "message": "System LLM API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    from sqlalchemy import text
    from app.core.database import engine

    try:
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            db_version = result.scalar()

            # Check pgvector extension
            result = conn.execute(text(
                "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
            ))
            vector_version = result.scalar()

            # Count tables
            result = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
            ))
            table_count = result.scalar()

        return {
            "status": "healthy",
            "database": {
                "connected": True,
                "postgres_version": db_version.split()[0] if db_version else None,
                "pgvector_version": vector_version,
                "tables_count": table_count
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": {
                "connected": False,
                "error": str(e)
            }
        }

# Setup SQLAdmin
authentication_backend = AdminAuthBackend(secret_key=settings.SECRET_KEY)
admin = Admin(
    app,
    engine,
    title="System LLM Admin",
    base_url="/admin",
    authentication_backend=authentication_backend,
)

# Register admin views
admin.add_view(UserAdmin)
admin.add_view(ModelAdmin)
admin.add_view(PromptAdmin)
admin.add_view(DocumentAdmin)
admin.add_view(DocumentChunkAdmin)
admin.add_view(ChatSessionAdmin)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info(f"🚀 {settings.PROJECT_NAME} is starting...")
    logger.info(f"📝 Documentation available at: http://localhost:8000/docs")
    logger.info(f"🔐 Admin panel available at: http://localhost:8000/admin")
    logger.info(f"🔧 Debug mode: {settings.DEBUG}")

    # Initialize storage provider based on configuration
    try:
        initialize_storage_provider(settings)
        logger.info(f"✅ Storage provider initialized: {settings.STORAGE_TYPE}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize storage provider: {str(e)}")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info(f"👋 {settings.PROJECT_NAME} is shutting down...")
