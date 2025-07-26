"""
Vision routes for LLM Agent service.

Provides endpoints for image analysis and description using vision models.
"""

from fastapi import APIRouter, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
from typing import Any
from src.llm_service import describe_image_from_file_stream
import json

router = APIRouter(prefix="", tags=["vision"])

@router.post("/describe/stream")
async def describe_image_stream_endpoint(file: UploadFile = File(...)):
    """Create a caption for an image using Ollava (llava model) with streaming response"""
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read file bytes directly
        file_content = await file.read()
        
        async def generate_stream():
            async for chunk in describe_image_from_file_stream(file_content):
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