#!/usr/bin/env python3
"""
Test script for the new advanced matching system
Demonstrates character n-gram + soft token matching for spine OCR
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from permanent_pipeline.src.core.matching_v2 import create_advanced_book_matcher

def test_advanced_matching():
    """Test the advanced matching system with the ChatGPT example"""
    
    # Sample catalog (simulating Open Library results)
    catalog = [
        {
            "title": "The Ballad of Songbirds and Snakes",
            "author_name": "Suzanne Collins",
            "key": "OL123456W"
        },
        {
            "title": "The Ballad of Reading Gaol",
            "author_name": "Oscar Wilde", 
            "key": "OL789012W"
        },
        {
            "title": "The Hunger Games",
            "author_name": "Suzanne Collins",
            "key": "OL345678W"
        },
        {
            "title": "A Ballad of the Republic",
            "author_name": "John Smith",
            "key": "OL901234W"
        },
        {
            "title": "Songbirds and Snakes",
            "author_name": "Jane Doe",
            "key": "OL567890W"
        }
    ]
    
    # OCR text from the ChatGPT example
    ocr_text = "THE BALLAD OF OLLINS SONGBIRDS AND SNAKES SCHOLASTIC PRESS"
    
    print("🧪 Testing Advanced Book Matching System")
    print("=" * 50)
    print(f"OCR Text: {ocr_text}")
    print(f"Catalog Size: {len(catalog)} books")
    print()
    
    # Create and fit the advanced matcher
    print("🔧 Initializing Advanced Book Matcher...")
    matcher = create_advanced_book_matcher(use_character_ngrams=True)
    
    print("📚 Fitting matcher to catalog...")
    matcher.fit(catalog)
    
    print("🔍 Running matching...")
    results = matcher.match_books(
        ocr_text=ocr_text,
        top_k=5,
        confidence_threshold=0.65
    )
    
    print("\n📊 Matching Results:")
    print("-" * 50)
    
    for i, (book, match_score) in enumerate(results, 1):
        print(f"{i}. {book['title']} by {book['author_name']}")
        print(f"   Score: {match_score.score:.3f} ({match_score.score*100:.1f}%)")
        print(f"   Type: {match_score.match_type}")
        print(f"   Confidence: {match_score.confidence:.3f}")
        
        # Show feature breakdown
        if match_score.metadata and 'features' in match_score.metadata:
            features = match_score.metadata['features']
            print(f"   Features:")
            print(f"     - Char TF-IDF: {features.get('char_tfidf_cosine', 0):.3f}")
            print(f"     - Token Set: {features.get('token_set_sim', 0):.3f}")
            print(f"     - Soft TF-IDF: {features.get('soft_tfidf_overlap', 0):.3f}")
            print(f"     - Author: {features.get('author_lastname_sim', 0):.3f}")
            print(f"     - Distinctive: {features.get('distinctive_token_coverage', 0):.3f}")
        
        print()
    
    # Test with different OCR variations
    print("🔄 Testing OCR Variations:")
    print("-" * 30)
    
    variations = [
        "THE BALLAD OF COLLINS SONGBIRDS AND SNAKES",
        "BALLAD SONGBIRDS SNAKES COLLINS",
        "SONGBIRDS AND SNAKES THE BALLAD OF COLLINS",
        "THE BALLAD OF SONG BIRDS AND SNAKES COLLINS"
    ]
    
    for variation in variations:
        print(f"\nOCR: {variation}")
        results = matcher.match_books(variation, top_k=3, confidence_threshold=0.5)
        if results:
            best = results[0]
            print(f"  Best: {best[0]['title']} (score: {best[1].score:.3f})")
        else:
            print("  No matches found")
    
    print("\n✅ Advanced matching test completed!")

if __name__ == "__main__":
    test_advanced_matching()


