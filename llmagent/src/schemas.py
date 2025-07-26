"""
Pydantic schemas for LLM Agent service.

Defines request and response models for LLM operations.
"""

from pydantic import BaseModel

class TextRequest(BaseModel):
    """Request model for text generation"""
    text: str

class RAGRequest(BaseModel):
    """Request model for RAG operations"""
    query: str
    sources: list[str] | None = None 