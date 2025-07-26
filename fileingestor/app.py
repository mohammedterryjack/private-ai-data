"""
FileIngestor Service

A FastAPI service for ingesting and processing files.
Provides endpoints for file upload and processing.
"""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Any

from src.routes import images_router, pdfs_router

app = FastAPI(title="FileIngestor", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(images_router)
app.include_router(pdfs_router)

@app.get("/")
async def root() -> RedirectResponse:
    """Redirect to API documentation"""
    return RedirectResponse(url="/docs")

@app.get("/health/")
async def health_check() -> dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "fileingestor",
        "message": "File ingestor service is running"
    } 