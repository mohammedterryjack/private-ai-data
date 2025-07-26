"""
Pydantic schemas for KnowledgeBase service.

Defines request and response models for all API endpoints.
"""

from pydantic import BaseModel
from typing import Any, List
from datetime import datetime

class QueryTableRequest(BaseModel):
    """Request model for querying tables with custom SQL"""
    table_name: str
    query: str

# Specific table request models
class AddImageRequest(BaseModel):
    """Request model for adding image data"""
    content: str  # Base64 encoded image

class AddCaptionRequest(BaseModel):
    """Request model for adding caption data"""
    content: str

class AddKeywordRequest(BaseModel):
    """Request model for adding keyword with sources"""
    keyword: str
    sources: list[str]  # List of UUID strings

class AddVectorRequest(BaseModel):
    """Request model for adding vector data using pgvector"""
    uuid: str
    embedding: list[float] 