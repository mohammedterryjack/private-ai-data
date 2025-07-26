"""
WebInterface Service

A FastAPI service providing the web interface for the PrAID platform.
Serves static files and provides the main user interface.
"""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.routes import pages
from typing import Any
import os

app = FastAPI(title="WebInterface", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root() -> FileResponse:
    """Serve the main search page"""
    return FileResponse("static/searchpage.html")

@app.get("/health/")
async def health_check() -> dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "webinterface",
        "message": "Web interface is running"
    }

# Include routers
app.include_router(pages.router)