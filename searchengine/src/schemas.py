"""
Pydantic schemas for SearchEngine service.

Defines request and response models for search operations.
"""

from typing import Any
from pydantic import BaseModel

class SearchRequest(BaseModel):
    """Request model for document search"""
    query: str
    n: int = 10