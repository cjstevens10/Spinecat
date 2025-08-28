"""
Text denoising and cleaning for OCR outputs
Handles jumbled text, out-of-order words, and OCR artifacts
"""

import re
import string
from typing import List, Tuple, Dict
from dataclasses import dataclass
from rapidfuzz import fuzz
import nltk
from nltk.corpus import words
from nltk.tokenize import word_tokenize
import logging

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/words')
except LookupError:
    nltk.download('words')

logger = logging.getLogger(__name__)

@dataclass
class DenoisingStep:
    """Represents a single denoising step"""
    name: str
    input_text: str
    output_text: str
    confidence: float
    metadata: Dict = None

class TextDenoiser:
    """Advanced text denoising for OCR outputs"""
    
    def __init__(self):
        self.common_book_words = {
            'book', 'novel', 'story', 'tale', 'volume', 'edition', 'series',
            'author', 'writer', 'published', 'publisher', 'press', 'company',
            'library', 'classics', 'modern', 'contemporary', 'fiction', 'nonfiction'
        }
        
        # Common OCR errors and their corrections
        self.ocr_corrections = {
            '0': 'O', '1': 'I', '5': 'S', '8': 'B', '6': 'G',
            'rn': 'm', 'cl': 'd', 'vv': 'w', 'nn': 'm'
        }
    
    def denoise_text(self, text: str) -> Tuple[str, float, List[DenoisingStep]]:
        """
        Simple denoising that ONLY fixes obvious OCR character errors
        Returns: (denoised_text, confidence, steps)
        """
        if not text or not text.strip():
            return "", 0.0, []
        
        original_text = text.strip()
        steps = []
        
        # Step 1: Basic cleaning (whitespace only)
        current_text = self._basic_cleaning_simple(original_text)
        steps.append(DenoisingStep("basic_cleaning", original_text, current_text, 0.9))
        
        # Step 2: Fix common OCR errors (ONLY character-level fixes)
        current_text, confidence = self._fix_ocr_errors_simple(current_text)
        steps.append(DenoisingStep("ocr_error_fix", steps[-1].output_text, current_text, confidence))
        
        # Step 3: That's it! No reordering, no phrase deletion, no "intelligent" processing
        
        return current_text, confidence, steps
    
    def _basic_cleaning_simple(self, text: str) -> str:
        """Simple basic cleaning - whitespace only"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        return text.strip()
    
    def _fix_ocr_errors_simple(self, text: str) -> Tuple[str, float]:
        """Fix ONLY obvious OCR character errors"""
        corrected_text = text
        
        # Apply character corrections
        for error, correction in self.ocr_corrections.items():
            corrected_text = corrected_text.replace(error, correction)
        
        # Only fix obvious character-level errors, nothing else
        confidence = 0.95 if corrected_text != text else 1.0
        return corrected_text, confidence
    
    def _basic_cleaning(self, text: str) -> Tuple[str, float]:
        """Basic text cleaning"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove non-printable characters
        text = ''.join(char for char in text if char.isprintable())
        
        # Fix common punctuation issues
        text = re.sub(r'([a-zA-Z])\s*([.,!?])', r'\1\2', text)
        
        # Remove leading/trailing punctuation
        text = text.strip(string.punctuation + ' ')
        
        confidence = 0.9 if text else 0.0
        return text, confidence
    
    def _fix_ocr_errors(self, text: str) -> Tuple[str, float]:
        """Fix common OCR character recognition errors"""
        corrected_text = text
        
        # Apply character corrections
        for error, correction in self.ocr_corrections.items():
            corrected_text = corrected_text.replace(error, correction)
        
        # Fix common word-level OCR errors
        corrected_text = re.sub(r'\b(\w+)\1\b', r'\1', corrected_text)  # Remove repeated words
        
        # Fix spacing issues around punctuation
        corrected_text = re.sub(r'\s*([.,!?;:])\s*', r'\1 ', corrected_text)
        
        confidence = 0.85 if corrected_text != text else 1.0
        return corrected_text, confidence
    
    def _reorder_jumbled_text(self, text: str) -> Tuple[str, float]:
        """Reorder jumbled or out-of-order text using ML-based approach"""
        words = word_tokenize(text)
        if len(words) <= 3:
            return text, 1.0  # Too short to reorder meaningfully
        
        # Check if the text is already well-ordered (most book spines are)
        original_score = self._score_text_ordering(text)
        if original_score >= 0.6:  # Lowered threshold - most book spines are readable as-is
            return text, original_score
        
        # Only try reordering if the original text scores poorly
        possible_orderings = self._generate_word_orderings(words)
        
        if not possible_orderings:
            return text, 1.0
        
        # Find the best ordering
        best_ordering = max(possible_orderings, key=lambda x: x[1])
        
        # Only use reordered text if it's significantly better
        if best_ordering[1] > original_score + 0.2:  # Require 20% improvement
            return best_ordering[0], best_ordering[1]
        else:
            return text, original_score  # Keep original if reordering doesn't help much
    
    def _generate_word_orderings(self, words: List[str]) -> List[Tuple[str, float]]:
        """Generate possible word orderings and score them"""
        if len(words) <= 3:
            return [(' '.join(words), 1.0)]
        
        # For longer texts, use sliding window approach
        orderings = []
        
        # Try different window sizes
        for window_size in range(2, min(6, len(words) + 1)):
            for i in range(len(words) - window_size + 1):
                window = words[i:i + window_size]
                
                # Generate permutations of the window
                from itertools import permutations
                for perm in permutations(window):
                    perm_text = ' '.join(perm)
                    score = self._score_text_ordering(perm_text)
                    orderings.append((perm_text, score))
        
        # Also try the original ordering
        original_text = ' '.join(words)
        original_score = self._score_text_ordering(original_text)
        orderings.append((original_text, original_score))
        
        # Return top 5 orderings
        orderings.sort(key=lambda x: x[1], reverse=True)
        return orderings[:5]
    
    def _score_text_ordering(self, text: str) -> float:
        """Score a text ordering based on various heuristics"""
        words = text.split()
        if not words:
            return 0.0
        
        score = 0.0
        
        # 1. English word frequency
        try:
            valid_words = sum(1 for word in words if word.lower() in words.words())
            score += (valid_words / len(words)) * 0.3
        except:
            pass
        
        # 2. Book title patterns
        # Titles often start with articles (The, A, An) or proper nouns
        if words and words[0].lower() in ['the', 'a', 'an']:
            score += 0.2
        
        # 3. Author name patterns (usually at the end)
        if len(words) >= 2:
            last_word = words[-1]
            if last_word[0].isupper() and len(last_word) > 2:
                score += 0.2
        
        # 4. Publisher patterns
        publisher_indicators = ['press', 'books', 'publishing', 'company', 'inc', 'ltd']
        for word in words:
            if word.lower() in publisher_indicators:
                score += 0.1
        
        # 5. Length-based scoring - prefer longer, more complete titles
        if 4 <= len(words) <= 15:  # Changed from 3 to 4 to prefer longer titles
            score += 0.2  # Increased weight for length
        
        # 6. NEW: Prefer complete, readable text over truncated text
        if len(words) >= 5:  # Bonus for longer, more complete titles
            score += 0.1
        
        return score
    
    def _remove_noise(self, text: str) -> Tuple[str, float]:
        """Remove OCR noise and artifacts - more intelligent approach"""
        if not text:
            return "", 0.0
        
        # Keep the original text for fallback
        original_text = text
        
        # Remove excessive punctuation (but keep some)
        text = re.sub(r'[.,!?;:]{3,}', '.', text)
        
        # Remove random single digits that are clearly noise (but keep meaningful numbers)
        text = re.sub(r'\b\d\b(?![a-zA-Z])', '', text)  # Single digit not followed by letter
        
        # Remove non-word characters at the beginning/end (but be more careful)
        text = re.sub(r'^[^a-zA-Z0-9]+', '', text)
        text = re.sub(r'[^a-zA-Z0-9]+$', '', text)
        
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        # If we removed too much, fall back to original
        if len(text) < len(original_text) * 0.5:
            text = original_text
        
        confidence = 0.9 if text else 0.0
        return text, confidence
    
    def _validate_text(self, text: str) -> Tuple[str, float]:
        """Final validation of denoised text - more lenient for OCR"""
        if not text or len(text) < 2:  # Reduced from 3 to 2
            return "", 0.0
        
        # Check if text contains meaningful content
        words = text.split()
        if len(words) < 1:  # Reduced from 2 to 1
            return "", 0.0
        
        # Check for minimum word length - more lenient
        if any(len(word) < 1 for word in words):  # Reduced from 2 to 1
            return "", 0.0
        
        # Check if text looks like a book title/author - more lenient
        has_proper_case = any(word[0].isupper() for word in words)
        has_meaningful_length = any(len(word) > 2 for word in words)  # Reduced from 3 to 2
        
        if has_proper_case and has_meaningful_length:
            confidence = 0.95
        elif has_proper_case or has_meaningful_length:
            confidence = 0.8
        else:
            confidence = 0.6  # Even low confidence text is kept
        
        return text, confidence
    
    def _extract_meaningful_text(self, text: str) -> str:
        """Extract meaningful text from noisy OCR using intelligent heuristics"""
        if not text:
            return ""
        
        words = text.split()
        if not words:
            return ""
        
        # Strategy 1: Look for book title patterns - prioritize title-like phrases
        meaningful_words = []
        
        # First, try to find title-like patterns (3+ consecutive words with proper case)
        for i in range(len(words) - 2):
            phrase_words = words[i:i+3]
            if (len(phrase_words) >= 3 and 
                all(w[0].isupper() for w in phrase_words) and
                all(len(w) > 2 for w in phrase_words)):
                meaningful_words = phrase_words
                break
        
        # Strategy 2: If no title pattern found, look for individual meaningful words
        if not meaningful_words:
            for i, word in enumerate(words):
                # Keep words that look like book titles
                if (word[0].isupper() and len(word) > 2) or \
                   (word.lower() in ['the', 'a', 'an', 'and', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by']) or \
                   (len(word) > 3):  # Keep longer words
                    meaningful_words.append(word)
        
        # Strategy 3: If we have very few meaningful words, try to extract the most promising ones
        if len(meaningful_words) < 2 and len(words) >= 2:
            # Look for the most promising word combinations
            for i in range(len(words) - 1):
                for j in range(i + 2, min(len(words) + 1, i + 5)):
                    phrase = words[i:j]
                    if len(phrase) > 2 and any(w[0].isupper() for w in phrase):
                        meaningful_words = phrase
                        break
                if len(meaningful_words) >= 2:
                    break
        
        # Strategy 4: If still no results, return the original text
        if not meaningful_words:
            return text
        
        return ' '.join(meaningful_words)

def create_denoiser() -> TextDenoiser:
    """Factory function to create a TextDenoiser instance"""
    return TextDenoiser()
