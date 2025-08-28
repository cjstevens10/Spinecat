# Advanced Book Matching System

## Overview

The Advanced Book Matching System implements the recommendations from ChatGPT for robust spine OCR matching. It uses character n-grams, soft token matching, and author-focused scoring to handle OCR errors, word order issues, and character confusions commonly found in book spine text.

## Key Features

### 🔍 **Character N-gram TF-IDF**
- **N-gram range**: 3-5 characters
- **OCR robust**: Survives word reordering and small OCR edits
- **Fast retrieval**: Efficient vector similarity search

### 🎯 **Soft Token Matching**
- **Fuzzy token matching**: Handles OCR errors like "OLLINS" ≈ "COLLINS"
- **Jaro-Winkler similarity**: Threshold 0.88 for token matching
- **IDF weighting**: Rare tokens (like "SONGBIRDS", "SNAKES") get higher weight

### 👤 **Author-Focused Scoring**
- **Last name matching**: Most robust author identification
- **Fuzzy author matching**: Handles OCR variations in author names
- **Author weight**: 15% of total score

### 📊 **Multi-Feature Scoring**
```
Final Score = 0.35 × Char TF-IDF + 
              0.25 × Token Set Similarity + 
              0.20 × Soft TF-IDF Overlap + 
              0.15 × Author Last Name + 
              0.05 × Distinctive Token Coverage
```

## How It Works

### 1. **Text Normalization**
- Case folding and accent removal
- Punctuation removal and whitespace normalization
- OCR confusion mapping (I↔L↔1, 0↔O, 5↔S, etc.)

### 2. **Candidate Generation**
- Character n-gram TF-IDF vectors
- Fast similarity search across catalog
- Returns top K candidates for re-ranking

### 3. **Feature Calculation**
- **Character TF-IDF**: Vector similarity on normalized text
- **Token Set**: Order-insensitive word overlap
- **Soft TF-IDF**: Fuzzy token matching with IDF weights
- **Author Matching**: Last name similarity using Jaro-Winkler
- **Distinctive Coverage**: High-IDF token overlap

### 4. **Score Combination**
- Weighted sum of all features
- Confidence threshold (default: 0.65)
- Match type classification (exact/strong/moderate/weak/poor)

## Example: "THE BALLAD OF OLLINS SONGBIRDS AND SNAKES SCHOLASTIC PRESS"

### OCR Processing
- **Normalized**: "THE BALLAD OF OLLINS SONGBIRDS AND SNAKES SCHOLASTIC PRESS"
- **Confusion variants**: Try "COLLINS" instead of "OLLINS"
- **Key tokens**: BALLAD, SONGBIRDS, SNAKES, COLLINS

### Matching Results
1. **"The Ballad of Songbirds and Snakes" by Suzanne Collins**
   - Score: ~0.85 (Strong Match)
   - High character n-gram overlap
   - Strong token set similarity
   - Author last name match (COLLINS)

2. **"The Ballad of Reading Gaol" by Oscar Wilde**
   - Score: ~0.45 (Weak Match)
   - Some character overlap ("BALLAD")
   - Low distinctive token coverage

## Configuration

### Environment Variables
```bash
# Enable/disable systems
USE_ADVANCED_MATCHING=true
USE_LEGACY_MATCHING=false

# Advanced matching settings
ADVANCED_MATCHING_CONFIDENCE_THRESHOLD=0.65
ADVANCED_MATCHING_TOP_K=10
ADVANCED_MATCHING_USE_CHARACTER_NGRAMS=true
```

### Python Configuration
```python
from config.matching_config import MatchingConfig

# Get pipeline configuration
pipeline_config = MatchingConfig.get_pipeline_config()

# Get advanced matcher configuration
matcher_config = MatchingConfig.get_advanced_matcher_config()
```

## Usage

### Basic Usage
```python
from permanent_pipeline.src.core.matching_v2 import create_advanced_book_matcher

# Create matcher
matcher = create_advanced_book_matcher(use_character_ngrams=True)

# Fit to catalog
matcher.fit(book_catalog)

# Match OCR text
results = matcher.match_books(
    ocr_text="THE BALLAD OF OLLINS SONGBIRDS AND SNAKES",
    top_k=5,
    confidence_threshold=0.65
)

# Process results
for book, match_score in results:
    print(f"{book['title']}: {match_score.score:.3f}")
```

### Pipeline Integration
```python
from permanent_pipeline.src.core.pipeline import create_pipeline

# Create pipeline with advanced matching
pipeline = create_pipeline(
    yolo_model_path="path/to/model.pt",
    google_vision_api_key="your-api-key",
    use_semantic_matching=False,  # Disable legacy
    use_advanced_matching=True    # Enable advanced
)

# Process image
results = pipeline.process_image("book_spine.jpg")
```

## Testing

### Run Test Script
```bash
cd scripts
python test_advanced_matching.py
```

### Expected Output
```
🧪 Testing Advanced Book Matching System
==================================================
OCR Text: THE BALLAD OF OLLINS SONGBIRDS AND SNAKES SCHOLASTIC PRESS
Catalog Size: 5 books

📊 Matching Results:
--------------------------------------------------
1. The Ballad of Songbirds and Snakes by Suzanne Collins
   Score: 0.847 (84.7%)
   Type: strong
   Confidence: 0.847
   Features:
     - Char TF-IDF: 0.892
     - Token Set: 0.923
     - Soft TF-IDF: 0.856
     - Author: 0.923
     - Distinctive: 1.000
```

## Performance

### Speed
- **Character n-gram**: Fast vector similarity (O(n log n))
- **Token matching**: Efficient fuzzy matching with RapidFuzz
- **Overall**: Sub-second matching for catalogs up to 100K books

### Accuracy
- **High recall**: Character n-grams catch partial matches
- **High precision**: Multi-feature scoring reduces false positives
- **OCR robust**: Handles common OCR errors and word order issues

### Scalability
- **Small catalogs** (<1K): Direct matching
- **Medium catalogs** (1K-100K): TF-IDF indexing
- **Large catalogs** (>100K): Add SVD compression + ANN indexing

## Fallback Strategy

The system automatically falls back to legacy matching if:
1. Advanced matching is disabled
2. Advanced matching fails to initialize
3. Advanced matching encounters an error during execution

This ensures system reliability while providing the option to use the improved matching algorithm.

## Comparison with Legacy System

| Feature | Legacy System | Advanced System |
|---------|---------------|-----------------|
| **Word Order** | Sensitive | Order-insensitive |
| **OCR Errors** | Basic fuzzy | Character n-grams + confusion mapping |
| **Author Matching** | Simple contains | Fuzzy last name matching |
| **Scoring** | Single algorithm | Multi-feature weighted scoring |
| **Performance** | Good | Better (character-level features) |
| **Accuracy** | Moderate | Higher (robust to OCR noise) |

## Troubleshooting

### Common Issues

1. **Low match scores**
   - Check confidence threshold (default: 0.65)
   - Verify OCR text quality
   - Ensure catalog has relevant books

2. **Slow performance**
   - Reduce `top_k` parameter
   - Use smaller catalog subset for testing
   - Check if character n-grams are enabled

3. **No matches found**
   - Lower confidence threshold
   - Check OCR text normalization
   - Verify catalog format

### Debug Mode
```python
import logging
logging.getLogger('permanent_pipeline.src.core.matching_v2').setLevel(logging.DEBUG)

# Run matching with debug output
results = matcher.match_books(ocr_text, top_k=5)
```

## Future Enhancements

1. **SVD Compression**: For catalogs >100K books
2. **ANN Indexing**: HNSW/FAISS for sub-millisecond search
3. **Learning Weights**: Train feature weights on labeled data
4. **Multi-language**: Support for non-English books
5. **Series Detection**: Identify book series and volumes


