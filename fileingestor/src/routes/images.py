"""
Image ingestion routes for the FileIngestor service.
"""

from typing import Any
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from ..client import ImageClient
import json
import asyncio

router = APIRouter(prefix="/ingest_image", tags=["images"])

async def progress_stream(image_data: bytes):
    """Stream progress updates during image processing"""
    progress_queue = asyncio.Queue()
    
    def progress_callback(stage: str, percent: int):
        """Queue progress update - this will be called from the image client"""
        # We need to use asyncio.create_task to avoid blocking
        asyncio.create_task(progress_queue.put({
            "type": "progress",
            "stage": stage,
            "percent": percent
        }))
    
    async def process_image_task():
        """Process image in background"""
        try:
            image_client = ImageClient()
            result = await image_client.process_image(image_data, progress_callback)
            
            # Send final result
            final_response = {
                "type": "complete",
                "status": "success",
                "image_id": result["image_id"],
                "caption": result["caption"],
                "ocr_text": result["ocr_text"],
                "keywords": result["keywords"],
                "vector_length": result["vector_length"]
            }
            await progress_queue.put(final_response)
            
        except Exception as e:
            error_response = {
                "type": "error",
                "status": "error",
                "detail": str(e)
            }
            await progress_queue.put(error_response)
    
    # Start image processing in background
    asyncio.create_task(process_image_task())
    
    # Stream progress updates as they arrive
    while True:
        try:
            update = await asyncio.wait_for(progress_queue.get(), timeout=300.0)  # 5 minute timeout
            yield f"data: {json.dumps(update)}\n\n"
            
            # Stop streaming if we get a final result
            if update.get("type") in ["complete", "error"]:
                break
                
        except asyncio.TimeoutError:
            # Send timeout error
            timeout_response = {
                "type": "error",
                "status": "error",
                "detail": "Processing timeout"
            }
            yield f"data: {json.dumps(timeout_response)}\n\n"
            break

@router.post("/stream/")
async def ingest_image_stream(file: UploadFile = File(...)):
    """Ingest and process an image file with real-time progress streaming"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await file.read()
        print(f"Image data read, size: {len(image_data)} bytes")
        
        return StreamingResponse(
            progress_stream(image_data),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        print(f"Error in image ingestion stream: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Image ingestion stream failed: {str(e)}")

