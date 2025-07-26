"""
Ollama client for LLM Agent service.

Provides async client for interacting with Ollama API for text generation,
embeddings, and streaming responses.
"""

import os
import httpx
import logging
import json
from typing import Any
from PIL import Image

from .prompts import IMAGE_CAPTION_PROMPT

# Configure logging
logger = logging.getLogger(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST")
OLLAMA_PORT = os.getenv("OLLAMA_PORT")

print(f"DEBUG OLLAMA: OLLAMA_HOST={OLLAMA_HOST} OLLAMA_PORT={OLLAMA_PORT} OLLAMA_BASE_URL=http://{OLLAMA_HOST}:{OLLAMA_PORT}")

if not OLLAMA_HOST or not OLLAMA_PORT:
    raise ValueError("OLLAMA_HOST and OLLAMA_PORT environment variables must be set")

OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"


class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> dict[str, Any]:
        """Make a request to Ollama API with error handling"""
        full_url = f"{self.base_url}{endpoint}"
        logger.info(f"Making {method} request to: {full_url}")
        logger.info(f"Request kwargs: {kwargs}")
        
        try:
            # Use a longer timeout for Ollama requests (up to 300 seconds for image processing)
            async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
                logger.info("Sending request to Ollama...")
                response = await client.request(method, full_url, **kwargs)
                logger.info(f"Received response: status={response.status_code}")
                logger.info(f"Response headers: {dict(response.headers)}")
                
                response.raise_for_status()
                response_json = response.json()
                logger.info(f"Response JSON: {response_json}")
                return response_json
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code}")
            logger.error(f"Response text: {e.response.text}")
            error_detail = f"Ollama API error: {e.response.status_code}"
            try:
                error_json = e.response.json()
                if "error" in error_json:
                    error_detail += f" - {error_json['error']}"
                    logger.error(f"Error JSON: {error_json}")
            except:
                pass
            raise Exception(error_detail)
        except httpx.TimeoutException as e:
            logger.error(f"Request timed out after 300 seconds: {str(e)}")
            raise Exception(f"Request timeout: Ollama took too long to respond")
        except Exception as e:
            logger.error(f"Request failed with exception: {type(e).__name__}: {str(e)}")
            error_msg = str(e) if str(e) else "Unknown error occurred"
            raise Exception(f"Request error: {error_msg}")
    
    async def get_models(self) -> dict[str, Any]:
        """Get available models"""
        return await self._make_request("GET", "/api/tags")
    
    async def generate_embedding(self, text: str, model: str) -> dict[str, Any]:
        """Generate embedding for text"""
        return await self._make_request("POST", "/api/embeddings", json={
            "model": model,
            "prompt": text
        })

    async def generate_text(self, prompt: str, model: str, 
                          images: list[str] | None = None,
                          return_json: bool=False) -> dict[str, Any]:
        """Generate text using Ollama"""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if return_json:
           payload["format"] = "json"
        if images:
            payload["images"] = images
        
        return await self._make_request("POST", "/api/generate", json=payload)

    async def generate_text_stream(self, system_prompt: str, prompt: str, 
                                 max_tokens: int = 500, temperature: float = 0.7,
                                 images: list[str] | None = None, return_json: bool = False):
        """Generate text using Ollama with streaming response"""
        payload = {
            "model": "llama3.2",
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        if return_json:
            payload["format"] = "json"
        if images:
            payload["images"] = images
        
        logger.info(f"Streaming payload: {payload}")
        full_url = f"{self.base_url}/api/generate"
        logger.info(f"Making streaming request to: {full_url}")
        
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
                async with client.stream("POST", full_url, json=payload) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                logger.info(f"DEBUG: Received streaming chunk: {data}")
                                if "response" in data:
                                    yield data["response"]
                                elif data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                logger.warning(f"DEBUG: Skipping malformed JSON line: {line}")
                                continue
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code}")
            logger.error(f"Response text: {e.response.text}")
            yield f"Error: Ollama API error: {e.response.status_code}"
        except httpx.TimeoutException as e:
            logger.error(f"Request timed out after 300 seconds: {str(e)}")
            yield "Error: Request timeout: Ollama took too long to respond"
        except Exception as e:
            logger.error(f"Request failed with exception: {type(e).__name__}: {str(e)}")
            yield f"Request error: {str(e)}"

    async def generate_caption_stream(self, b64_encoded_images: list[str]):
        """Generate caption using Ollama with streaming response"""
        payload = {
            "model": "llava",
            "prompt": IMAGE_CAPTION_PROMPT,
            "images": b64_encoded_images,
            "stream": True
        }
        
        full_url = f"{self.base_url}/api/generate"
        logger.info(f"Making streaming caption request to: {full_url}")
        
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
                async with client.stream("POST", full_url, json=payload) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    yield data["response"]
                                elif data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                # Skip malformed JSON lines
                                continue
                                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code}")
            logger.error(f"Response text: {e.response.text}")
            yield f"Error: Ollama API error: {e.response.status_code}"
        except httpx.TimeoutException as e:
            logger.error(f"Request timed out after 300 seconds: {str(e)}")
            yield "Error: Request timeout: Ollama took too long to respond"
        except Exception as e:
            logger.error(f"Request failed with exception: {type(e).__name__}: {str(e)}")
            yield f"Request error: {str(e)}" 