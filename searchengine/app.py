"""
SearchEngine Service

A FastAPI service for semantic document search and retrieval.
Provides hybrid search combining keyword matching and semantic similarity.
"""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Any
from src.search_service import get_health_status
from src.routes import search

app = FastAPI(title="SearchEngine", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root() -> RedirectResponse:
    """Redirect to API documentation"""
    return RedirectResponse(url="/docs")

@app.get("/health/")
async def health_check() -> dict[str, Any]:
    """Health check endpoint"""
    return await get_health_status()

# Include routers
app.include_router(search.router) 