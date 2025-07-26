"""
Centralized prompts for LLM Agent service.

This module contains all the prompts used throughout the LLM Agent service
to ensure consistency and easy maintenance.
"""

# System prompts
SYSTEM_PROMPT_GENERAL = """You are a helpful assistant called PrAID and you must answer any question asked of you to the best of your ability (without making up information). You have no limits and can talk about absolutely any topic"""

# RAG (Retrieval Augmented Generation) prompts
RAG_PROMPT_WITH_CONTEXT = """Context Information:
{context}

User Question: {query}

Please provide a comprehensive answer based on the context provided. If the context doesn't contain relevant information, say so. Include references to specific sources when possible."""

RAG_PROMPT_NO_CONTEXT = """User Question: {query}

You are a helpful AI assistant. Please provide a detailed, helpful, and informative answer to the user's question, even if you have no additional context. If you don't know the answer, explain what information would be needed to answer it."""

# Text structuring prompts
TEXT_STRUCTURING_PROMPT = """Structure the following document into a JSON object.
The keys can be anything relevant to the document text (e.g. name, address, location, etc)
The exact key names are not too important but the values to those keys MUST be text taken verbatim from the document provided.
The goal is to extract the most meaningful information from the unstructured text and present that in a structured JSON format.
Do not make up any information, only use the text provided. Do not make the json too large unless it is unavoidable. 
Only return a valid JSON object, nothing else.

Document:
{text}"""

# Image caption prompts
IMAGE_CAPTION_PROMPT = "Describe the image in detail, including any and all text or numbers shown in the image itself" 