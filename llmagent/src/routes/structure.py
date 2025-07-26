"""
Structure extraction route for LLM Agent service.

Provides an endpoint to convert raw text into a structured JSON format.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Any
from src.llm_service import structure_text, structure_text_stream
from src.schemas import TextRequest
import json

router = APIRouter(prefix="", tags=["structure"])

@router.post("/")
async def structure_text_endpoint(request: TextRequest) -> dict[str, Any]:
    """Extract structured JSON from raw text using LLM"""
    try:
        return await structure_text(request.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream/")
async def structure_text_stream_endpoint(request: TextRequest):
    """Extract structured JSON from raw text using LLM with streaming response"""
    try:
        async def generate_stream():
            async for chunk in structure_text_stream(request.text):
                # Format as Server-Sent Events
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 