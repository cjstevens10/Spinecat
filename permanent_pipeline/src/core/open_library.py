"""
Open Library API client for searching books
"""

import requests
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

@dataclass
class OpenLibrarySearchParams:
    """Parameters for Open Library search"""
    query: str
    limit: int = 20
    offset: int = 0
    fields: List[str] = None
    sort: str = "relevance"
    
    def __post_init__(self):
        if self.fields is None:
            self.fields = [
                "key", "title", "author_name", "first_publish_year",
                "cover_i", "isbn", "publisher", "language", "subject"
            ]

class OpenLibraryClient:
    """Client for Open Library API"""
    
    def __init__(self, base_url: str = "https://openlibrary.org", rate_limit_delay: float = 0.1):
        self.base_url = base_url.rstrip('/')
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Spinecat/1.0 (Book Spine OCR Pipeline)',
            'Accept': 'application/json'
        })
        
        # Set up logging for debugging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def search_books(self, params: OpenLibrarySearchParams) -> List[Dict[str, Any]]:
        """Search for books using the Open Library API"""
        self._rate_limit()
        
        # Use the modern Open Library search API
        search_url = f"{self.base_url}/search.json"
        
        # Build query parameters - simplified for better compatibility
        query_params = {
            "q": params.query,
            "limit": min(params.limit, 50),  # Cap at 50 for API stability
            "offset": params.offset
        }
        
        try:
            response = self.session.get(search_url, params=query_params, timeout=15)
            
            # Log response for debugging
            logger.debug(f"Search URL: {response.url}")
            logger.debug(f"Response status: {response.status_code}")
            
            if response.status_code == 429:  # Rate limited
                logger.warning("Rate limited by Open Library API, waiting...")
                time.sleep(2)
                return []
            
            response.raise_for_status()
            
            data = response.json()
            docs = data.get("docs", [])
            
            # Log successful results
            logger.debug(f"Found {len(docs)} results for query: {params.query}")
            
            return docs
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Open Library API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in Open Library search: {e}")
            return []
    
    def search_by_title_author(self, title: str, author: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for books by title and optionally author"""
        # Build search query
        if author:
            query = f"title:\"{title}\" AND author:\"{author}\""
        else:
            query = f"title:\"{title}\""
        
        params = OpenLibrarySearchParams(
            query=query,
            limit=limit,
            fields=["key", "title", "author_name", "first_publish_year", "cover_i", "isbn", "publisher"]
        )
        
        return self.search_books(params)
    
    def search_by_isbn(self, isbn: str) -> List[Dict[str, Any]]:
        """Search for books by ISBN"""
        query = f"isbn:{isbn}"
        
        params = OpenLibrarySearchParams(
            query=query,
            limit=10,
            fields=["key", "title", "author_name", "first_publish_year", "cover_i", "isbn", "publisher"]
        )
        
        return self.search_books(params)
    
    def get_book_details(self, book_key: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific book"""
        self._rate_limit()
        
        book_url = f"{self.base_url}/works/{book_key}.json"
        
        try:
            response = self.session.get(book_url, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get book details for {book_key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting book details: {e}")
            return None
    
    def search_flexible(self, text: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Flexible search that tries multiple search strategies
        Useful for OCR text that might be jumbled or incomplete
        """
        if not text or not text.strip():
            return []
        
        text = text.strip()
        results = []
        
        # Strategy 1: Direct search (most likely to succeed)
        try:
            params = OpenLibrarySearchParams(query=text, limit=limit)
            direct_results = self.search_books(params)
            if direct_results:
                results.extend(direct_results)
        except Exception as e:
            logger.warning(f"Direct search failed for '{text}': {e}")
        
        # Strategy 2: Try with quotes for exact phrases (only if direct search didn't work well)
        if len(results) < limit // 2:
            try:
                quoted_text = f'"{text}"'
                params = OpenLibrarySearchParams(query=quoted_text, limit=limit//2)
                quoted_results = self.search_books(params)
                if quoted_results:
                    results.extend(quoted_results)
            except Exception as e:
                logger.warning(f"Quoted search failed for '{text}': {e}")
        
        # Strategy 3: Split into words and search (only if we still need more results)
        if len(results) < limit // 2:
            words = text.split()
            if len(words) >= 2:  # Changed from > 2 to >= 2 to handle 2-word cases
                # Try different combinations of words, starting with longer phrases
                for phrase_length in range(min(4, len(words)), 0, -1):  # Changed from 1 to 0 to include single words
                    for i in range(len(words) - phrase_length + 1):
                        phrase = " ".join(words[i:i+phrase_length])
                        if len(phrase) > 2 and len(results) < limit:  # Changed from > 3 to > 2 to include 3-letter words
                            try:
                                params = OpenLibrarySearchParams(query=phrase, limit=3)
                                phrase_results = self.search_books(params)
                                if phrase_results:
                                    results.extend(phrase_results)
                                    logger.debug(f"Phrase search successful for '{phrase}': {len(phrase_results)} results")
                            except Exception as e:
                                logger.debug(f"Phrase search failed for '{phrase}': {e}")
        
        # Remove duplicates and limit results
        seen_keys = set()
        unique_results = []
        for result in results:
            if result.get("key") not in seen_keys:
                seen_keys.add(result.get("key"))
                unique_results.append(result)
                if len(unique_results) >= limit:
                    break
        
        return unique_results
    
    def search_simple(self, text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Simple, reliable search method for basic queries
        """
        if not text or not text.strip():
            return []
        
        text = text.strip()
        
        try:
            # Use a simple, direct search approach
            search_url = f"{self.base_url}/search.json"
            query_params = {
                "q": text,
                "limit": min(limit, 20)
            }
            
            self._rate_limit()
            response = self.session.get(search_url, params=query_params, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                docs = data.get("docs", [])
                return docs
            else:
                logger.warning(f"Simple search failed with status {response.status_code} for '{text}'")
                return []
                
        except Exception as e:
            logger.error(f"Simple search failed for '{text}': {e}")
            return []
    
    def search_intelligent(self, text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Intelligent search that tries multiple strategies for OCR text
        """
        if not text or not text.strip():
            return []
        
        text = text.strip()
        results = []
        
        # Strategy 1: Try the full text
        full_results = self.search_simple(text, limit)
        if full_results:
            results.extend(full_results)
        
        # Strategy 2: If no results, try extracting the most promising words
        if not results and len(text.split()) > 1:
            words = text.split()
            
            # Priority 1: Look for title-like phrases (3+ consecutive words with proper case)
            for phrase_length in range(min(5, len(words)), 2, -1):
                for i in range(len(words) - phrase_length + 1):
                    phrase_words = words[i:i+phrase_length]
                    # Check if this looks like a book title
                    if (len(phrase_words) >= 3 and 
                        all(w[0].isupper() for w in phrase_words) and
                        all(len(w) > 2 for w in phrase_words)):
                        phrase = ' '.join(phrase_words)
                        phrase_results = self.search_simple(phrase, limit//2)
                        if phrase_results:
                            results.extend(phrase_results)
                            logger.info(f"Title-like phrase search successful for '{phrase}': {len(phrase_results)} results")
                            break
                if results:
                    break
            
            # Priority 2: Try other word combinations if no title-like phrases found
            if not results:
                for phrase_length in range(min(4, len(words)), 0, -1):
                    for i in range(len(words) - phrase_length + 1):
                        phrase = ' '.join(words[i:i+phrase_length])
                        if len(phrase) > 2:  # Only try meaningful phrases
                            phrase_results = self.search_simple(phrase, limit//2)
                            if phrase_results:
                                results.extend(phrase_results)
                                logger.info(f"General phrase search successful for '{phrase}': {len(phrase_results)} results")
                                break
                    if results:
                        break
        
        # Strategy 3: If still no results, try individual significant words
        if not results:
            significant_words = [w for w in text.split() if len(w) > 3 and w[0].isupper()]
            for word in significant_words[:3]:  # Try up to 3 significant words
                word_results = self.search_simple(word, limit//3)
                if word_results:
                    results.extend(word_results)
                    logger.info(f"Word search successful for '{word}': {len(word_results)} results")
        
        # Remove duplicates and limit results
        seen_keys = set()
        unique_results = []
        for result in results:
            if result.get("key") not in seen_keys:
                seen_keys.add(result.get("key"))
                unique_results.append(result)
                if len(unique_results) >= limit:
                    break
        
        logger.info(f"Intelligent search total results for '{text}': {len(unique_results)}")
        return unique_results
    
class OpenLibraryBookMapper:
    """Maps Open Library API responses to our data models"""
    
    @staticmethod
    def map_search_result(result: Dict[str, Any]) -> Dict[str, Any]:
        """Map a search result to our standardized format"""
        return {
            "key": result.get("key", ""),
            "title": result.get("title", ""),
            "author_name": result.get("author_name", []),
            "first_publish_year": result.get("first_publish_year"),
            "cover_i": result.get("cover_i"),
            "isbn": result.get("isbn", []),
            "publisher": result.get("publisher", []),
            "language": result.get("language", []),
            "subject": result.get("subject", []),
            "score": result.get("score", 0.0)
        }
    
    @staticmethod
    def map_work_details(work_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map detailed work information"""
        return {
            "key": work_data.get("key", ""),
            "title": work_data.get("title", ""),
            "author_name": work_data.get("authors", []),
            "first_publish_year": work_data.get("first_publish_year"),
            "cover_i": work_data.get("covers", [None])[0] if work_data.get("covers") else None,
            "isbn": work_data.get("isbn_13", []) + work_data.get("isbn_10", []),
            "publisher": work_data.get("publishers", []),
            "language": work_data.get("languages", []),
            "subject": work_data.get("subjects", []),
            "description": work_data.get("description", {}).get("value", ""),
            "excerpts": work_data.get("excerpts", []),
            "links": work_data.get("links", [])
        }

def create_open_library_client() -> OpenLibraryClient:
    """Factory function to create an Open Library client"""
    return OpenLibraryClient()
