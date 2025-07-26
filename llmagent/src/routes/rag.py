"""
RAG routes for LLM Agent service.

Provides endpoints for Retrieval Augmented Generation with streaming support.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Any
from src.llm_service import rag_query_stream
from src.schemas import RAGRequest
import json

router = APIRouter(prefix="", tags=["rag"])

@router.post("/")
async def rag_stream_endpoint(request: RAGRequest) -> StreamingResponse:
    """RAG: Retrieval Augmented Generation with streaming response"""
    try:
        async def generate_stream():
            async for chunk in rag_query_stream(request.query, request.sources):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        
        return StreamingResponse(
            generate_stream(), 
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 