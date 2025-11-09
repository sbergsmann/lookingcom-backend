"""FastAPI application entry point"""

import logfire
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.api.v1.router import api_router

settings = get_settings()

# Configure Logfire
if settings.logfire_api_key:
    logfire.configure(
        token=settings.logfire_api_key,
        service_name=settings.app_name,
        service_version=settings.app_version,
    )
    # Instrument httpx for external API calls logging
    logfire.instrument_httpx()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FastAPI wrapper for CapCorn Hotel API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Instrument FastAPI with Logfire (logs all requests, responses, and bodies)
if settings.logfire_api_key:
    logfire.instrument_fastapi(
        app,
        capture_headers=True,
        request_attributes_mapper=lambda request, attributes: {
            **attributes,
            "custom.path": request.url.path,
            "custom.method": request.method,
        },
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/", tags=["health"])
async def root():
    """Root endpoint - health check"""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}
