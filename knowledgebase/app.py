"""
KnowledgeBase Service

A FastAPI service for managing structured data storage with PostgreSQL.
Provides endpoints for storing and querying images, captions, markdown, keywords, sources, and vectors.
"""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Any
from src.database import init_database, get_health_status
from src.routes import tables

app = FastAPI(title="KnowledgeBase", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event() -> None:
    """Initialize database on startup"""
    await init_database()

@app.get("/")
async def root() -> RedirectResponse:
    """Redirect to API documentation"""
    return RedirectResponse(url="/docs")

@app.get("/health/")
async def health_check() -> dict[str, Any]:
    """Health check endpoint with database status"""
    return await get_health_status()

# Include routers
app.include_router(tables.router) 