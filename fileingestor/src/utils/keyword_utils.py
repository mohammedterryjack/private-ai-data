"""
Shared keyword extraction utilities.
"""

import re
from typing import List


# Common stop words used across all clients
STOP_WORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
    'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
    'to', 'was', 'will', 'with', 'the', 'this', 'but', 'they', 'have',
    'had', 'what', 'said', 'each', 'which', 'she', 'do', 'how', 'their',
    'if', 'up', 'out', 'many', 'then', 'them', 'these', 'so', 'some',
    'her', 'would', 'make', 'like', 'into', 'him', 'time', 'two', 'more',
    'go', 'no', 'way', 'could', 'my', 'than', 'first', 'been', 'call',
    'who', 'oil', 'sit', 'now', 'find', 'down', 'day', 'did', 'get',
    'come', 'made', 'may', 'part', 'text', 'image', 'shows', 'picture',
    'photo', 'photograph', 'image', 'showing', 'depicting', 'containing'
}


def extract_keywords(text: str, max_keywords: int = 10, max_word_length: int = 250) -> List[str]:
    """
    Extract keywords from text using simple NLP techniques.
    
    Args:
        text: The text to extract keywords from
        max_keywords: Maximum number of keywords to return (default: 10)
        max_word_length: Maximum length of individual keywords (default: 250)
    
    Returns:
        List of extracted keywords
    """
    try:
        print(f"Extracting keywords from text of length: {len(text)}")
        print(f"Text preview: {text[:200]}...")
        
        # Convert to lowercase and remove punctuation
        cleaned_text = re.sub(r'[^\w\s]', '', text.lower())
        print(f"After cleaning, text length: {len(cleaned_text)}")
        
        # Split into words
        words = cleaned_text.split()
        print(f"Found {len(words)} words")
        
        # Filter out stop words, short words, and limit length
        keywords = [
            word for word in words 
            if word not in STOP_WORDS 
            and len(word) > 2 
            and len(word) <= max_word_length
        ]
        print(f"After filtering, {len(keywords)} keywords remain")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for word in keywords:
            if word not in seen:
                seen.add(word)
                unique_keywords.append(word)
        
        # Return top keywords
        result = unique_keywords[:max_keywords]
        print(f"Final keywords: {result}")
        return result
        
    except Exception as e:
        print(f"Error in extract_keywords: {str(e)}")
        import traceback
        traceback.print_exc()
        return [] 