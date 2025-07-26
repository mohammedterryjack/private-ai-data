"""
LLM Agent Service

A FastAPI service for LLM operations using Ollama.
Provides text generation, embeddings, vision, and RAG capabilities.
"""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Any
from src.llm_service import check_ollama_health
from src.routes import vector, vision, rag, structure

app = FastAPI(title="LLMAgent", version="1.0.0")

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
    return await check_ollama_health()

# Include routers with new prefixes
app.include_router(vector.router, prefix="/vector")
app.include_router(vision.router, prefix="/image")
app.include_router(rag.router, prefix="/rag")
app.include_router(structure.router, prefix="/structure") 