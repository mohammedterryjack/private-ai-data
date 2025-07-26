"""
Page routes for WebInterface service.

Provides endpoints for serving the main application pages.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
import os

router = APIRouter(tags=["pages"])

@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request) -> FileResponse:
    """Serve the main application page"""
    return FileResponse("static/index.html")

@router.get("/searchpage", response_class=HTMLResponse)
async def searchpage(request: Request) -> FileResponse:
    """Serve the main application page (alias for homepage)"""
    return FileResponse("static/index.html") 