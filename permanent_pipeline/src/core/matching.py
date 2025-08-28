"""
ML-based matching for comparing OCR text with Open Library books
Uses multiple strategies including fuzzy matching, semantic similarity, and token-based approaches
"""

import re
import logging
from typing import List, Tuple, Dict, Any, Set, Optional
from dataclasses import dataclass
from collections import Counter, defaultdict
import numpy as np
from rapidfuzz import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import unicodedata

# Import sentence transformers if available
try:
    import os
    # Suppress sentence transformers progress bars
    os.environ['SENTENCE_TRANSFORMERS_HOME'] = os.path.join(os.path.dirname(__file__), '..', '..', 'models')
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    
    from sentence_transformers import SentenceTransformer
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False

logger = logging.getLogger(__name__)

# Suppress sentence transformers logging
logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
logging.getLogger('transformers').setLevel(logging.WARNING)
logging.getLogger('torch').setLevel(logging.WARNING)

@dataclass
class MatchScore:
    """Represents a match score with metadata"""
    score: float
    match_type: str
    confidence: float
    metadata: Dict[str, Any] = None

class BookMatcher:
    """Advanced book matching using multiple ML strategies with asymmetric scoring"""
    
    def __init__(self, use_semantic_matching: bool = True):
        self.use_semantic_matching = use_semantic_matching
        self.semantic_model = None
        self.tfidf_vectorizer = None
        
        if use_semantic_matching and SEMANTIC_AVAILABLE:
            try:
                self.semantic_model = SentenceTransformer('all-mpnet-base-v2')
            except Exception as e:
                logger.warning(f"Failed to load semantic model: {e}")
                self.use_semantic_matching = False
        
        # Initialize TF-IDF vectorizer
        self.tfidf_vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=1000,
            stop_words='english'
        )
    
    def match_books(self, 
                   ocr_text: str, 
                   denoised_text: str, 
                   library_books: List[Dict[str, Any]],
                   top_k: int = 5) -> List[Tuple[Dict[str, Any], MatchScore]]:
        """
        Match OCR text with library books using asymmetric scoring strategy
        Returns: List of (book, match_score) tuples
        """
        if not library_books:
            return []
        
        # Prepare texts for matching
        search_texts = [denoised_text if denoised_text else ocr_text]
        if denoised_text and denoised_text != ocr_text:
            search_texts.append(ocr_text)
        
        # Get different text variations for better matching
        text_variations = self._generate_text_variations(search_texts[0])
        search_texts.extend(text_variations)
        
        # Calculate scores using different strategies
        all_scores = []
        
        for book in library_books:
            book_text = self._extract_book_text(book)
            
            # Check for exact title match first (highest priority)
            exact_title_match = self._check_exact_title_match(search_texts, book)
            if exact_title_match:
                match_score = MatchScore(
                    score=1.0,
                    match_type='exact',
                    confidence=1.0,
                    metadata={'reason': 'exact_title_match'}
                )
                all_scores.append((book, match_score))
                continue
            
            # Strategy 1: Character-by-character similarity (STRICT matching)
            char_scores = self._character_similarity(search_texts, book_text)
            
            # Strategy 2: Fuzzy string matching
            fuzzy_scores = self._fuzzy_match(search_texts, book_text)
            
            # Strategy 3: Token-based matching (LEXICAL SIMILARITY regardless of word order)
            token_scores = self._token_based_match(search_texts, book_text)
            
            # Strategy 4: Word order similarity (BONUS POINTS for same word order)
            word_order_scores = self._word_order_similarity(search_texts, book_text)
            
            # Strategy 5: Semantic similarity (if available)
            semantic_scores = []
            if self.use_semantic_matching:
                semantic_scores = self._semantic_similarity(search_texts, book_text)
            
            # Strategy 6: TF-IDF similarity
            tfidf_scores = self._tfidf_similarity(search_texts, book_text)
            
            # Strategy 7: Field-specific scoring (weight title matches higher)
            field_scores = self._calculate_field_scores(search_texts, book)
            
            # Combine scores using asymmetric scoring strategy
            combined_score = self._combine_scores_asymmetric(
                char_scores, fuzzy_scores, token_scores, word_order_scores, 
                semantic_scores, tfidf_scores, field_scores, search_texts[0], book
            )
            
            # Determine match type and confidence
            match_type, confidence = self._determine_match_type(combined_score)
            
            match_score = MatchScore(
                score=combined_score,
                match_type=match_type,
                confidence=confidence,
                metadata={
                    'char_scores': char_scores,
                    'fuzzy_scores': fuzzy_scores,
                    'token_scores': token_scores,
                    'word_order_scores': word_order_scores,
                    'semantic_scores': semantic_scores,
                    'tfidf_scores': tfidf_scores
                }
            )
            
            all_scores.append((book, match_score))
        
        # Sort by score and return top_k
        all_scores.sort(key=lambda x: x[1].score, reverse=True)
        return all_scores[:top_k]
    
    def _generate_text_variations(self, text: str) -> List[str]:
        """Generate variations of text for better matching"""
        variations = []
        
        # Remove common words that might interfere with matching
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = text.split()
        filtered_words = [w for w in words if w.lower() not in common_words]
        if filtered_words:
            variations.append(' '.join(filtered_words))
        
        # Try different word combinations
        if len(words) > 3:
            # First 3 words
            variations.append(' '.join(words[:3]))
            # Last 3 words
            variations.append(' '.join(words[-3:]))
            # Middle section
            if len(words) > 6:
                mid_start = len(words) // 2 - 1
                variations.append(' '.join(words[mid_start:mid_start + 3]))
        
        # Try with and without punctuation
        no_punct = re.sub(r'[^\w\s]', '', text)
        if no_punct != text:
            variations.append(no_punct)
        
        return variations
    
    def _extract_book_text(self, book: Dict[str, Any]) -> str:
        """Extract searchable text from book data"""
        parts = []
        
        # Title
        if book.get('title'):
            parts.append(book['title'])
        
        # Author names
        if book.get('author_name'):
            author_names = book['author_name'] if isinstance(book['author_name'], list) else [book['author_name']]
            for author in author_names:
                if author:
                    parts.append(author)
        
        # Publisher (lower weight)
        if book.get('publisher'):
            parts.append(book['publisher'])
        
        return ' '.join(parts)
    
    def _fuzzy_match(self, search_texts: List[str], book_text: str) -> List[float]:
        """Calculate fuzzy string matching scores"""
        scores = []
        
        for search_text in search_texts:
            # Clean and normalize texts for better matching
            clean_search = self._normalize_text(search_text)
            clean_book = self._normalize_text(book_text)
            
            # Token set ratio (handles word order differences) - most important for OCR
            token_set_score = fuzz.token_set_ratio(clean_search, clean_book) / 100.0
            
            # Partial ratio (handles partial matches)
            partial_score = fuzz.partial_ratio(clean_search, clean_book) / 100.0
            
            # Token sort ratio (handles anagram-like text)
            token_sort_score = fuzz.token_sort_ratio(clean_search, clean_book) / 100.0
            
            # Weighted ratio (handles OCR character errors)
            weighted_score = fuzz.WRatio(clean_search, clean_book) / 100.0
            
            # Use the best score, with preference for token_set for OCR
            best_score = max(token_set_score, partial_score, token_sort_score, weighted_score)
            
            # Cap scores for very short search texts vs long book texts
            if len(clean_search) < 10 and len(clean_book) > 50:
                best_score = min(best_score, 0.8)  # Cap at 0.8 for length mismatch
            
            scores.append(best_score)
        
        return scores
    
    def _token_based_match(self, search_texts: List[str], book_text: str) -> List[float]:
        """Calculate token-based matching scores - LEXICAL SIMILARITY regardless of word order"""
        scores = []
        
        for search_text in search_texts:
            search_tokens = set(search_text.lower().split())
            book_tokens = set(book_text.lower().split())
            
            if not search_tokens or not book_tokens:
                scores.append(0.0)
                continue
            
            # Jaccard similarity - measures lexical overlap regardless of order
            intersection = len(search_tokens.intersection(book_tokens))
            union = len(search_tokens.union(book_tokens))
            jaccard_score = intersection / union if union > 0 else 0.0
            
            # Token overlap - how much of search text is covered
            overlap_score = intersection / len(search_tokens) if search_tokens else 0.0
            
            # Weighted combination - this is the "lexical meaning vector" approach
            token_score = (jaccard_score * 0.6) + (overlap_score * 0.4)
            scores.append(token_score)
        
        return scores
    
    def _word_order_similarity(self, search_texts: List[str], book_text: str) -> List[float]:
        """Calculate word order similarity scores - BONUS POINTS for same word order"""
        scores = []
        
        for search_text in search_texts:
            search_words = search_text.lower().split()
            book_words = book_text.lower().split()
            
            if not search_words or not book_words:
                scores.append(0.0)
                continue
            
            # Calculate word order similarity
            order_score = self._calculate_word_order_score(search_words, book_words)
            scores.append(order_score)
        
        return scores
    
    def _calculate_word_order_score(self, search_words: List[str], book_words: List[str]) -> float:
        """Calculate how well words appear in the same order"""
        if not search_words or not book_words:
            return 0.0
        
        # Find the longest common subsequence (LCS) in order
        lcs_length = self._longest_common_subsequence(search_words, book_words)
        
        # Calculate order similarity based on LCS
        max_possible = min(len(search_words), len(book_words))
        if max_possible == 0:
            return 0.0
        
        # Base order score
        order_score = lcs_length / max_possible
        
        # Bonus for consecutive word matches (stronger ordering)
        consecutive_bonus = self._calculate_consecutive_bonus(search_words, book_words)
        
        # Combine base score with consecutive bonus
        final_score = order_score + (consecutive_bonus * 0.3)  # Bonus can add up to 0.3
        
        return min(1.0, final_score)
    
    def _longest_common_subsequence(self, words1: List[str], words2: List[str]) -> int:
        """Find the length of the longest common subsequence in order"""
        if not words1 or not words2:
            return 0
        
        # Dynamic programming approach for LCS
        m, n = len(words1), len(words2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if words1[i-1] == words2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        return dp[m][n]
    
    def _calculate_consecutive_bonus(self, search_words: List[str], book_words: List[str]) -> float:
        """Calculate bonus for consecutive word matches"""
        if len(search_words) < 2 or len(book_words) < 2:
            return 0.0
        
        # Find consecutive word pairs that match in order
        consecutive_matches = 0
        total_pairs = 0
        
        # Check search word pairs
        for i in range(len(search_words) - 1):
            pair = (search_words[i], search_words[i + 1])
            total_pairs += 1
            
            # Check if this pair appears consecutively in book words
            for j in range(len(book_words) - 1):
                if book_words[j] == pair[0] and book_words[j + 1] == pair[1]:
                    consecutive_matches += 1
                    break
        
        if total_pairs == 0:
            return 0.0
        
        return consecutive_matches / total_pairs
    
    def _semantic_similarity(self, search_texts: List[str], book_text: str) -> List[float]:
        """Calculate semantic similarity using sentence transformers"""
        if not self.semantic_model:
            return [0.0] * len(search_texts)
        
        try:
            # Encode texts
            all_texts = search_texts + [book_text]
            embeddings = self.semantic_model.encode(all_texts)
            
            # Calculate cosine similarity
            search_embeddings = embeddings[:len(search_texts)]
            book_embedding = embeddings[-1].reshape(1, -1)
            
            similarities = cosine_similarity(search_embeddings, book_embedding).flatten()
            return similarities.tolist()
            
        except Exception as e:
            logger.warning(f"Semantic similarity calculation failed: {e}")
            return [0.0] * len(search_texts)
    
    def _tfidf_similarity(self, search_texts: List[str], book_text: str) -> List[float]:
        """Calculate TF-IDF similarity"""
        try:
            # Fit and transform texts
            all_texts = search_texts + [book_text]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_texts)
            
            # Calculate cosine similarity
            search_vectors = tfidf_matrix[:len(search_texts)]
            book_vector = tfidf_matrix[-1]
            
            similarities = cosine_similarity(search_vectors, book_vector).flatten()
            return similarities.tolist()
            
        except Exception as e:
            logger.warning(f"TF-IDF similarity calculation failed: {e}")
            return [0.0] * len(search_texts)
    
    def _combine_scores_asymmetric(self, 
                                 char_scores: List[float],
                                 fuzzy_scores: List[float], 
                                 token_scores: List[float], 
                                 word_order_scores: List[float],
                                 semantic_scores: List[float], 
                                 tfidf_scores: List[float],
                                 field_scores: List[float],
                                 search_text: str,
                                 book: Dict[str, Any]) -> float:
        """
        Combine scores using asymmetric scoring strategy:
        - Measure how well the candidate is contained in OCR (not vice versa)
        - Focus on distinctive, meaningful tokens
        - Consider word order as bonus
        """
        # Get best scores from each strategy
        best_char = max(char_scores) if char_scores else 0.0
        best_fuzzy = max(fuzzy_scores) if fuzzy_scores else 0.0
        best_token = max(token_scores) if token_scores else 0.0
        best_word_order = max(word_order_scores) if word_order_scores else 0.0
        best_semantic = max(semantic_scores) if semantic_scores else 0.0
        best_tfidf = max(tfidf_scores) if tfidf_scores else 0.0
        best_field = max(field_scores) if field_scores else 0.0
        
        # Asymmetric scoring: focus on how well candidate is contained in OCR
        # Token-based matching is primary (lexical similarity regardless of order)
        base_score = best_token * 0.4
        
        # Character similarity for OCR error tolerance
        char_contribution = best_char * 0.25
        
        # Fuzzy matching for partial matches
        fuzzy_contribution = best_fuzzy * 0.20
        
        # Word order as bonus (not primary)
        word_order_bonus = best_word_order * 0.15
        
        # Semantic similarity for meaning-based matching
        semantic_contribution = best_semantic * 0.15
        
        # TF-IDF for keyword matching
        tfidf_contribution = best_tfidf * 0.10
        
        # Field-specific boost
        field_boost = best_field * 0.20
        
        # Combine all components
        combined_score = (base_score + char_contribution + fuzzy_contribution + 
                         word_order_bonus + semantic_contribution + tfidf_contribution + 
                         field_boost)
        
        # Apply asymmetric penalties
        # Penalize if search text is much longer than book text (OCR noise)
        search_length = len(search_text.split())
        book_length = len(book.get('title', '').split())
        if search_length > book_length * 2:
            combined_score *= 0.8
        
        # Penalize if only common words matched
        if best_token < 0.3 and best_char < 0.3:
            combined_score *= 0.7
        
        # Cap the score to prevent false perfect matches
        return min(combined_score, 0.95)
    
    def _calculate_field_scores(self, search_texts: List[str], book: Dict[str, Any]) -> List[float]:
        """Calculate field-specific scores with enhanced author matching"""
        field_scores = []
        
        for search_text in search_texts:
            search_lower = search_text.lower().strip()
            field_score = 0.0
            
            # Title matching (highest weight)
            if book.get('title'):
                title_lower = book['title'].lower().strip()
                title_score = self._calculate_field_match_score(search_lower, title_lower)
                field_score += title_score * 0.6  # Title gets 60% weight
            
            # Author matching (important for spine text)
            if book.get('author_name'):
                author_names = book['author_name'] if isinstance(book['author_name'], list) else [book['author_name']]
                for author in author_names:
                    if author:
                        author_lower = author.lower().strip()
                        author_score = self._calculate_field_match_score(search_lower, author_lower)
                        field_score += author_score * 0.3  # Author gets 30% weight
            
            # Publisher matching (lowest weight)
            if book.get('publisher'):
                publisher_lower = book['publisher'].lower().strip()
                publisher_score = self._calculate_field_match_score(search_lower, publisher_lower)
                field_score += publisher_score * 0.1  # Publisher gets 10% weight
            
            field_scores.append(field_score)
        
        return field_scores
    
    def _calculate_field_match_score(self, search_text: str, field_text: str) -> float:
        """Calculate match score for a specific field"""
        if not search_text or not field_text:
            return 0.0
        
        # Strategy 1: Exact match
        if search_text == field_text:
            return 1.0
        
        # Strategy 2: Contains match
        if search_text in field_text or field_text in search_text:
            # Calculate overlap ratio
            shorter = min(len(search_text), len(field_text))
            longer = max(len(search_text), len(field_text))
            overlap_ratio = shorter / longer
            
            # Require substantial overlap for high scores
            if overlap_ratio >= 0.7:  # At least 70% overlap
                return 0.7 + (overlap_ratio * 0.3)  # 0.7 to 1.0
            else:
                return overlap_ratio * 0.7  # Scale down for lower overlap
        
        # Strategy 3: Word overlap
        search_words = set(search_text.split())
        field_words = set(field_text.split())
        if search_words and field_words:
            intersection = search_words & field_words
            union = search_words | field_words
            jaccard_similarity = len(intersection) / len(union) if union else 0.0
            return jaccard_similarity * 0.7  # Scale down for word-level matches
        
        # Strategy 4: Fuzzy match for OCR errors
        fuzzy_score = fuzz.ratio(search_text, field_text) / 100.0
        return fuzzy_score * 0.6  # Scale down for fuzzy matches
    
    def _check_exact_title_match(self, search_texts: List[str], book: Dict[str, Any]) -> bool:
        """Check if any search text exactly matches the book title"""
        if not book.get('title'):
            return False
        
        book_title = book['title'].lower().strip()
        
        for search_text in search_texts:
            search_lower = search_text.lower().strip()
            
            # Exact match
            if search_lower == book_title:
                return True
        
        return False
    
    def _character_similarity(self, search_texts: List[str], book_text: str) -> List[float]:
        """Calculate character-by-character similarity scores"""
        scores = []
        
        for search_text in search_texts:
            if not search_text or not book_text:
                scores.append(0.0)
                continue
            
            # Normalize texts
            search_norm = self._normalize_text(search_text)
            book_norm = self._normalize_text(book_text)
            
            # Character-level similarity using Levenshtein distance
            max_len = max(len(search_norm), len(book_norm))
            if max_len == 0:
                scores.append(0.0)
                continue
            
            # Calculate character similarity
            char_similarity = 1.0 - (fuzz.ratio(search_norm, book_norm) / 100.0)
            
            # Length penalty for very different lengths
            length_ratio = min(len(search_norm), len(book_norm)) / max_len
            if length_ratio < 0.5:  # Very different lengths
                char_similarity *= 0.7
            
            scores.append(char_similarity)
        
        return scores
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for better fuzzy matching"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove common OCR artifacts
        text = re.sub(r'[^\w\s]', ' ', text)  # Remove punctuation
        text = re.sub(r'\s+', ' ', text)       # Normalize whitespace
        
        # Common OCR corrections
        text = text.replace('0', 'o').replace('1', 'l').replace('5', 's')
        text = text.replace('8', 'b').replace('6', 'g')
        
        return text.strip()
    
    def _determine_match_type(self, score: float) -> Tuple[str, float]:
        """Determine match type and confidence based on score"""
        if score >= 0.85:
            return 'exact', score
        elif score >= 0.70:
            return 'strong', score
        elif score >= 0.55:
            return 'moderate', score
        elif score >= 0.40:
            return 'weak', score
        else:
            return 'poor', score

def create_book_matcher(use_semantic_matching: bool = True) -> BookMatcher:
    """Factory function to create a BookMatcher instance"""
    return BookMatcher(use_semantic_matching=use_semantic_matching)
