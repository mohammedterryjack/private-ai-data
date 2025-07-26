"""
Client classes for external service interactions.
"""

import httpx
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import uuid
from fastapi import HTTPException
import base64
import io
from PIL import Image
import json
import traceback
from typing import Dict, Any, Callable, Optional

class EasyOCRClient:
    """Client for EasyOCR service interactions."""
    
    def __init__(self):
        self.easyocr_url = os.getenv("EASYOCR_URL")
        if not self.easyocr_url:
            raise ValueError("EASYOCR_URL environment variable is not set")
    
    async def extract_text_from_image(self, image_data: bytes) -> str:
        """Extract text from image using EasyOCR service"""
        try:
            async with httpx.AsyncClient() as client:
                # Create a file-like object
                files = {"file": ("image.jpg", image_data, "image/jpeg")}
                
                response = await client.post(
                    f"{self.easyocr_url}/ocr/extract-text/",
                    files=files,
                    timeout=120.0  # 2 minute timeout for OCR
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("extracted_text", "")
                else:
                    raise HTTPException(
                        status_code=response.status_code, 
                        detail=f"EasyOCR service returned error: {response.text}"
                    )
        except httpx.ConnectError as e:
            raise HTTPException(
                status_code=503, 
                detail=f"Failed to connect to EasyOCR service at {self.easyocr_url}: {str(e)}"
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504, 
                detail="EasyOCR service request timed out after 2 minutes"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502, 
                detail=f"Request to EasyOCR service failed: {str(e)}"
            )

class LLMClient:
    """Client for LLM agent interactions."""
    
    def __init__(self):
        self.llm_agent_url = os.getenv("LLM_AGENT_URL")
        if not self.llm_agent_url:
            raise ValueError("LLM_AGENT_URL environment variable is not set")
    
    async def get_image_caption(self, image_b64: str) -> str:
        """Get image caption from LLM agent"""
        try:
            async with httpx.AsyncClient() as client:
                # Convert base64 back to bytes and send as file
                # Decode base64 to bytes
                image_bytes = base64.b64decode(image_b64)
                
                # Create a file-like object
                files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
                
                response = await client.post(
                    f"{self.llm_agent_url}/image/describe",
                    files=files,
                    timeout=300.0  # Increased timeout to 5 minutes for image processing
                )
                if response.status_code == 200:
                    data = response.json()
                    # Combine description and text_in_image for a complete caption
                    description = data.get("description", "")
                    text_in_image = data.get("text_in_image", "")
                    if text_in_image:
                        return f"{description} Text in image: {text_in_image}"
                    return description
                else:
                    raise HTTPException(
                        status_code=response.status_code, 
                        detail=f"LLM agent returned error: {response.text}"
                    )
        except httpx.ConnectError as e:
            raise HTTPException(
                status_code=503, 
                detail=f"Failed to connect to LLM agent at {self.llm_agent_url}: {str(e)}"
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504, 
                detail="LLM agent request timed out after 5 minutes"
            )
        except httpx.ReadTimeout:
            raise HTTPException(
                status_code=504, 
                detail="LLM agent read timeout - image processing took too long"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502, 
                detail=f"Request to LLM agent failed: {str(e)}"
            )

    async def get_text_vector(self, text: str) -> list[float]:
        """Get vector representation of text from LLM agent"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.llm_agent_url}/vector/",
                    json={"text": text},
                    timeout=120.0  # Increased timeout for vector generation
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("vector", [])
                else:
                    raise HTTPException(
                        status_code=response.status_code, 
                        detail=f"LLM agent returned error: {response.text}"
                    )
        except httpx.ConnectError as e:
            raise HTTPException(
                status_code=503, 
                detail=f"Failed to connect to LLM agent at {self.llm_agent_url}: {str(e)}"
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504, 
                detail="LLM agent request timed out after 2 minutes"
            )
        except httpx.ReadTimeout:
            raise HTTPException(
                status_code=504, 
                detail="LLM agent read timeout - vector generation took too long"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502, 
                detail=f"Request to LLM agent failed: {str(e)}"
            )

    async def get_image_caption_stream(self, image_b64: str):
        """Get image caption from LLM agent with streaming response"""
        try:
            async with httpx.AsyncClient() as client:
                # Convert base64 back to bytes and send as file
                image_bytes = base64.b64decode(image_b64)
                
                # Create a file-like object
                files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
                
                async with client.stream(
                    "POST",
                    f"{self.llm_agent_url}/image/describe/stream",
                    files=files,
                    timeout=300.0
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.startswith('data: '):
                                try:
                                    data = json.loads(line[6:])
                                    if data.get('content'):
                                        yield data['content']
                                except json.JSONDecodeError:
                                    continue
                    else:
                        raise HTTPException(
                            status_code=response.status_code, 
                            detail=f"LLM agent returned error: {response.text}"
                        )
        except httpx.ConnectError as e:
            raise HTTPException(
                status_code=503, 
                detail=f"Failed to connect to LLM agent at {self.llm_agent_url}: {str(e)}"
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504, 
                detail="LLM agent request timed out after 5 minutes"
            )
        except httpx.ReadTimeout:
            raise HTTPException(
                status_code=504, 
                detail="LLM agent read timeout - image processing took too long"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502, 
                detail=f"Request to LLM agent failed: {str(e)}"
            )

    async def structure_text(self, text: str) -> dict:
        """Get structured JSON from text using LLM agent"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.llm_agent_url}/structure/",
                    json={"text": text},
                    timeout=120.0
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    raise HTTPException(
                        status_code=response.status_code, 
                        detail=f"LLM agent returned error: {response.text}"
                    )
        except httpx.ConnectError as e:
            raise HTTPException(
                status_code=503, 
                detail=f"Failed to connect to LLM agent at {self.llm_agent_url}: {str(e)}"
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504, 
                detail="LLM agent request timed out after 2 minutes"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502, 
                detail=f"Request to LLM agent failed: {str(e)}"
            )

    async def structure_text_stream(self, text: str):
        """Get structured JSON from text using LLM agent with streaming response"""
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.llm_agent_url}/structure/stream/",
                    json={"text": text},
                    timeout=300.0
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.startswith('data: '):
                                try:
                                    data = json.loads(line[6:])
                                    if data.get('content'):
                                        yield data['content']
                                except json.JSONDecodeError:
                                    continue
                    else:
                        raise HTTPException(
                            status_code=response.status_code, 
                            detail=f"LLM agent returned error: {response.text}"
                        )
        except httpx.ConnectError as e:
            raise HTTPException(
                status_code=503, 
                detail=f"Failed to connect to LLM agent at {self.llm_agent_url}: {str(e)}"
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504, 
                detail="LLM agent request timed out after 5 minutes"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502, 
                detail=f"Request to LLM agent failed: {str(e)}"
            )


class DatabaseClient:
    """Client for database interactions."""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is not set")
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.database_url)
    
    def store_image_data(self, image_id: str, image_b64: str, caption: str, vector: list[float], keywords: list[str]):
        """Store image data in database using the knowledgebase schema"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Store image in images table
                    cur.execute("""
                        INSERT INTO images (uuid, content)
                        VALUES (%s, %s)
                        ON CONFLICT (uuid) DO UPDATE SET
                            content = EXCLUDED.content,
                            updated_at = NOW()
                    """, (image_id, image_b64))
                    
                    # Store caption in captions table
                    cur.execute("""
                        INSERT INTO captions (uuid, content)
                        VALUES (%s, %s)
                        ON CONFLICT (uuid) DO UPDATE SET
                            content = EXCLUDED.content,
                            updated_at = NOW()
                    """, (image_id, caption))
                    
                    # Store vector in vectors table using pgvector
                    if not vector or len(vector) == 0:
                        print(f"Warning: Empty vector for image {image_id}, skipping vector storage")
                    else:
                        # Convert list to proper vector format for pgvector
                        vector_str = f"[{','.join(map(str, vector))}]"
                        
                        cur.execute("""
                            INSERT INTO vectors (uuid, embedding)
                            VALUES (%s, %s::vector)
                            ON CONFLICT (uuid) DO UPDATE SET
                                embedding = EXCLUDED.embedding,
                                updated_at = NOW()
                        """, (image_id, vector_str))
                    
                    # Store keywords in keywords table
                    for keyword in keywords:
                        cur.execute("""
                            INSERT INTO keywords (keyword, uuids)
                            VALUES (%s, ARRAY[%s]::UUID[])
                            ON CONFLICT (keyword) DO UPDATE SET
                                uuids = array_append(keywords.uuids, EXCLUDED.uuids[1]),
                                updated_at = NOW()
                        """, (keyword, image_id))
                    
                    conn.commit()
                    print(f"Image data stored successfully for ID: {image_id}")
                    
        except Exception as e:
            print(f"Database error: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to store image data: {str(e)}"
            )
    
    def get_image_data(self, image_id: str) -> dict:
        """Get image data from database"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Get image data
                    cur.execute("""
                        SELECT uuid, content, created_at, updated_at
                        FROM images WHERE uuid = %s
                    """, (image_id,))
                    
                    image_result = cur.fetchone()
                    if not image_result:
                        raise HTTPException(
                            status_code=404, 
                            detail=f"Image with ID {image_id} not found"
                        )
                    
                    # Get caption
                    cur.execute("""
                        SELECT content FROM captions WHERE uuid = %s
                    """, (image_id,))
                    
                    caption_result = cur.fetchone()
                    caption = caption_result['content'] if caption_result else ""
                    
                    # Get vector
                    cur.execute("""
                        SELECT embedding FROM vectors WHERE uuid = %s
                    """, (image_id,))
                    
                    vector_result = cur.fetchone()
                    vector = vector_result['embedding'] if vector_result else []
                    
                    # Get keywords
                    cur.execute("""
                        SELECT keyword FROM keywords WHERE %s = ANY(uuids)
                    """, (image_id,))
                    
                    keyword_results = cur.fetchall()
                    keywords = [row['keyword'] for row in keyword_results]
                    
                    return {
                        "uuid": image_result['uuid'],
                        "image_data": image_result['content'],
                        "caption": caption,
                        "keywords": keywords,
                        "vector": vector,
                        "created_at": image_result['created_at'],
                        "updated_at": image_result['updated_at']
                    }
                        
        except HTTPException:
            raise
        except Exception as e:
            print(f"Database error: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to retrieve image data: {str(e)}"
            )
    
    def list_images(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """List images from database"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT uuid, content, created_at, updated_at
                        FROM images
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    """, (limit, offset))
                    
                    results = cur.fetchall()
                    return [dict(row) for row in results]
                    
        except Exception as e:
            print(f"Database error: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to list images: {str(e)}"
            )
    
    def delete_image(self, image_id: str):
        """Delete image from database"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Delete from all related tables
                    cur.execute("DELETE FROM images WHERE uuid = %s", (image_id,))
                    cur.execute("DELETE FROM captions WHERE uuid = %s", (image_id,))
                    cur.execute("DELETE FROM vectors WHERE uuid = %s", (image_id,))
                    
                    # Remove from keywords table
                    cur.execute("""
                        UPDATE keywords 
                        SET uuids = array_remove(uuids, %s)
                        WHERE %s = ANY(uuids)
                    """, (image_id, image_id))
                    
                    conn.commit()
                    print(f"Image deleted successfully: {image_id}")
                    
        except Exception as e:
            print(f"Database error: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to delete image: {str(e)}"
            )
    
    async def save_document(self, document_id: str, content: str, keywords: list[str], vector_embedding: list[float]):
        """Store document data in database using the knowledgebase schema"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Store document content in documents table (using uuid for consistency)
                    cur.execute("""
                        INSERT INTO documents (uuid, content)
                        VALUES (%s, %s)
                    """, (document_id, content))
                    
                    # Validate and format vector for pgvector
                    if not vector_embedding or len(vector_embedding) == 0:
                        print(f"Warning: Empty vector for document {document_id}, skipping vector storage")
                    else:
                        # Convert list to proper vector format for pgvector
                        vector_str = f"[{','.join(map(str, vector_embedding))}]"
                        
                        # Store vector in vectors table using pgvector
                        cur.execute("""
                            INSERT INTO vectors (uuid, embedding)
                            VALUES (%s, %s::vector)
                            ON CONFLICT (uuid) DO UPDATE SET
                                embedding = EXCLUDED.embedding,
                                updated_at = NOW()
                        """, (document_id, vector_str))
                    
                    # Store keywords in keywords table
                    for keyword in keywords:
                        cur.execute("""
                            INSERT INTO keywords (keyword, uuids)
                            VALUES (%s, ARRAY[%s]::UUID[])
                            ON CONFLICT (keyword) DO UPDATE SET
                                uuids = array_append(keywords.uuids, EXCLUDED.uuids[1]),
                                updated_at = NOW()
                        """, (keyword, document_id))
                    
                    conn.commit()
                    print(f"Document data stored successfully for ID: {document_id}")
                    
        except Exception as e:
            print("Error in save_document:", e)
            traceback.print_exc()
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to store document data: {str(e)}"
            )
    
    async def save_raw_file_path(self, document_id: str, file_path: str, original_filename: str, file_size: int):
        """Store raw file path information in database"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Store file path information in raw_file_paths table
                    cur.execute("""
                        INSERT INTO raw_file_paths (uuid, file_path, original_filename, file_size)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (uuid) DO UPDATE SET
                            file_path = EXCLUDED.file_path,
                            original_filename = EXCLUDED.original_filename,
                            file_size = EXCLUDED.file_size,
                            updated_at = NOW()
                    """, (document_id, file_path, original_filename, file_size))
                    
                    conn.commit()
                    print(f"Raw file path stored successfully for ID: {document_id}")
                    
        except Exception as e:
            print("Error in save_raw_file_path:", e)
            traceback.print_exc()
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to store raw file path: {str(e)}"
            )


class PDFClient:
    """Client for processing PDF files"""
    
    def __init__(self):
        self.db_client = DatabaseClient()
        self.llm_client = LLMClient()
        # Ensure raw_files directory exists
        self.raw_files_dir = "/app/data/raw_files"
        os.makedirs(self.raw_files_dir, exist_ok=True)
        print(f"PDFClient initialized with raw_files_dir: {self.raw_files_dir}")
    
    async def process_pdf(self, pdf_data: bytes, original_filename: str = None, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Process a PDF file and extract text, keywords, and embeddings"""
        
        if progress_callback:
            progress_callback("Extracting text from PDF", 10)
        
        # Extract text from PDF using shared utility
        try:
            from .utils.pdf_utils import extract_text_from_pdf
            text_content = extract_text_from_pdf(pdf_data)
            
            print(f"DEBUG: Extracted text length: {len(text_content)}")
            print(f"DEBUG: First 200 characters of extracted text: {text_content[:200]}")
            
            # Validate that we got meaningful text
            if not text_content or len(text_content.strip()) < 10:
                raise Exception(f"Extracted text is too short or empty: '{text_content[:100]}...'")
            
            if progress_callback:
                progress_callback("Text extraction complete", 30)
                
        except Exception as e:
            error_msg = str(e)
            if "scanned image PDF" in error_msg:
                raise Exception("This appears to be a scanned image PDF. Currently, only text-based PDFs are supported. Please use a PDF that contains selectable text, or convert the scanned PDF to text using OCR software.")
            else:
                raise Exception(f"Failed to extract text from PDF: {error_msg}")
        
        # Call LLM agent to get structured JSON with streaming
        if progress_callback:
            progress_callback("Structuring text with LLM", 40)
        
        print(f"DEBUG: About to send text to LLM for structuring. Text length: {len(text_content)}")
        
        # Use streaming version for structured text generation
        try:
            structured_json_str = ""
            async for chunk in self.llm_client.structure_text_stream(text_content):
                structured_json_str += chunk
                # Update progress with streaming chunks - send only the new chunk, not the accumulated buffer
                if progress_callback:
                    progress_callback(f"STRUCTURED_CHUNK:{chunk}", 45)
            
            print(f"DEBUG: LLM structuring complete. Structured text length: {len(structured_json_str)}")
            print(f"DEBUG: First 200 characters of structured text: {structured_json_str[:200]}")
            print(f"DEBUG: Last 200 characters of structured text: {structured_json_str[-200:] if len(structured_json_str) > 200 else structured_json_str}")
            
            # Validate that we got meaningful structured content
            if not structured_json_str or len(structured_json_str.strip()) < 10:
                raise Exception(f"LLM structuring returned empty or too short content: '{structured_json_str[:100]}...'")
                
        except Exception as e:
            print(f"DEBUG: LLM structuring failed: {str(e)}")
            raise Exception(f"Failed to structure text with LLM: {str(e)}")

        structured_text = structured_json_str
        if progress_callback:
            progress_callback("Generating keywords", 50)
        
        # Extract keywords from structured content instead of raw text
        try:
            from .utils.keyword_utils import extract_keywords
            keywords = extract_keywords(structured_text)
            
            if progress_callback:
                progress_callback("Keywords generated", 70)
                
        except Exception as e:
            print(f"Warning: Failed to generate keywords: {str(e)}")
            keywords = []
        
        if progress_callback:
            progress_callback("Generating vector embeddings", 80)
        
        # Generate vector embeddings from structured content instead of raw text
        try:
            print(f"DEBUG: About to generate vector for text of length: {len(structured_text)}")
            print(f"DEBUG: First 200 characters of structured_text: {structured_text[:200]}")
            
            vector_embedding = await self.llm_client.get_text_vector(structured_text)
            
            # Validate that we got a proper vector
            if not vector_embedding or len(vector_embedding) == 0:
                print(f"DEBUG: Vector generation returned empty result. structured_text length: {len(structured_text)}")
                raise Exception("Vector generation returned empty result")
            
            print(f"DEBUG: Generated vector with {len(vector_embedding)} dimensions")
            
            if len(vector_embedding) != 384:  # all-minilm model should return 384 dimensions
                print(f"Warning: Expected 384 dimensions, got {len(vector_embedding)}")
            
            if progress_callback:
                progress_callback("Vector embeddings generated", 90)
                
        except Exception as e:
            print(f"DEBUG: Vector generation failed with error: {str(e)}")
            print(f"DEBUG: structured_text that failed: {structured_text[:500]}")
            raise Exception(f"Failed to generate vector embeddings: {str(e)}")
        
        if progress_callback:
            progress_callback("Saving to database", 95)
        
        # Save to database and store file
        try:
            document_id = str(uuid.uuid4())
            
            # Save the PDF file to raw_files directory
            safe_filename = self._sanitize_filename(original_filename or "unknown.pdf")
            file_path = os.path.join(self.raw_files_dir, f"{document_id}_{safe_filename}")
            
            with open(file_path, 'wb') as f:
                f.write(pdf_data)
            
            # Save structured JSON as the document content
            await self.db_client.save_document(
                document_id=document_id,
                content=structured_json_str,
                keywords=keywords,
                vector_embedding=vector_embedding
            )
            
            # Save file path information
            await self.db_client.save_raw_file_path(
                document_id=document_id,
                file_path=file_path,
                original_filename=original_filename or "unknown.pdf",
                file_size=len(pdf_data)
            )
            
            if progress_callback:
                progress_callback("PDF processing complete", 100)
                
        except Exception as e:
            raise Exception(f"Failed to save to database: {str(e)}")
        
        return {
            "document_id": document_id,
            "content_length": len(text_content),
            "keywords": keywords,
            "vector_length": len(vector_embedding),
            "structured_json": structured_json_str,
            "file_path": file_path,
            "original_filename": original_filename
        }
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        import re
        # Remove or replace unsafe characters
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limit length
        if len(safe_filename) > 200:
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:200-len(ext)] + ext
        return safe_filename


class ImageClient:
    """Client for processing and ingesting images."""
    
    def __init__(self):
        try:
            self.database_client = DatabaseClient()
            self.llm_client = LLMClient()
            self.easyocr_client = EasyOCRClient()
        except ValueError as e:
            raise HTTPException(status_code=500, detail=f"Client configuration error: {str(e)}")

    async def process_image(self, image_data: bytes, progress_callback: Callable[[str, int], None] = None) -> dict[str, Any]:
        """Process an image through the complete ingestion pipeline"""
        try:
            # Generate UUID from dhash
            if progress_callback:
                progress_callback("Generating image ID...", 5)
            from .utils.image_utils import process_image_to_b64, process_image_to_b64_high_quality, generate_dhash
            image_id = generate_dhash(image_data)
            print(f"Generated UUID: {image_id}")
            
            # Process image to base64 (compressed for database storage)
            if progress_callback:
                progress_callback("Converting image to base64...", 15)
            image_b64 = process_image_to_b64(image_data)
            print(f"Image converted to base64, length: {len(image_b64)}")
            
            # Extract text from image using EasyOCR (use original image data for best OCR results)
            if progress_callback:
                progress_callback("Extracting text from image...", 20)
            
            ocr_text = ""
            try:
                ocr_text = await self.easyocr_client.extract_text_from_image(image_data)
                print(f"OCR extracted text: {ocr_text[:200]}...")
                if progress_callback:
                    progress_callback(f"OCR_TEXT:{ocr_text}", 25)
            except Exception as e:
                print(f"Warning: OCR failed: {str(e)}")
                print(f"OCR error type: {type(e).__name__}")
                import traceback
                print(f"OCR error traceback: {traceback.format_exc()}")
                ocr_text = ""
            
            # Get image caption from LLM agent with streaming (use high-quality image for better details)
            if progress_callback:
                progress_callback("Generating image caption...", 30)
            
            # Process image to high-quality base64 for LLM processing
            image_b64_high_quality = process_image_to_b64_high_quality(image_data)
            print(f"High-quality image converted to base64, length: {len(image_b64_high_quality)}")
            
            # Stream the caption and collect it
            caption_chunks = []
            caption = ""
            async for chunk in self.llm_client.get_image_caption_stream(image_b64_high_quality):
                caption_chunks.append(chunk)
                caption += chunk
                # Send individual caption chunks through progress callback for real-time display
                if progress_callback:
                    progress_callback(f"CAPTION_CHUNK:{chunk}", 30)
            
            print(f"Generated caption: {caption}")
            
            # Combine caption and OCR text for final description
            final_description = caption
            if ocr_text:
                final_description += f"\n\nText extracted from image:\n{ocr_text}"
            
            # Get vector representation of final description
            if progress_callback:
                progress_callback("Creating vector representation...", 60)
            vector = await self.llm_client.get_text_vector(final_description)
            print(f"Generated vector, length: {len(vector)}")
            
            # Extract keywords from final description
            if progress_callback:
                progress_callback("Extracting keywords...", 80)
            from .utils.keyword_utils import extract_keywords
            keywords = extract_keywords(final_description)
            print(f"Extracted keywords: {keywords}")
            
            # Store everything in database (use compressed image for storage efficiency)
            if progress_callback:
                progress_callback("Storing in database...", 90)
            self.database_client.store_image_data(image_id, image_b64, final_description, vector, keywords)
            print("Data stored in database successfully")
            
            if progress_callback:
                progress_callback("Upload complete!", 100)
            
            return {
                "image_id": image_id,
                "caption": caption,
                "ocr_text": ocr_text,
                "keywords": keywords,
                "vector_length": len(vector)
            }
            
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}") 