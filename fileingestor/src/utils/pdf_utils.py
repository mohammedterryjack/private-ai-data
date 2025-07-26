"""
Shared PDF processing utilities.
"""

import tempfile
import os
from typing import Optional
from pypdf import PdfReader


def extract_text_from_pdf(pdf_data: bytes) -> str:
    """
    Extract text content from PDF bytes.
    
    Args:
        pdf_data: Raw PDF bytes
    
    Returns:
        Extracted text content
    
    Raises:
        Exception: If text extraction fails or no content is found
    """
    print(f"PDF text extraction - Input size: {len(pdf_data)} bytes")
    
    # Create a temporary file for pypdf
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        temp_file.write(pdf_data)
        temp_file_path = temp_file.name
    
    try:
        # Use pypdf to extract text
        reader = PdfReader(temp_file_path)
        print(f"PDF text extraction - Number of pages: {len(reader.pages)}")
        
        # Extract text from all pages
        text_content = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            print(f"PDF text extraction - Page {i+1} text length: {len(page_text) if page_text else 0}")
            if page_text:
                text_content += page_text + "\n\n"
        
        print(f"PDF text extraction - Total extracted text length: {len(text_content)}")
        
        if not text_content.strip():
            print("PDF text extraction - No text content found, this might be a scanned image PDF")
            raise Exception("No text content extracted from PDF - this might be a scanned image PDF")
        
        return text_content
        
    finally:
        # Clean up temporary file
        os.unlink(temp_file_path) 