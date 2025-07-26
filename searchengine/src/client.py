"""
API clients for SearchEngine service.

Provides clients for interacting with KnowledgeBase and LLM Agent services.
"""

import httpx
import os
from typing import Any, List

# Service URLs - must be set via environment variables
KNOWLEDGE_BASE_URL = os.getenv("KNOWLEDGE_BASE_URL")
LLM_AGENT_URL = os.getenv("LLM_AGENT_URL")

class KnowledgeBaseClient:
    """Client for KnowledgeBase service operations"""
    
    def __init__(self):
        self.base_url = os.getenv("KNOWLEDGE_BASE_URL")
    
    async def get_tables(self) -> dict[str, Any]:
        """Get list of available tables"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health/")
            response.raise_for_status()
            health_data = response.json()
            return {
                "tables": health_data.get("tables", []),
                "table_counts": health_data.get("table_counts", {})
            }
    
    async def lookup_images(self, uuids: list[str]) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/tables/images/lookup", json=uuids)
            response.raise_for_status()
            return response.json().get("results", [])

    async def lookup_captions(self, uuids: list[str]) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/tables/captions/lookup", json=uuids)
            response.raise_for_status()
            return response.json().get("results", [])

    async def lookup_documents(self, uuids: list[str]) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/tables/documents/lookup", json=uuids)
            response.raise_for_status()
            return response.json().get("results", [])

    async def lookup_raw_file_paths(self, uuids: list[str]) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/tables/raw_file_paths/lookup", json=uuids)
            response.raise_for_status()
            return response.json().get("results", [])

    async def lookup_vectors(self, uuids: list[str]) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/tables/vectors/lookup", json=uuids)
            response.raise_for_status()
            return response.json().get("results", [])

    # Deprecated: Use lookup_* methods instead
    async def query_table(self, table_name: str) -> list[dict[str, Any]]:
        raise NotImplementedError("query_table is deprecated. Use lookup_* methods for efficient indexed lookups.")
    
    async def lookup_keywords(self, keywords: list[str]) -> list[dict[str, Any]]:
        """Lookup specific keywords efficiently"""
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/tables/keywords/lookup", json=keywords)
            response.raise_for_status()
            return response.json().get("results", [])
    
    async def add_document(self, table_name: str, document: dict[str, Any]) -> dict[str, Any]:
        """Add a document to a table"""
        async with httpx.AsyncClient() as client:
            response = await client.put(f"{self.base_url}/tables/{table_name}/add", json=document)
            response.raise_for_status()
            return response.json()

    async def remove_id(self, uuid: str) -> dict[str, Any]:
        """Remove all data related to a UUID from all tables"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{self.base_url}/tables/remove_id/{uuid}")
            response.raise_for_status()
            return response.json()

    async def similarity_search(self, query_vector: List[float], candidate_uuids: List[str] = None, limit: int = 10) -> dict[str, Any]:
        """Search for similar vectors using pgvector's native similarity search within candidate UUIDs"""
        async with httpx.AsyncClient() as client:
            payload = {
                "query_vector": query_vector, 
                "limit": limit
            }
            if candidate_uuids:
                payload["candidate_uuids"] = candidate_uuids
                
            response = await client.post(
                f"{self.base_url}/tables/vectors/similarity_search",
                json=payload
            )
            response.raise_for_status()
            return response.json()

class LLMClient:
    """Client for interacting with LLM Agent API"""
    
    def __init__(self, base_url: str = LLM_AGENT_URL):
        self.base_url = base_url
    
    async def generate_text(self, prompt: str) -> dict[str, Any]:
        """Generate text using LLM Agent"""
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/generate_text/", json={
                "prompt": prompt,
            })
            if response.status_code != 200:
                raise Exception("LLM Agent service unavailable")
            return response.json()

    async def get_embedding(self, text: str) -> list[float]:
        """Get embedding from LLM Agent /vector endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/vector/", json={"text": text})
            response.raise_for_status()
            return response.json()["vector"]

# Global client instances
kb_client = KnowledgeBaseClient()
llm_client = LLMClient() 