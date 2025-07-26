"""
Vector routes for LLM Agent service.

Provides endpoints for text-to-vector conversion using embeddings.
"""

from fastapi import APIRouter, HTTPException
from typing import Any
from src.llm_service import text_to_vector
from src.schemas import TextRequest

router = APIRouter(prefix="", tags=["vector"])

@router.post("/")
async def text_to_vector_endpoint(request: TextRequest) -> dict[str, Any]:
    """Convert text to semantic vector using Ollama (all-minilm model)"""
    try:
        return await text_to_vector(request.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 