"""
LLM Agent Service

A FastAPI service for LLM operations using Ollama.
Provides text generation, embeddings, vision, and RAG capabilities.
"""

import asyncio
import base64
import io
import json
import logging
import os
from typing import Any

import httpx
from PIL import Image

from .client import OllamaClient
from .prompts import (
    SYSTEM_PROMPT_GENERAL,
    RAG_PROMPT_WITH_CONTEXT,
    RAG_PROMPT_NO_CONTEXT,
    TEXT_STRUCTURING_PROMPT
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
OLLAMA_HOST = os.getenv("OLLAMA_HOST")
OLLAMA_PORT = os.getenv("OLLAMA_PORT")

if not OLLAMA_HOST or not OLLAMA_PORT:
    raise ValueError("OLLAMA_HOST and OLLAMA_PORT environment variables must be set")

OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
SEARCH_ENGINE_URL = os.getenv("SEARCH_ENGINE_URL")

# Initialize Ollama client
_ollama_client = OllamaClient(OLLAMA_BASE_URL)


async def check_ollama_health() -> dict[str, Any]:
    """Check if Ollama is available"""
    try:
        result = await _ollama_client.get_models()
        return {
            "status": "healthy",
            "service": "llmagent",
            "ollama_available": True,
            "models": result.get("models", [])
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "llmagent",
            "ollama_available": False,
            "error": str(e)
        }

async def text_to_vector(text: str) -> dict[str, Any]:
    """Convert text to semantic vector using Ollama (all-minilm model)"""
    try:
        result = await _ollama_client.generate_embedding(text, "all-minilm")
        return {
            "vector": result.get("embedding", []),
            "model": "all-minilm",
            "text_length": len(text)
        }
    except Exception as e:
        raise Exception(f"Vector generation error: {str(e)}")

async def describe_image_from_file_stream(image_bytes: bytes):
    """Create a caption for an image using Ollava (llava model) with streaming response"""
    try:
        # Open image from bytes
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert image to base64 for Ollama (required by Ollama API)
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        image_encoded = base64.b64encode(img_buffer.getvalue()).decode() 
        
        # Stream the caption generation
        async for chunk in _ollama_client.generate_caption_stream(
            b64_encoded_images=[image_encoded],
        ):
            yield chunk
            
    except Exception as e:
        yield f"Error: Image description error: {str(e)}"

async def rag_query_stream(query: str, sources: list[str] | None = None):
    """RAG: Retrieval Augmented Generation with streaming response"""
    try:
        logger.info(f"RAG stream query started with query: '{query}'")
        logger.info(f"Sources provided: {sources}")
        
        # Build context from sources
        logger.info("Building context from sources...")
        context_parts = []
        if sources:
            context_parts.append("Available Sources:\n" + "\n".join([f"- {source}" for source in sources]))
        
        full_context = "\n\n".join(context_parts) if context_parts else ""
        logger.info(f"Built context: '{full_context}'")
        
        # Create RAG prompt
        logger.info("Creating RAG prompt...")
        if full_context:
            rag_prompt = RAG_PROMPT_WITH_CONTEXT.format(context=full_context, query=query)
        else:
            rag_prompt = RAG_PROMPT_NO_CONTEXT.format(query=query)
        
        logger.info(f"RAG prompt created (length: {len(rag_prompt)}):")
        logger.info(f"Prompt: {rag_prompt}")
        
        logger.info("Calling Ollama generate_text_stream...")
        async for chunk in _ollama_client.generate_text_stream(
            system_prompt=SYSTEM_PROMPT_GENERAL,
            prompt=rag_prompt,
        ):
            yield chunk
        
    except Exception as e:
        logger.error(f"RAG stream query failed with error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        yield f"Error: {str(e)}"

async def structure_text_stream(text: str):
    """Extract structured JSON from raw text using LLM with streaming response"""
    # Truncate text if it's too long (LLM has context limits)    
    prompt = TEXT_STRUCTURING_PROMPT.format(text=text)
    
    try:
        # Use llama3.2 for structured extraction with streaming and JSON formatting
        chunk_count = 0
        async for chunk in _ollama_client.generate_text_stream(
            system_prompt=SYSTEM_PROMPT_GENERAL,
            prompt=prompt,
            return_json=True  # Enable JSON formatting
        ):
            chunk_count += 1
            # Yield each chunk as it comes in
            yield chunk
            
        # Validate that we got meaningful content
        if chunk_count == 0:
            logger.error("Structure text stream returned no chunks")
            yield "Error: LLM returned no content"
        else:
            logger.info(f"Structure text stream completed with {chunk_count} chunks")
            
    except Exception as e:
        logger.error(f"Structure text stream failed with error: {str(e)}")
        yield f"Error: Failed to structure text: {str(e)}"

async def structure_text(text: str) -> dict[str, Any]:
    """Extract structured JSON from raw text using LLM"""
    # Truncate text if it's too long (LLM has context limits)    
    prompt = TEXT_STRUCTURING_PROMPT.format(text=text)
    
    try:
        # Use llama3.2 for structured extraction
        result = await _ollama_client.generate_text(prompt, "llama3.2", return_json=True)
        return {
            "structured_text": result.get("response", "")
        }
    except Exception as e:
        logger.error(f"Structure text failed with error: {str(e)}")
        # Return default structure on error
        return {
            "error": f"Failed to structure text: {str(e)}"
        } 