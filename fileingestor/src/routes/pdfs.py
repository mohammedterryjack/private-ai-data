"""
PDF ingestion routes for the FileIngestor service.
"""

from typing import Any
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from ..client import PDFClient, DatabaseClient
import json
import asyncio
import os

router = APIRouter(prefix="/ingest_pdf", tags=["pdfs"])

async def progress_stream(pdf_data: bytes, filename: str):
    """Stream progress updates during PDF processing"""
    progress_queue = asyncio.Queue()
    
    def progress_callback(stage: str, percent: int):
        """Queue progress update - this will be called from the PDF client"""
        # We need to use asyncio.create_task to avoid blocking
        asyncio.create_task(progress_queue.put({
            "type": "progress",
            "stage": stage,
            "percent": percent
        }))
    
    async def process_pdf_task():
        """Process PDF in background"""
        try:
            pdf_client = PDFClient()
            result = await pdf_client.process_pdf(pdf_data, filename, progress_callback)
            
            # Send final result
            final_response = {
                "type": "complete",
                "status": "success",
                "document_id": result["document_id"],
                "content_length": result["content_length"],
                "keywords": result["keywords"],
                "vector_length": result["vector_length"],
                "structured_json": result.get("structured_json", ""),
                "file_path": result.get("file_path", ""),
                "original_filename": result.get("original_filename", "")
            }
            await progress_queue.put(final_response)
            
        except Exception as e:
            error_response = {
                "type": "error",
                "status": "error",
                "detail": str(e)
            }
            await progress_queue.put(error_response)
    
    # Start PDF processing in background
    asyncio.create_task(process_pdf_task())
    
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
async def ingest_pdf_stream(file: UploadFile = File(...)):
    """Ingest and process a PDF file with real-time progress streaming"""
    try:
        # Enhanced file validation - check both content type and file extension
        content_type = file.content_type or ""
        file_name = file.filename or ""
        
        print(f"PDF validation - Content type: '{content_type}', File name: '{file_name}'")
        
        # Check if it's a PDF by content type or file extension
        is_pdf_by_type = content_type.lower() == 'application/pdf'
        is_pdf_by_extension = file_name.lower().endswith('.pdf')
        
        if not (is_pdf_by_type or is_pdf_by_extension):
            raise HTTPException(
                status_code=400, 
                detail=f"File must be a PDF. Content type: '{content_type}', File name: '{file_name}'"
            )
        
        # Read PDF data
        pdf_data = await file.read()
        print(f"PDF data read, size: {len(pdf_data)} bytes")
        
        return StreamingResponse(
            progress_stream(pdf_data, file.filename),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        print(f"Error in PDF ingestion stream: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF ingestion stream failed: {str(e)}")

@router.get("/file/{document_id}")
async def get_pdf_file(document_id: str):
    """Serve a PDF file by document ID"""
    try:
        # Get file path from database
        db_client = DatabaseClient()
        
        # Query the raw_file_paths table to get the file path
        with db_client.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT file_path, original_filename 
                    FROM raw_file_paths 
                    WHERE uuid = %s
                """, (document_id,))
                
                result = cur.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="PDF file not found")
                
                file_path, original_filename = result
                
                # Check if file exists
                if not os.path.exists(file_path):
                    raise HTTPException(status_code=404, detail="PDF file not found on disk")
                
                # Return the PDF file
                return FileResponse(
                    path=file_path,
                    filename=original_filename or f"{document_id}.pdf",
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f"inline; filename=\"{original_filename or f'{document_id}.pdf'}\"",
                        "Cache-Control": "no-cache",
                        "X-Content-Type-Options": "nosniff"
                    }
                )
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error serving PDF file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to serve PDF file: {str(e)}") 