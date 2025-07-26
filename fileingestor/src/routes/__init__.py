# Routes package for FileIngestor service

from .images import router as images_router
from .pdfs import router as pdfs_router

__all__ = ["images_router", "pdfs_router"]
