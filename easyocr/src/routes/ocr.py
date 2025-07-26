"""
OCR routes for the EasyOCR service.
"""

from typing import Any
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import easyocr
import logging
from PIL import Image
import io
import tempfile
import os

router = APIRouter(prefix="/ocr", tags=["ocr"])

def get_reader():
    """Get the global EasyOCR reader instance"""
    from app import reader
    if reader is None:
        raise HTTPException(
            status_code=503, 
            detail="EasyOCR models are still initializing. Please try again in a moment."
        )
    return reader

@router.post("/extract-text/")
async def extract_text_from_image(file: UploadFile = File(...)):
    """Extract text from an uploaded image using EasyOCR"""
    try:
        # Validate file type
        content_type = file.content_type or ""
        file_name = file.filename or ""
        
        print(f"OCR validation - Content type: '{content_type}', File name: '{file_name}'")
        
        # Check if it's an image by content type or file extension
        valid_image_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff', 'image/webp']
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
        
        is_image_by_type = content_type.lower() in valid_image_types
        is_image_by_extension = any(file_name.lower().endswith(ext) for ext in valid_extensions)
        
        if not (is_image_by_type or is_image_by_extension):
            raise HTTPException(
                status_code=400, 
                detail=f"File must be an image. Content type: '{content_type}', File name: '{file_name}'"
            )
        
        # Read image data
        image_data = await file.read()
        print(f"Image data read, size: {len(image_data)} bytes")
        
        # Create temporary file for the image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(image_data)
            temp_file_path = temp_file.name
        
        try:
            # Get EasyOCR reader (global instance)
            ocr_reader = get_reader()
            
            # Extract text using EasyOCR with confidence filtering
            print(f"Using EasyOCR to extract text from: {file_name}")
            result = ocr_reader.readtext(temp_file_path)
            
            # Extract text with confidence filtering and proper line breaks
            extracted_text = "\n".join(chunk for _, chunk, confidence in result if confidence > 0.1)
            
            # Get all confidence scores for response
            confidence_scores = [float(confidence) for _, _, confidence in result]
            
            print(f"OCR extraction complete. Text length: {len(extracted_text)}")
            print(f"First 200 characters: {extracted_text[:200]}")
            
            return JSONResponse({
                "status": "success",
                "filename": file_name,
                "text_length": len(extracted_text),
                "extracted_text": extracted_text,
                "confidence_scores": confidence_scores,
                "method": "easyocr"
            })
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                print(f"Cleaned up temporary file: {temp_file_path}")
        
    except Exception as e:
        print(f"Error in OCR text extraction: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"OCR text extraction failed: {str(e)}") 