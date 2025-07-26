"""
EasyOCR Service

A FastAPI service for extracting text from images using EasyOCR.
Provides a simple endpoint for OCR text extraction.
"""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Any
import easyocr
import asyncio

from src.routes import ocr_router

app = FastAPI(title="EasyOCR", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global reader instance
reader = None

@app.on_event("startup")
async def startup_event():
    """Pre-download EasyOCR models on startup"""
    global reader
    print("Starting EasyOCR service...")
    print("Pre-downloading EasyOCR models...")
    
    try:
        # Initialize the reader with English language
        # This will download the models if they don't exist
        reader = easyocr.Reader(lang_list=["en"], gpu=False)
        print("✅ EasyOCR models downloaded and initialized successfully!")
        print("Service is ready to process OCR requests.")
    except Exception as e:
        print(f"❌ Failed to initialize EasyOCR models: {str(e)}")
        raise e

# Include routers
app.include_router(ocr_router)

@app.get("/")
async def root() -> RedirectResponse:
    """Redirect to API documentation"""
    return RedirectResponse(url="/docs")

@app.get("/health/")
async def health_check() -> dict[str, Any]:
    """Health check endpoint"""
    global reader
    status = "healthy" if reader is not None else "initializing"
    return {
        "status": status,
        "service": "easyocr",
        "message": "EasyOCR service is running" if reader is not None else "EasyOCR service is initializing models",
        "models_ready": reader is not None
    } 