"""
Advanced OCR-robust book matching using character n-grams and soft token matching
Based on ChatGPT's recommendations for spine OCR matching
Focuses on title + author matching, excluding publisher/edition features
"""

import re
import unicodedata
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler

logger = logging.getLogger(__name__)

# Suppress sklearn logging
logging.getLogger('sklearn').setLevel(logging.WARNING)

@dataclass
class MatchScore:
    """Represents a match score with metadata"""
    score: float
    match_type: str
    confidence: float
    metadata: Dict[str, Any] = None

class AdvancedBookMatcher:
    """
    Advanced book matching using character n-grams and soft token matching
    Designed specifically for OCR spine text with word order issues
    """
    
    def __init__(self, use_character_ngrams: bool = True):
        self.use_character_ngrams = use_character_ngrams
        self.vectorizer = None
        self.corpus_matrix = None
        self.corpus_meta = []
        self.token_idf = {}
        self.is_fitted = False
        
        # Stop words to downweight (not delete)
        self.STOP_LOW = {
            "THE", "A", "AN", "OF", "AND", "PRESS", "PUBLISHING", 
            "BOOKS", "INC", "LTD", "CO", "CORP", "COMPANY"
        }
        
        # OCR confusion mappings (applied gently)
        self.OCR_CONFUSIONS = {
            "I": ["L", "1"],
            "L": ["I", "1"],
            "1": ["I", "L"],
            "0": ["O"],
            "O": ["0"],
            "5": ["S"],
            "S": ["5"],
            "8": ["B"],
            "B": ["8"],
            "6": ["G"],
            "G": ["6"],
            "Z": ["2"],
            "2": ["Z"]
        }
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for matching:
        - Case fold and remove accents
        - Replace & with AND
        - Remove punctuation, normalize whitespace
        - Apply OCR confusion mappings
        """
        if not text:
            return ""
        
        # Remove accents and case fold
        s = "".join(c for c in unicodedata.normalize("NFKD", text.upper()) 
                   if not unicodedata.combining(c))
        
        # Replace common variants
        s = s.replace("&", " AND ")
        s = s.replace("'", "'")
        s = s.replace("–", "-").replace("—", "-")
        
        # Remove punctuation, keep alphanumeric and spaces
        s = re.sub(r"[^A-Z0-9 ]+", " ", s)
        
        # Normalize whitespace
        s = re.sub(r"\s+", " ", s).strip()
        
        return s
    
    def generate_confusion_variants(self, text: str) -> List[str]:
        """
        Generate variants with common OCR confusions for better matching
        """
        variants = [text]
        
        # Apply OCR confusion mappings
        for original, confusions in self.OCR_CONFUSIONS.items():
            if original in text:
                for confusion in confusions:
                    variant = text.replace(original, confusion)
                    if variant != text:
                        variants.append(variant)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(variants))
    
    def extract_tokens(self, text: str) -> List[str]:
        """Extract meaningful tokens from normalized text"""
        tokens = text.split()
        # Filter out very short tokens and stop words (but keep them for context)
        return [t for t in tokens if len(t) > 1]
    
    def build_corpus(self, catalog: List[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Build normalized corpus from catalog entries
        Each entry becomes "TITLE AUTHOR" for matching
        """
        corpus = []
        meta = []
        
        for book in catalog:
            # Combine title and author
            title = book.get('title', '').strip()
            author = book.get('author_name', '')
            
            if isinstance(author, list):
                author = ' '.join(author)
            
            # Create base string: "TITLE AUTHOR"
            base = f"{title} {author}".strip()
            normalized = self.normalize_text(base)
            
            corpus.append(normalized)
            
            # Store metadata for scoring
            meta.append({
                "original_book": book,
                "norm": normalized,
                "tokens": self.extract_tokens(normalized),
                "title_norm": self.normalize_text(title),
                "author_norm": self.normalize_text(author),
                "author_last": self.extract_author_last_name(author)
            })
        
        return corpus, meta
    
    def extract_author_last_name(self, author: str) -> str:
        """Extract last name from author string"""
        if not author:
            return ""
        
        # Split and get last non-empty part
        parts = [p.strip() for p in author.split() if p.strip()]
        if not parts:
            return ""
        
        return parts[-1]
    
    def fit(self, catalog: List[Dict[str, Any]]):
        """
        Fit the matcher to a catalog of books
        Builds character n-gram TF-IDF vectors and token IDF weights
        """
        logger.info(f"Fitting AdvancedBookMatcher to {len(catalog)} books")
        
        # Build normalized corpus
        corpus, meta = self.build_corpus(catalog)
        self.corpus_meta = meta
        
        if self.use_character_ngrams:
            # Character n-gram TF-IDF (n=3-5)
            self.vectorizer = TfidfVectorizer(
                analyzer="char", 
                ngram_range=(3, 5),
                max_features=10000,
                min_df=2
            )
            self.corpus_matrix = self.vectorizer.fit_transform(corpus)
        
        # Build token-level IDF for soft TF-IDF scoring
        token_vectorizer = TfidfVectorizer(
            analyzer="word",
            max_features=5000,
            min_df=2
        )
        token_matrix = token_vectorizer.fit_transform(corpus)
        
        # Map token -> IDF weight
        self.token_idf = {}
        for token, idx in token_vectorizer.vocabulary_.items():
            token_upper = token.upper()
            idf_value = token_vectorizer.idf_[idx]
            # Downweight stop words
            if token_upper in self.STOP_LOW:
                idf_value *= 0.1
            self.token_idf[token_upper] = idf_value
        
        self.is_fitted = True
        logger.info("AdvancedBookMatcher fitted successfully")
    
    def soft_tfidf_overlap(self, query_tokens: List[str], candidate_tokens: List[str]) -> float:
        """
        Calculate soft TF-IDF overlap with fuzzy token matching
        Handles OCR errors like OLLINS ≈ COLLINS
        """
        if not query_tokens or not candidate_tokens:
            return 0.0
        
        used_candidate_tokens = set()
        total_idf = sum(self.token_idf.get(t, 1.0) for t in query_tokens)
        
        if total_idf == 0:
            return 0.0
        
        gained_idf = 0.0
        
        for query_token in query_tokens:
            best_similarity = 0.0
            best_candidate = None
            
            # Find best matching candidate token
            for candidate_token in candidate_tokens:
                if candidate_token in used_candidate_tokens:
                    continue
                
                # Use Jaro-Winkler for fuzzy matching
                similarity = JaroWinkler.normalized_similarity(query_token, candidate_token)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_candidate = candidate_token
            
            # If we found a good match (threshold 0.88)
            if best_similarity >= 0.88 and best_candidate:
                gained_idf += self.token_idf.get(query_token, 1.0)
                used_candidate_tokens.add(best_candidate)
        
        return gained_idf / total_idf
    
    def calculate_match_features(self, query_norm: str, candidate_norm: str, 
                               candidate_meta: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate all match features for a query-candidate pair
        """
        query_tokens = self.extract_tokens(query_norm)
        candidate_tokens = candidate_meta["tokens"]
        
        features = {}
        
        # 1. Character TF-IDF cosine similarity
        if self.use_character_ngrams and self.vectorizer:
            query_vec = self.vectorizer.transform([query_norm])
            candidate_vec = self.vectorizer.transform([candidate_norm])
            features['char_tfidf_cosine'] = float(
                cosine_similarity(query_vec, candidate_vec)[0][0]
            )
        else:
            features['char_tfidf_cosine'] = 0.0
        
        # 2. Token set similarity (order-insensitive)
        features['token_set_sim'] = fuzz.token_set_ratio(query_norm, candidate_norm) / 100.0
        
        # 3. Soft TF-IDF overlap with fuzzy token matching
        features['soft_tfidf_overlap'] = self.soft_tfidf_overlap(query_tokens, candidate_tokens)
        
        # 4. Author last name similarity
        author_last = candidate_meta["author_last"]
        if author_last:
            # Try to find author last name in query
            best_author_sim = 0.0
            for query_token in query_tokens:
                if len(query_token) > 2:  # Only meaningful tokens
                    sim = JaroWinkler.normalized_similarity(query_token, author_last)
                    best_author_sim = max(best_author_sim, sim)
            features['author_lastname_sim'] = best_author_sim
        else:
            features['author_lastname_sim'] = 0.0
        
        # 5. Distinctive token coverage
        # Count how many high-IDF tokens from query appear in candidate
        high_idf_tokens = [t for t in query_tokens if self.token_idf.get(t, 0) > 2.0]
        if high_idf_tokens:
            covered = 0
            for token in high_idf_tokens:
                # Check if any candidate token is similar enough
                for cand_token in candidate_tokens:
                    if JaroWinkler.normalized_similarity(token, cand_token) >= 0.88:
                        covered += 1
                        break
            features['distinctive_token_coverage'] = covered / len(high_idf_tokens)
        else:
            features['distinctive_token_coverage'] = 0.0
        
        return features
    
    def combine_features(self, features: Dict[str, float]) -> float:
        """
        Combine features into final score using weighted sum
        Weights tuned for spine OCR matching
        """
        weights = {
            'char_tfidf_cosine': 0.35,
            'token_set_sim': 0.25,
            'soft_tfidf_overlap': 0.20,
            'author_lastname_sim': 0.15,
            'distinctive_token_coverage': 0.05
        }
        
        score = 0.0
        for feature, weight in weights.items():
            score += features.get(feature, 0.0) * weight
        
        return min(score, 1.0)  # Cap at 1.0
    
    def determine_match_type(self, score: float) -> Tuple[str, float]:
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
    
    def match_books(self, ocr_text: str, top_k: int = 10, 
                    confidence_threshold: float = 0.65) -> List[Tuple[Dict[str, Any], MatchScore]]:
        """
        Match OCR text to books in the fitted catalog
        
        Args:
            ocr_text: Raw OCR text from spine
            top_k: Number of top results to return
            confidence_threshold: Minimum score to consider a confident match
            
        Returns:
            List of (book, match_score) tuples sorted by score
        """
        if not self.is_fitted:
            raise ValueError("Matcher must be fitted before matching")
        
        if not ocr_text or not ocr_text.strip():
            return []
        
        logger.info(f"Matching OCR text: '{ocr_text}'")
        
        # Normalize OCR text
        ocr_norm = self.normalize_text(ocr_text)
        logger.debug(f"Normalized OCR: '{ocr_norm}'")
        
        # Generate confusion variants
        variants = self.generate_confusion_variants(ocr_norm)
        logger.debug(f"Generated {len(variants)} OCR variants")
        
        # Score all candidates
        all_scores = []
        
        for i, candidate_meta in enumerate(self.corpus_meta):
            candidate_norm = candidate_meta["norm"]
            
            # Try all OCR variants and keep best score
            best_score = 0.0
            best_features = {}
            
            for variant in variants:
                features = self.calculate_match_features(variant, candidate_norm, candidate_meta)
                score = self.combine_features(features)
                
                if score > best_score:
                    best_score = score
                    best_features = features
            
            if best_score > 0:  # Only include non-zero scores
                all_scores.append((i, best_score, best_features))
        
        # Sort by score (highest first)
        all_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Convert to results
        results = []
        for idx, score, features in all_scores[:top_k]:
            book = self.corpus_meta[idx]["original_book"]
            match_type, confidence = self.determine_match_type(score)
            
            match_score = MatchScore(
                score=score,
                match_type=match_type,
                confidence=confidence,
                metadata={
                    'features': features,
                    'ocr_normalized': ocr_norm,
                    'candidate_normalized': self.corpus_meta[idx]["norm"]
                }
            )
            
            results.append((book, match_score))
        
        # Check if top result meets confidence threshold
        if results and results[0][1].score >= confidence_threshold:
            logger.info(f"Confident match found: {results[0][0].get('title', 'Unknown')} (score: {results[0][1].score:.3f})")
        else:
            if results:
                logger.info(f"No confident match found. Top score: {results[0][1].score:.3f}")
            else:
                logger.info("No confident match found. No results.")
        
        return results

def create_advanced_book_matcher(use_character_ngrams: bool = True) -> AdvancedBookMatcher:
    """Factory function to create an AdvancedBookMatcher instance"""
    return AdvancedBookMatcher(use_character_ngrams=use_character_ngrams)
