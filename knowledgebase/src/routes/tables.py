"""
Table management routes for KnowledgeBase service.

Provides endpoints for adding data to and querying specific tables.
"""

from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import Response
from typing import Any
import base64
from src.database import (
    query_table,
    add_image, add_caption, add_keyword, add_vector, find_similar_vectors,
    SessionLocal, _execute_safe_query
)
from src.schemas import (
    AddImageRequest, AddCaptionRequest, 
    AddKeywordRequest, AddVectorRequest
)

router = APIRouter(prefix="/tables", tags=["tables"])

# --- Add entry endpoints (PUT) - used internally by fileingestor ---
@router.put("/images/add")
async def add_image_endpoint(request: AddImageRequest) -> dict[str, Any]:
    """Add an image entry to the images table"""
    try:
        return await add_image(request.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/captions/add")
async def add_caption_endpoint(request: AddCaptionRequest) -> dict[str, Any]:
    """Add a caption entry to the captions table"""
    try:
        return await add_caption(request.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/keywords/add")
async def add_keyword_endpoint(request: AddKeywordRequest) -> dict[str, Any]:
    """Add or update a keyword entry in the keywords table"""
    try:
        return await add_keyword(request.keyword, request.sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/vectors/add")
async def add_vector_endpoint(request: AddVectorRequest) -> dict[str, Any]:
    """Add a vector entry to the vectors table using pgvector"""
    try:
        return await add_vector(request.uuid, request.embedding)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Efficient lookup endpoints (by primary key) ---
@router.post("/images/lookup")
async def lookup_images_endpoint(uuids: list[str] = Body(...)) -> dict[str, Any]:
    """Lookup images by UUID(s) only (indexed)"""
    try:
        if not uuids:
            return {"results": [], "count": 0, "table": "images"}
        
        # Convert string UUIDs to UUID objects for PostgreSQL
        import uuid
        uuid_objects = [uuid.UUID(uuid_str) for uuid_str in uuids]
        
        query = "SELECT uuid, content, created_at, updated_at FROM images WHERE uuid = ANY(:uuids)"
        db = SessionLocal()
        try:
            result = _execute_safe_query(db, query, {"uuids": uuid_objects})
            rows = result.fetchall()
            results = []
            for row in rows:
                results.append({
                    "uuid": str(row[0]),
                    "content": row[1],
                    "created_at": row[2],
                    "updated_at": row[3]
                })
            return {"results": results, "count": len(results), "table": "images", "searched_uuids": uuids}
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/captions/lookup")
async def lookup_captions_endpoint(uuids: list[str] = Body(...)) -> dict[str, Any]:
    """Lookup captions by UUID(s) only (indexed)"""
    try:
        if not uuids:
            return {"results": [], "count": 0, "table": "captions"}
        
        # Convert string UUIDs to UUID objects for PostgreSQL
        import uuid
        uuid_objects = [uuid.UUID(uuid_str) for uuid_str in uuids]
        
        query = "SELECT uuid, content, created_at, updated_at FROM captions WHERE uuid = ANY(:uuids)"
        db = SessionLocal()
        try:
            result = _execute_safe_query(db, query, {"uuids": uuid_objects})
            rows = result.fetchall()
            results = []
            for row in rows:
                results.append({
                    "uuid": str(row[0]),
                    "content": row[1],
                    "created_at": row[2],
                    "updated_at": row[3]
                })
            return {"results": results, "count": len(results), "table": "captions", "searched_uuids": uuids}
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/lookup")
async def lookup_documents_endpoint(uuids: list[str] = Body(...)) -> dict[str, Any]:
    """Lookup documents by UUID(s) only (indexed)"""
    try:
        if not uuids:
            return {"results": [], "count": 0, "table": "documents"}
        
        # Convert string UUIDs to UUID objects for PostgreSQL
        import uuid
        uuid_objects = [uuid.UUID(uuid_str) for uuid_str in uuids]
        
        query = "SELECT uuid, content, created_at, updated_at FROM documents WHERE uuid = ANY(:uuids)"
        db = SessionLocal()
        try:
            result = _execute_safe_query(db, query, {"uuids": uuid_objects})
            rows = result.fetchall()
            results = []
            for row in rows:
                results.append({
                    "uuid": str(row[0]),
                    "content": row[1],
                    "created_at": row[2],
                    "updated_at": row[3]
                })
            return {"results": results, "count": len(results), "table": "documents", "searched_uuids": uuids}
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/raw_file_paths/lookup")
async def lookup_raw_file_paths_endpoint(uuids: list[str] = Body(...)) -> dict[str, Any]:
    """Lookup raw_file_paths by UUID(s) only (indexed)"""
    try:
        if not uuids:
            return {"results": [], "count": 0, "table": "raw_file_paths"}
        
        # Convert string UUIDs to UUID objects for PostgreSQL
        import uuid
        uuid_objects = [uuid.UUID(uuid_str) for uuid_str in uuids]
        
        query = "SELECT uuid, file_path, original_filename, file_size, created_at, updated_at FROM raw_file_paths WHERE uuid = ANY(:uuids)"
        db = SessionLocal()
        try:
            result = _execute_safe_query(db, query, {"uuids": uuid_objects})
            rows = result.fetchall()
            results = []
            for row in rows:
                results.append({
                    "uuid": str(row[0]),
                    "file_path": row[1],
                    "original_filename": row[2],
                    "file_size": row[3],
                    "created_at": row[4],
                    "updated_at": row[5]
                })
            return {"results": results, "count": len(results), "table": "raw_file_paths", "searched_uuids": uuids}
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vectors/lookup")
async def lookup_vectors_endpoint(uuids: list[str] = Body(...)) -> dict[str, Any]:
    """Lookup vectors by UUID(s) only (indexed)"""
    try:
        if not uuids:
            return {"results": [], "count": 0, "table": "vectors"}
        
        # Convert string UUIDs to UUID objects for PostgreSQL
        import uuid
        uuid_objects = [uuid.UUID(uuid_str) for uuid_str in uuids]
        
        query = "SELECT uuid, embedding, created_at, updated_at FROM vectors WHERE uuid = ANY(:uuids)"
        db = SessionLocal()
        try:
            result = _execute_safe_query(db, query, {"uuids": uuid_objects})
            rows = result.fetchall()
            results = []
            for row in rows:
                results.append({
                    "uuid": str(row[0]),
                    "embedding": list(row[1]) if row[1] else [],
                    "created_at": row[2],
                    "updated_at": row[3]
                })
            return {"results": results, "count": len(results), "table": "vectors", "searched_uuids": uuids}
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/keywords/lookup")
async def lookup_keywords_endpoint(keywords: list[str] = Body(...)) -> dict[str, Any]:
    """Lookup specific keywords efficiently using indexed queries"""
    try:
        if not keywords:
            return {"results": [], "count": 0, "table": "keywords"}
        query = "SELECT keyword, uuids, created_at, updated_at FROM keywords WHERE keyword = ANY(:keywords)"
        db = SessionLocal()
        try:
            result = _execute_safe_query(db, query, {"keywords": keywords})
            rows = result.fetchall()
            results = []
            for row in rows:
                results.append({
                    "keyword": row[0],
                    "uuids": list(row[1]) if row[1] else [],
                    "created_at": row[2],
                    "updated_at": row[3]
                })
            return {"results": results, "count": len(results), "table": "keywords", "searched_keywords": keywords}
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Document serving endpoint ---
@router.get("/documents/{document_id}")
async def get_document(document_id: str):
    """Serve a document by ID from the database"""
    try:
        # First, check if the document exists in raw_file_paths table (actual PDF files)
        path_result = await query_table("raw_file_paths", f"SELECT file_path, original_filename FROM raw_file_paths WHERE uuid = '{document_id}'")
        
        if path_result["results"] and len(path_result["results"]) > 0:
            # Document found in raw_file_paths - serve the actual PDF file
            document_data = path_result["results"][0]
            file_path = document_data.get("file_path")
            original_filename = document_data.get("original_filename", f"{document_id}.pdf")
            
            if not file_path:
                raise HTTPException(status_code=404, detail="Document file path not found")
            
            # Check if file exists
            import os
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="Document file not found on disk")
            
            # Read and return the file
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to read document file: {str(e)}")
            
            # Return the document with proper headers
            return Response(
                content=file_content,
                media_type="application/pdf",
                headers={
                    "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                    "Content-Disposition": f"inline; filename=\"{original_filename}\""
                }
            )
        
        # If not found in raw_file_paths, check documents table (extracted text content)
        doc_result = await query_table("documents", f"SELECT content FROM documents WHERE uuid = '{document_id}'")
        
        if doc_result["results"] and len(doc_result["results"]) > 0:
            # Document found in documents table - return the extracted text content
            document_data = doc_result["results"][0]
            content = document_data.get("content", "")
            
            # Handle different content types
            if isinstance(content, dict):
                import json
                content = json.dumps(content, indent=2)
            elif not isinstance(content, str):
                content = str(content)
            
            # Return the document content as text
            return Response(
                content=content,
                media_type="text/plain",
                headers={
                    "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                    "Content-Disposition": f"inline; filename=\"{document_id}.txt\""
                }
            )
        
        # Document not found in either table
        raise HTTPException(status_code=404, detail="Document not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve document: {str(e)}")

# --- Image serving endpoint ---
@router.get("/images/{image_id}")
async def get_image(image_id: str):
    """Serve an image by ID from the database"""
    try:
        # Query the images table for the specific image
        result = await query_table("images", f"SELECT content FROM images WHERE uuid = '{image_id}'")
        
        if not result["results"] or len(result["results"]) == 0:
            raise HTTPException(status_code=404, detail="Image not found")
        
        image_data = result["results"][0]["content"]
        
        # Decode base64 image data
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Invalid image data: {str(e)}")
        
        # Return the image with proper headers
        return Response(
            content=image_bytes,
            media_type="image/jpeg",
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "Content-Disposition": f"inline; filename=\"{image_id}.jpg\""
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve image: {str(e)}")

@router.delete("/remove_id/{uuid}")
async def remove_id_endpoint(uuid: str):
    """Remove all data related to a given UUID from all tables"""
    try:
        # Convert string UUID to UUID object
        import uuid as uuid_module
        import os
        uuid_obj = uuid_module.UUID(uuid)
        
        db = SessionLocal()
        try:
            # Start transaction
            db.begin()
            
            # Get file paths before deletion for cleanup
            file_paths_to_delete = []
            
            # Check raw_file_paths table for file paths
            path_result = _execute_safe_query(db, 
                "SELECT file_path FROM raw_file_paths WHERE uuid = :uuid", 
                {"uuid": uuid_obj}
            )
            rows = path_result.fetchall()
            for row in rows:
                if row[0]:  # file_path is not None
                    file_paths_to_delete.append(row[0])
            
            # Remove from images table
            _execute_safe_query(db, "DELETE FROM images WHERE uuid = :uuid", {"uuid": uuid_obj})
            
            # Remove from captions table
            _execute_safe_query(db, "DELETE FROM captions WHERE uuid = :uuid", {"uuid": uuid_obj})
            
            # Remove from documents table
            _execute_safe_query(db, "DELETE FROM documents WHERE uuid = :uuid", {"uuid": uuid_obj})
            
            # Remove from raw_file_paths table
            _execute_safe_query(db, "DELETE FROM raw_file_paths WHERE uuid = :uuid", {"uuid": uuid_obj})
            
            # Remove from vectors table
            _execute_safe_query(db, "DELETE FROM vectors WHERE uuid = :uuid", {"uuid": uuid_obj})
            
            # Remove UUID from keywords table arrays
            _execute_safe_query(db, 
                "UPDATE keywords SET uuids = array_remove(uuids, :uuid), updated_at = NOW() WHERE :uuid = ANY(uuids)", 
                {"uuid": uuid_obj}
            )
            
            # Clean up empty keywords
            _execute_safe_query(db, "DELETE FROM keywords WHERE array_length(uuids, 1) IS NULL OR array_length(uuids, 1) = 0")
            
            # Commit transaction
            db.commit()
            
            # Delete actual files from filesystem
            deleted_files = []
            for file_path in file_paths_to_delete:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        deleted_files.append(file_path)
                        print(f"Deleted file: {file_path}")
                except Exception as e:
                    print(f"Warning: Could not delete file {file_path}: {e}")
            
            return {
                "message": f"Successfully removed all data for UUID: {uuid}",
                "removed_uuid": uuid,
                "deleted_files": deleted_files,
                "files_deleted_count": len(deleted_files),
                "status": "success"
            }
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear_all_vectors")
async def clear_all_vectors_endpoint():
    """Temporary endpoint to clear all vectors from the database"""
    try:
        db = SessionLocal()
        try:
            # Clear all vectors
            result = _execute_safe_query(db, "DELETE FROM vectors")
            db.commit()
            return {"message": "All vectors cleared successfully", "deleted_count": result.rowcount}
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vectors/similarity_search")
async def similarity_search_endpoint(request: dict):
    """Search for similar vectors using pgvector's native similarity search within candidate UUIDs"""
    try:
        query_vector = request.get("query_vector")
        candidate_uuids = request.get("candidate_uuids", [])
        limit = request.get("limit", 10)
        
        if not query_vector or not isinstance(query_vector, list):
            raise HTTPException(status_code=400, detail="query_vector must be a list of floats")
        
        if not isinstance(limit, int) or limit <= 0:
            raise HTTPException(status_code=400, detail="limit must be a positive integer")
        
        db = SessionLocal()
        try:
            # Convert query vector to PostgreSQL vector format
            vector_str = "[" + ",".join(map(str, query_vector)) + "]"
            
            if candidate_uuids:
                # Convert string UUIDs to UUID objects
                import uuid
                uuid_objects = [uuid.UUID(uuid_str) for uuid_str in candidate_uuids]
                
                # Use pgvector's cosine similarity operator (<=>) for ranking within candidates
                # 1 - (embedding <=> query_vector) gives us cosine similarity
                query = f"""
                    SELECT uuid, 1 - (embedding <=> '{vector_str}'::vector) AS similarity
                    FROM vectors
                    WHERE uuid = ANY(ARRAY{list(uuid_objects)}::uuid[])
                    ORDER BY embedding <=> '{vector_str}'::vector
                    LIMIT {limit}
                """
            else:
                # If no candidates provided, search all vectors
                query = f"""
                    SELECT uuid, 1 - (embedding <=> '{vector_str}'::vector) AS similarity
                    FROM vectors
                    ORDER BY embedding <=> '{vector_str}'::vector
                    LIMIT {limit}
                """
            
            # Execute query directly using text()
            from sqlalchemy import text
            result = db.execute(text(query))
            rows = result.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    "uuid": str(row[0]),
                    "similarity": float(row[1])
                })
            
            return {"results": results}
            
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 