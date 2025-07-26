"""
Search service for SearchEngine.

Provides document search, retrieval, and LLM-powered search capabilities.
"""

import os
import logging
import numpy as np
import re
from typing import Any, List
from .client import KnowledgeBaseClient, LLMClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global client instances
_kb_client = KnowledgeBaseClient()
_llm_client = LLMClient()

def _extract_keywords_from_query(query: str) -> List[str]:
    """Extract keywords from search query using improved keyword extraction"""
    logger.info(f"Extracting keywords from query: '{query}'")
    
    # More sophisticated keyword extraction
    common_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
        'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
        'there', 'here', 'where', 'when', 'why', 'how', 'what', 'which', 'who', 'whom',
        'very', 'much', 'more', 'most', 'less', 'least', 'so', 'as', 'than', 'too', 'also',
        'just', 'only', 'even', 'still', 'again', 'back', 'up', 'down', 'out', 'off', 'over',
        'under', 'through', 'between', 'among', 'within', 'without', 'against', 'toward', 'towards',
        'into', 'onto', 'upon', 'from', 'since', 'during', 'before', 'after', 'until', 'while',
        'because', 'although', 'though', 'unless', 'if', 'else', 'then', 'therefore', 'thus',
        'hence', 'consequently', 'meanwhile', 'furthermore', 'moreover', 'however', 'nevertheless',
        'nonetheless', 'otherwise', 'instead', 'rather', 'quite', 'rather', 'quite', 'rather',
        'text', 'image', 'picture', 'photo', 'photograph', 'shows', 'showing', 'depicts', 'depicting',
        'contains', 'containing', 'features', 'featuring', 'displays', 'displaying', 'appears',
        'appearing', 'looks', 'looking', 'seems', 'seeming', 'like', 'similar', 'different',
        'same', 'other', 'another', 'each', 'every', 'all', 'both', 'either', 'neither',
        'some', 'any', 'no', 'none', 'few', 'many', 'several', 'various', 'various', 'various'
    }
    
    # Clean and normalize text
    text = query.lower()
    # Remove punctuation but keep apostrophes for contractions
    text = re.sub(r'[^\w\s\']', ' ', text)
    
    # Split into words
    words = text.split()
    logger.info(f"Split words: {words}")
    
    # Extract meaningful keywords
    keywords = []
    for word in words:
        # Clean the word
        word = word.strip("'").strip()
        
        # Skip if too short or common word
        if len(word) < 3 or word in common_words:
            continue
            
        # Skip numbers
        if word.isdigit():
            continue
            
        # Skip common image description words
        if word in ['text', 'image', 'picture', 'photo', 'photograph', 'shows', 'showing', 'depicts', 'depicting']:
            continue
            
        keywords.append(word)
    
    # Remove duplicates and return
    unique_keywords = list(set(keywords))
    logger.info(f"Final unique keywords: {unique_keywords}")
    
    return unique_keywords

def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    try:
        vec1_array = np.array(vec1)
        vec2_array = np.array(vec2)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1_array, vec2_array)
        norm1 = np.linalg.norm(vec1_array)
        norm2 = np.linalg.norm(vec2_array)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    except Exception as e:
        logger.warning(f"Error calculating cosine similarity: {e}")
        return 0.0

async def _get_candidate_ids_from_keywords(keywords: List[str]) -> List[str]:
    """Get candidate IDs from keywords table that match the search keywords"""
    try:
        logger.info(f"Searching for keywords: {keywords}")
        
        # Use efficient keyword lookup instead of full table scan
        keywords_data = await _kb_client.lookup_keywords(keywords)
        logger.info(f"Retrieved {len(keywords_data)} matching keyword entries")
        
        # Debug: Log a summary of found keywords
        if keywords_data:
            found_keywords = [entry.get('keyword', 'NO_KEYWORD') for entry in keywords_data]
            logger.info(f"Found keywords: {found_keywords}")
        
        candidate_ids = set()
        
        for keyword_entry in keywords_data:
            keyword = keyword_entry.get('keyword', '').lower()
            uuids = keyword_entry.get('uuids', [])
            
            # Check if any of our search keywords match this keyword
            for search_keyword in keywords:
                if search_keyword.lower() in keyword or keyword in search_keyword.lower():
                    logger.info(f"Keyword match: '{search_keyword}' matches '{keyword}'")
                    candidate_ids.update(uuids)
        
        logger.info(f"Found {len(candidate_ids)} candidate IDs from keywords: {list(candidate_ids)}")
        return list(candidate_ids)
        
    except Exception as e:
        logger.error(f"Error getting candidate IDs from keywords: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return []

async def _get_vectors_for_ids(candidate_ids: List[str]) -> dict[str, List[float]]:
    """Get vectors for the given candidate IDs"""
    try:
        logger.info(f"Getting vectors for {len(candidate_ids)} candidate IDs")
        
        # Use efficient lookup
        vectors_data = await _kb_client.lookup_vectors(candidate_ids)
        logger.info(f"Retrieved {len(vectors_data)} vector entries")
        
        id_to_vector = {}
        
        for vector_entry in vectors_data:
            uuid = vector_entry.get('uuid')
            embedding = vector_entry.get('embedding', [])
            if uuid in candidate_ids and isinstance(embedding, list):
                id_to_vector[uuid] = embedding
        
        logger.info(f"Found vectors for {len(id_to_vector)} candidate IDs")
        return id_to_vector
        
    except Exception as e:
        logger.error(f"Error getting vectors for IDs: {e}")
        return {}

async def _get_captions_for_ids(candidate_ids: List[str]) -> dict[str, str]:
    """Get captions for the given candidate IDs"""
    try:
        logger.info(f"Getting captions for {len(candidate_ids)} candidate IDs")
        
        # Use efficient lookup
        captions_data = await _kb_client.lookup_captions(candidate_ids)
        logger.info(f"Retrieved {len(captions_data)} caption entries")
        
        id_to_caption = {}
        for caption_entry in captions_data:
            uuid = caption_entry.get('uuid')
            content = caption_entry.get('content', '')
            if uuid in candidate_ids:
                id_to_caption[uuid] = content
        logger.info(f"Found captions for {len(id_to_caption)} candidate IDs")
        return id_to_caption
        
    except Exception as e:
        logger.error(f"Error getting captions for IDs: {e}")
        return {}

async def _get_documents_for_ids(candidate_ids: List[str]) -> dict[str, str]:
    """Get documents for the given candidate IDs"""
    try:
        logger.info(f"Getting documents for {len(candidate_ids)} candidate IDs")
        
        # Use efficient lookup
        documents_data = await _kb_client.lookup_documents(candidate_ids)
        logger.info(f"Retrieved {len(documents_data)} document entries")
        
        id_to_document = {}
        for document_entry in documents_data:
            uuid = document_entry.get('uuid')
            content = document_entry.get('content', '')
            if uuid in candidate_ids:
                id_to_document[uuid] = content
        logger.info(f"Found documents for {len(id_to_document)} candidate IDs")
        return id_to_document
        
    except Exception as e:
        logger.error(f"Error getting documents for IDs: {e}")
        return {}

async def get_health_status() -> dict[str, Any]:
    """Get health status of the search engine"""
    try:
        # Test knowledge base connection
        tables = await _kb_client.get_tables()
        available_tables = tables.get("tables", [])
        table_counts = tables.get("table_counts", {})
        
        # Count actual documents (images/captions) instead of just tables
        total_documents = 0
        if "images" in table_counts:
            total_documents += table_counts["images"]
        elif "captions" in table_counts:
            total_documents += table_counts["captions"]
        
        return {
            "status": "healthy",
            "service": "searchengine",
            "knowledge_base_available": True,
            "tables": available_tables,
            "table_counts": table_counts,
            "document_count": total_documents
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "searchengine",
            "knowledge_base_available": False,
            "error": str(e)
        }

async def search_documents(query: str, n: int = 10) -> list[dict[str, Any]]:
    """Search documents using keyword filtering + pgvector similarity search"""
    try:
        logger.info(f"Hybrid search started with query: '{query}'")
        
        # Step 1: Extract keywords from the search query
        keywords = _extract_keywords_from_query(query)
        logger.info(f"Extracted keywords: {keywords}")
        
        if not keywords:
            logger.warning("No meaningful keywords found in query")
            return []
        
        # Step 2: Filter the keywords table for all IDs that could potentially match
        candidate_ids = await _get_candidate_ids_from_keywords(keywords)
        
        if not candidate_ids:
            logger.info("No candidate IDs found from keywords")
            return []
        
        logger.info(f"Found {len(candidate_ids)} candidate IDs from keyword filtering")
        
        # Step 3: Get vector for the search query
        try:
            query_vector = await _llm_client.get_embedding(query)
            logger.info(f"Generated query vector with length: {len(query_vector)}")
        except Exception as e:
            logger.error(f"Failed to get query vector: {e}")
            return []
        
        # Step 4: Use pgvector's native similarity search on the candidate IDs
        try:
            similarity_results = await _kb_client.similarity_search(query_vector, candidate_ids, n)
            logger.info(f"pgvector similarity search returned {len(similarity_results.get('results', []))} results")
        except Exception as e:
            logger.error(f"Failed to perform similarity search: {e}")
            return []
        
        # Step 5: Get the top N results with their UUIDs and similarity scores
        top_results = similarity_results.get('results', [])
        
        if not top_results:
            logger.info("No similar vectors found within candidates")
            return []
        
        # Extract UUIDs and similarity scores
        result_uuids = [result['uuid'] for result in top_results]
        uuid_to_similarity = {result['uuid']: result['similarity'] for result in top_results}
        
        logger.info(f"Top {len(result_uuids)} results with similarities: {[f'{uuid[:8]}...: {sim:.3f}' for uuid, sim in zip(result_uuids, [uuid_to_similarity[uuid] for uuid in result_uuids])]}")
        
        # Step 6: Get captions and documents for the top results
        id_to_caption = await _get_captions_for_ids(result_uuids)
        id_to_document = await _get_documents_for_ids(result_uuids)
        
        # Step 7: Build final results
        final_results = []
        for result_uuid in result_uuids:
            similarity = uuid_to_similarity[result_uuid]
            
            # Check if this is a document (PDF) or image
            if result_uuid in id_to_document:
                # This is a PDF/document
                document_content = id_to_document.get(result_uuid, 'No document content available')
                final_results.append({
                    'id': result_uuid,
                    'similarity': similarity,
                    'document_id': result_uuid,  # Mark as document
                    'structured_json': document_content,
                    'keywords_matched': keywords
                })
            else:
                # This is an image
                caption_content = id_to_caption.get(result_uuid, 'No caption available')
                
                # Parse caption content to separate LLM caption from OCR text
                caption = caption_content
                ocr_text = ""
                
                # Check if OCR text is embedded in the caption
                if "Text extracted from image:" in caption_content:
                    parts = caption_content.split("Text extracted from image:")
                    if len(parts) == 2:
                        caption = parts[0].strip()
                        ocr_text = parts[1].strip()
                
                final_results.append({
                    'id': result_uuid,
                    'similarity': similarity,
                    'caption': caption,
                    'ocr_text': ocr_text,
                    'keywords_matched': keywords
                })
        
        logger.info(f"Hybrid search completed, found {len(final_results)} results")
        return final_results
        
    except Exception as e:
        logger.error(f"Search failed with error: {str(e)}")
        raise Exception(f"Search error: {str(e)}")

async def count_keywords() -> dict[str, Any]:
    """Simple function to count keywords in the database"""
    try:
        logger.info("=== COUNTING KEYWORDS ===")
        
        # Get all keywords from the database
        keywords_data = await _kb_client.query_table("keywords")
        logger.info(f"Total keywords in database: {len(keywords_data)}")
        
        if keywords_data:
            # Show some sample keywords
            sample_keywords = [entry.get('keyword', 'NO_KEYWORD') for entry in keywords_data[:10]]
            logger.info(f"Sample keywords: {sample_keywords}")
            
            # Count total UUIDs across all keywords
            total_uuids = 0
            for entry in keywords_data:
                uuids = entry.get('uuids', [])
                if isinstance(uuids, list):
                    total_uuids += len(uuids)
                else:
                    logger.warning(f"UUIDs not a list for keyword '{entry.get('keyword')}': {type(uuids)}")
            
            logger.info(f"Total UUIDs across all keywords: {total_uuids}")
            
            return {
                "total_keywords": len(keywords_data),
                "total_uuids": total_uuids,
                "sample_keywords": sample_keywords
            }
        else:
            logger.warning("No keywords found in database")
            return {
                "total_keywords": 0,
                "total_uuids": 0,
                "sample_keywords": [],
                "warning": "No keywords found in database"
            }
        
    except Exception as e:
        logger.error(f"Count keywords failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {"error": str(e)}

async def check_database_content() -> dict[str, Any]:
    """Check what's actually in the database"""
    try:
        logger.info("=== CHECKING DATABASE CONTENT ===")
        
        # Check all tables
        tables = await _kb_client.get_tables()
        available_tables = tables.get("tables", [])
        table_counts = tables.get("table_counts", {})
        
        logger.info(f"Available tables: {available_tables}")
        logger.info(f"Table counts: {table_counts}")
        
        # Check specific tables
        results = {}
        
        for table_name in ['images', 'captions', 'keywords', 'vectors']:
            if table_name in available_tables:
                try:
                    table_data = await _kb_client.query_table(table_name)
                    results[table_name] = {
                        "count": len(table_data),
                        "sample": table_data[:2] if table_data else []
                    }
                    logger.info(f"{table_name}: {len(table_data)} entries")
                except Exception as e:
                    results[table_name] = {"error": str(e)}
                    logger.error(f"Error querying {table_name}: {e}")
            else:
                results[table_name] = {"error": "Table not found"}
                logger.warning(f"Table {table_name} not found")
        
        return {
            "available_tables": available_tables,
            "table_counts": table_counts,
            "table_details": results
        }
        
    except Exception as e:
        logger.error(f"Check database content failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {"error": str(e)} 