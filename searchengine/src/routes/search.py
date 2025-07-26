"""
Search routes for SearchEngine service.

Provides endpoints for document search and retrieval.
"""

from fastapi import APIRouter, HTTPException
from typing import Any
from src.search_service import search_documents
from src.schemas import SearchRequest

router = APIRouter(prefix="", tags=["search"])

@router.post("/")
async def search_endpoint(request: SearchRequest) -> list[dict[str, Any]]:
    """Search documents using keyword and semantic search"""
    try:
        return await search_documents(request.query, request.n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{uuid}")
async def delete_document_endpoint(uuid: str) -> dict[str, Any]:
    """Delete a document and all related data by UUID"""
    try:
        from src.client import kb_client
        result = await kb_client.remove_id(uuid)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @router.get("/debug")
# async def debug_endpoint() -> dict[str, Any]:
#     """Debug endpoint to see what's in the database"""
#     try:
#         return await debug_database_content()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/test/{query}")
# async def test_endpoint(query: str) -> dict[str, Any]:
#     """Test endpoint to debug keyword search step by step"""
#     try:
#         return await test_keyword_search(query)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/test-raw")
# async def test_raw_endpoint() -> dict[str, Any]:
#     """Test endpoint to debug raw keywords table content"""
#     try:
#         return await test_raw_keywords_query()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/count-keywords")
# async def count_keywords_endpoint() -> dict[str, Any]:
#     """Count keywords in the database"""
#     try:
#         return await count_keywords()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/check-db")
# async def check_db_endpoint() -> dict[str, Any]:
#     """Check what's in the database"""
#     try:
#         return await check_database_content()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e)) 