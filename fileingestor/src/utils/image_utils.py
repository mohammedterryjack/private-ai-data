"""
Shared image processing utilities.
"""

import base64
import io
import uuid
import imagehash
from PIL import Image
from typing import Tuple


def process_image_to_b64(image_data: bytes, size: Tuple[int, int] = (256, 256), quality: int = 50) -> str:
    """
    Process image: resize, compress, convert to base64.
    
    Args:
        image_data: Raw image bytes
        size: Target size as (width, height) tuple (default: (256, 256))
        quality: JPEG quality (1-100, default: 50)
    
    Returns:
        Base64 encoded string of the processed image
    """
    # Open image from bytes
    image = Image.open(io.BytesIO(image_data))
    
    # Convert to RGB if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize to target size
    image = image.resize(size, Image.Resampling.LANCZOS)
    
    # Save as JPEG with specified quality
    output_buffer = io.BytesIO()
    image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
    
    # Convert to base64
    b64_string = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
    return b64_string


def process_image_to_b64_high_quality(image_data: bytes) -> str:
    """
    Process image to base64 without compression or resizing for LLM processing.
    Preserves all image details for better caption generation.
    
    Args:
        image_data: Raw image bytes
    
    Returns:
        Base64 encoded string of the original image
    """
    # Open image from bytes
    image = Image.open(io.BytesIO(image_data))
    
    # Convert to RGB if necessary (required for most ML models)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Save as JPEG with high quality (no resizing)
    output_buffer = io.BytesIO()
    image.save(output_buffer, format='JPEG', quality=95, optimize=False)
    
    # Convert to base64
    b64_string = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
    return b64_string


def generate_dhash(image_data: bytes) -> str:
    """
    Generate dhash of image and return as UUID.
    
    Args:
        image_data: Raw image bytes
    
    Returns:
        UUID string generated from image hash
    """
    image = Image.open(io.BytesIO(image_data))
    # Convert to RGB if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Generate dhash
    dhash = imagehash.dhash(image)
    # Convert to UUID (using first 16 bytes of hash)
    hash_bytes = dhash.hash.tobytes()
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, hash_bytes.hex())) 