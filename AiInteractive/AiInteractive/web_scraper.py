import trafilatura
import requests
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

def get_website_text_content(url: str) -> dict:
    """
    Extract text content from a website URL.
    Returns a dictionary with content, title, and metadata.
    """
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL format")
        
        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        logger.info(f"Fetching content from: {url}")
        
        # Fetch the webpage
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            raise Exception("Failed to fetch the webpage")
        
        # Extract text content
        text_content = trafilatura.extract(downloaded)
        if not text_content:
            raise Exception("Failed to extract text content from the webpage")
        
        # Extract metadata
        metadata = trafilatura.extract_metadata(downloaded)
        title = metadata.title if metadata and metadata.title else "Untitled"
        
        logger.info(f"Successfully extracted {len(text_content)} characters of content")
        
        return {
            'content': text_content,
            'title': title,
            'url': url,
            'word_count': len(text_content.split()),
            'char_count': len(text_content)
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while fetching {url}: {str(e)}")
        raise Exception(f"Network error: Unable to fetch the webpage. Please check the URL and try again.")
    
    except ValueError as e:
        logger.error(f"URL validation error: {str(e)}")
        raise Exception(f"Invalid URL: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {str(e)}")
        raise Exception(f"Content extraction failed: {str(e)}")

def validate_url(url: str) -> bool:
    """
    Validate if the provided string is a valid URL.
    """
    try:
        parsed = urlparse(url if url.startswith(('http://', 'https://')) else 'https://' + url)
        return bool(parsed.netloc) and bool(parsed.scheme)
    except:
        return False
