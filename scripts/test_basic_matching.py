#!/usr/bin/env python3
"""
Basic test script for the advanced matching system
Tests core logic without external ML dependencies
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_basic_matching_logic():
    """Test the basic matching logic without ML dependencies"""
    
    print("🧪 Testing Basic Matching Logic")
    print("=" * 40)
    
    # Test text normalization
    print("📝 Testing Text Normalization:")
    
    test_cases = [
        "THE BALLAD OF OLLINS SONGBIRDS AND SNAKES SCHOLASTIC PRESS",
        "The Ballad of Songbirds & Snakes",
        "SONGBIRDS AND SNAKES - COLLINS",
        "BALLAD OF SONG BIRDS AND SNAKES"
    ]
    
    for text in test_cases:
        normalized = normalize_text_simple(text)
        print(f"  '{text}' -> '{normalized}'")
    
    print("\n🔍 Testing Token Extraction:")
    for text in test_cases:
        tokens = extract_tokens_simple(text)
        print(f"  '{text}' -> {tokens}")
    
    print("\n🎯 Testing OCR Confusion Handling:")
    confusion_tests = [
        "OLLINS", "COLLINS", "SONGBIRDS", "BALLAD"
    ]
    
    for text in confusion_tests:
        variants = generate_confusion_variants_simple(text)
        print(f"  '{text}' -> {variants}")
    
    print("\n✅ Basic matching logic test completed!")

def normalize_text_simple(text):
    """Simple text normalization without external dependencies"""
    if not text:
        return ""
    
    # Basic normalization
    s = text.upper()
    s = s.replace("&", " AND ")
    s = s.replace("'", "'")
    s = s.replace("-", " ")
    s = s.replace("_", " ")
    
    # Remove punctuation, keep alphanumeric and spaces
    import re
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    
    return s

def extract_tokens_simple(text):
    """Simple token extraction"""
    normalized = normalize_text_simple(text)
    tokens = [t for t in normalized.split() if len(t) > 1]
    return tokens

def generate_confusion_variants_simple(text):
    """Simple OCR confusion handling"""
    variants = [text]
    
    # Basic OCR confusions
    confusions = {
        "I": ["L", "1"],
        "L": ["I", "1"],
        "0": ["O"],
        "O": ["0"],
        "5": ["S"],
        "S": ["5"]
    }
    
    for original, replacements in confusions.items():
        if original in text:
            for replacement in replacements:
                variant = text.replace(original, replacement)
                if variant != text:
                    variants.append(variant)
    
    return list(set(variants))

def test_similarity_scoring():
    """Test basic similarity scoring logic"""
    print("\n📊 Testing Similarity Scoring:")
    
    # Test cases
    query = "THE BALLAD OF OLLINS SONGBIRDS AND SNAKES"
    candidates = [
        "THE BALLAD OF SONGBIRDS AND SNAKES SUZANNE COLLINS",
        "THE BALLAD OF READING GAOL OSCAR WILDE",
        "SONGBIRDS AND SNAKES JANE DOE",
        "THE HUNGER GAMES SUZANNE COLLINS"
    ]
    
    for candidate in candidates:
        score = calculate_simple_similarity(query, candidate)
        print(f"  Query: '{query}'")
        print(f"  Candidate: '{candidate}'")
        print(f"  Score: {score:.3f}")
        print()

def calculate_simple_similarity(query, candidate):
    """Simple similarity calculation"""
    query_tokens = set(extract_tokens_simple(query))
    candidate_tokens = set(extract_tokens_simple(candidate))
    
    if not query_tokens or not candidate_tokens:
        return 0.0
    
    # Jaccard similarity
    intersection = len(query_tokens & candidate_tokens)
    union = len(query_tokens | candidate_tokens)
    
    return intersection / union if union > 0 else 0.0

if __name__ == "__main__":
    test_basic_matching_logic()
    test_similarity_scoring()


