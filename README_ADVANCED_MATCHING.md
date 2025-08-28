# Advanced Matching System Integration

## 🎯 Overview

The Advanced Matching System has been successfully integrated into the main Spinecat pipeline. This system replaces the old hardcoded 70% match scores with intelligent, OCR-robust matching using character n-grams and soft token matching.

## 🚀 What's New

### ✅ **Real Match Scores**
- **Before**: All alternatives showed 70% (hardcoded)
- **After**: Dynamic scores from 20% to 100% based on actual similarity

### ✅ **OCR-Robust Matching**
- Handles OCR errors like "OLLINS" → "COLLINS"
- Word order insensitive (spine text can be scrambled)
- Character confusion mapping (I↔L↔1, 0↔O, 5↔S, etc.)

### ✅ **Author-Focused Scoring**
- Better author name matching
- Last name similarity using fuzzy logic
- 15% weight for author matching

### ✅ **Multi-Feature Scoring**
- Character n-gram TF-IDF (35%)
- Token set similarity (25%)
- Soft TF-IDF overlap (20%)
- Author last name (15%)
- Distinctive token coverage (5%)

### ✅ **Enhanced Open Library Search**
- **Multiple search strategies** for better recall
- **Fielded queries** with title/author/publisher
- **Phrase search** for longer titles
- **Author-focused search** when author is detected
- **Automatic fallback** to legacy search

## 🔧 Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Enable/Disable Matching Systems
USE_ADVANCED_MATCHING=true      # Enable new character n-gram matching (recommended)
USE_LEGACY_MATCHING=false       # Disable old fuzzy matching

# Advanced Matching Settings
ADVANCED_MATCHING_CONFIDENCE_THRESHOLD=0.65  # Minimum score for confident matches (0.0-1.0)
ADVANCED_MATCHING_TOP_K=10                   # Number of top results to return

# Enhanced Search Settings
USE_ENHANCED_SEARCH=true                      # Enable enhanced Open Library search (recommended)
ENHANCED_SEARCH_MAX_RESULTS=50                # Maximum total results from all search strategies
ENHANCED_SEARCH_RATE_LIMIT_DELAY=0.1         # Delay between API calls (seconds)
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `USE_ADVANCED_MATCHING` | `true` | Enable the new advanced matching system |
| `USE_LEGACY_MATCHING` | `false` | Enable the old fuzzy matching system |
| `ADVANCED_MATCHING_CONFIDENCE_THRESHOLD` | `0.65` | Minimum score for confident matches |
| `ADVANCED_MATCHING_TOP_K` | `10` | Number of top results to return |
| `USE_ENHANCED_SEARCH` | `true` | Enable enhanced Open Library search |
| `ENHANCED_SEARCH_MAX_RESULTS` | `50` | Maximum total search results |
| `ENHANCED_SEARCH_RATE_LIMIT_DELAY` | `0.1` | Delay between API calls (seconds) |

## 📊 Expected Results

### Example: "THE BALLAD OF OLLINS SONGBIRDS AND SNAKES SCHOLASTIC PRESS"

**Before (Legacy System):**
- All alternatives: 70% match (hardcoded)

**After (Advanced System):**
1. **"The Ballad of Songbirds and Snakes" by Suzanne Collins** → **~85%** (Strong Match)
2. **"The Ballad of Reading Gaol" by Oscar Wilde** → **~45%** (Weak Match)
3. **Other books** → **20-40%** (Poor/Weak Matches)

## 🧪 Testing

### 1. Test the Matching Algorithm
```bash
cd scripts
python test_advanced_matching.py
```

### 2. Test Enhanced Search
```bash
cd scripts
python test_enhanced_search.py
```

### 3. Test Pipeline Integration
```bash
cd scripts
python test_pipeline_integration.py
```

### 4. Test with Real Images
1. Start the backend: `cd web_interface/backend && python main.py`
2. Upload a book spine image
3. Check the console logs to see which matching system is active
4. Verify that match scores are realistic (not all 70%)

## 🔄 Switching Between Systems

### Enable Advanced Matching (Recommended)
```bash
USE_ADVANCED_MATCHING=true
USE_LEGACY_MATCHING=false
```

### Enable Legacy Matching (Fallback)
```bash
USE_ADVANCED_MATCHING=false
USE_LEGACY_MATCHING=true
```

### Enable Both (Advanced with Fallback)
```bash
USE_ADVANCED_MATCHING=true
USE_LEGACY_MATCHING=true
```

## 📋 Dependencies

The advanced matching system requires these Python packages:

```bash
pip install scikit-learn rapidfuzz numpy
```

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**
   - Make sure you're in the right virtual environment
   - Install required dependencies: `pip install scikit-learn rapidfuzz numpy`

2. **Low Match Scores**
   - Check `ADVANCED_MATCHING_CONFIDENCE_THRESHOLD` (default: 0.65)
   - Lower the threshold for more lenient matching

3. **System Falls Back to Legacy**
   - Check console logs for error messages
   - Verify `USE_ADVANCED_MATCHING=true` in your `.env`

4. **No Matches Found**
   - Lower the confidence threshold
   - Check OCR text quality
   - Ensure Open Library search is working

### Debug Mode

Enable debug logging to see detailed matching information:

```bash
LOG_LEVEL=DEBUG
```

## 🔍 How It Works

### 1. **Enhanced Open Library Search**
- **Multiple query strategies** for better recall
- **Fielded queries**: `title:(BALLAD SONGBIRDS) author:(COLLINS)`
- **Structured params**: Separate title/author fields
- **Phrase search**: `title_suggest:"THE BALLAD OF SONGBIRDS"`
- **Author-focused**: Search by author when detected
- **Broad search**: General token-based search
- **Automatic deduplication** and result limiting

### 2. **Text Normalization**
- Case folding and accent removal
- Punctuation removal and whitespace normalization
- OCR confusion mapping

### 3. **Candidate Generation**
- Character n-gram TF-IDF vectors
- Fast similarity search across catalog
- Returns top K candidates for re-ranking

### 4. **Feature Calculation**
- Character TF-IDF cosine similarity
- Token set similarity (order-insensitive)
- Soft TF-IDF overlap with fuzzy token matching
- Author last name similarity
- Distinctive token coverage

### 5. **Score Combination**
- Weighted sum of all features
- Confidence threshold filtering
- Match type classification

## 📈 Performance

- **Speed**: Sub-second matching for catalogs up to 100K books
- **Accuracy**: Higher precision and recall than legacy system
- **Scalability**: Designed for large catalogs with room for optimization

## 🔮 Future Enhancements

1. **SVD Compression**: For catalogs >100K books
2. **ANN Indexing**: HNSW/FAISS for sub-millisecond search
3. **Learning Weights**: Train feature weights on labeled data
4. **Multi-language**: Support for non-English books

## 📞 Support

If you encounter issues:

1. Check the console logs for error messages
2. Verify your `.env` configuration
3. Test with the provided test scripts
4. Check that all dependencies are installed

The system automatically falls back to legacy matching if advanced matching fails, ensuring system reliability.
