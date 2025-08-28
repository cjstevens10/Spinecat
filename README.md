# Spinecat 🐱📚

**Automated Book Spine OCR and Library Matching Pipeline**

Spinecat is a comprehensive system that automatically detects book spines in images, extracts text using Google Vision OCR, denoises the output, and matches it against the Open Library database using advanced ML techniques.

## 🚀 Features

- **YOLO-based Spine Detection**: Uses trained YOLOv8-OBB model for accurate book spine detection
- **Multi-Angle OCR**: Google Vision API with intelligent angle detection for rotated text
- **Advanced Text Denoising**: ML-powered cleaning of OCR artifacts and jumbled text
- **Smart Library Matching**: Multiple matching strategies including fuzzy, token-based, and semantic similarity
- **Comprehensive Pipeline**: End-to-end processing from image to matched book results
- **Rich CLI Interface**: Beautiful console output with progress tracking and detailed results

## 🏗️ Architecture

```
Image Input → YOLO Detection → OCR Extraction → Text Denoising → Open Library Search → ML Matching → Results
```

### Core Components

- **`SpinecatPipeline`**: Main orchestrator coordinating all components
- **`MultiAngleOCRProcessor`**: Handles OCR at multiple angles using Google Vision
- **`TextDenoiser`**: Cleans and reorders jumbled OCR text
- **`OpenLibraryClient`**: Searches Open Library API with flexible strategies
- **`BookMatcher`**: ML-based matching using multiple similarity algorithms

## 📦 Installation

### Prerequisites

- Python 3.8+
- Google Vision API key
- Trained YOLO model (`models/yolo-spine-obb-final2/weights/best.pt`)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Spinecat
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your API key
   GOOGLE_VISION_API_KEY=your_actual_api_key_here
   ```

4. **Download NLTK data** (first run will do this automatically)
   ```bash
   python -c "import nltk; nltk.download('punkt'); nltk.download('words')"
   ```

## 🎯 Usage

### Basic Usage

Process a single image:
```bash
python -m src.main process --image book_stack.jpg
```

### Advanced Options

```bash
# Custom confidence threshold
python -m src.main process --image book_stack.jpg --confidence 0.5

# Custom output directory
python -m src.main process --image book_stack.jpg --output my_results/

# Disable semantic matching (faster)
python -m src.main process --image book_stack.jpg --no-semantic

# Verbose logging
python -m src.main process --image book_stack.jpg --verbose

# Custom model path
python -m src.main process --image book_stack.jpg --model path/to/model.pt
```

### Configuration

The system can be configured via environment variables or a config file:

```bash
# Environment variables
export GOOGLE_VISION_API_KEY="your_key"
export PADDING_PIXELS=30
export USE_SEMANTIC_MATCHING=true

# Or use .env file
echo "GOOGLE_VISION_API_KEY=your_key" > .env
```

## 🔧 Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `PADDING_PIXELS` | 25 | Padding around detected spines |
| `ANGLE_TOLERANCE` | 5.0 | Degrees before rotation is applied |
| `CONFIDENCE_THRESHOLD` | 0.3 | YOLO detection confidence |
| `USE_SEMANTIC_MATCHING` | true | Enable semantic similarity |
| `OPEN_LIBRARY_RATE_LIMIT` | 0.1 | Seconds between API requests |

## 📊 Output

Results are saved to JSON files in the output directory:

```json
{
  "spine_id": "spine_1",
  "spine_data": {
    "book_id": "spine_1",
    "consolidated_text": "The Great Gatsby",
    "primary_orientation": "horizontal",
    "confidence_score": 0.95
  },
  "denoised_text": {
    "original_text": "The Great Gatsby",
    "denoised_text": "The Great Gatsby",
    "confidence": 1.0,
    "cleaning_steps": ["basic_cleaning", "validation"]
  },
  "best_match": {
    "title": "The Great Gatsby",
    "author": "F. Scott Fitzgerald",
    "match_score": 0.98,
    "match_type": "exact"
  },
  "processing_time": 2.34,
  "success": true
}
```

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

Test individual components:
```bash
# Test OCR processor
python -m src.core.ocr_processor

# Test text denoising
python -m src.core.denoising

# Test library matching
python -m src.core.matching
```

## 🔍 How It Works

### 1. Spine Detection
- YOLOv8-OBB model detects oriented bounding boxes for book spines
- Handles rotated and angled spines automatically

### 2. OCR Processing
- Extracts spine regions with intelligent padding
- Tests multiple rotation angles (0°, 90°, detected angle)
- Uses Google Vision API for high-quality text extraction

### 3. Text Denoising
- **Basic Cleaning**: Removes artifacts and normalizes text
- **OCR Error Correction**: Fixes common character recognition mistakes
- **Jumbled Text Reordering**: ML-based approach to fix word order issues
- **Noise Removal**: Eliminates irrelevant symbols and numbers
- **Validation**: Ensures text quality meets book title standards

### 4. Library Matching
- **Fuzzy Matching**: Handles OCR errors and typos
- **Token-based Matching**: Manages word order and partial matches
- **Semantic Similarity**: Uses sentence transformers for meaning-based matching
- **TF-IDF Similarity**: Keyword-based matching for technical titles

## 🚀 Performance

- **Detection**: ~100ms per image (GPU)
- **OCR**: ~500ms per spine
- **Denoising**: ~50ms per text
- **Matching**: ~200ms per spine (with semantic matching)
- **Total**: ~1-2 seconds per spine end-to-end

## 🛠️ Development

### Project Structure
```
src/
├── core/                 # Core pipeline components
│   ├── models.py        # Data models and structures
│   ├── pipeline.py      # Main pipeline orchestrator
│   ├── ocr_processor.py # OCR processing logic
│   ├── denoising.py     # Text denoising algorithms
│   ├── open_library.py  # Open Library API client
│   ├── matching.py      # ML-based matching
│   └── config.py        # Configuration management
├── main.py              # CLI interface
└── __init__.py          # Package initialization
```

### Adding New Components

1. **Create component module** in `src/core/`
2. **Add to pipeline** in `src/core/pipeline.py`
3. **Update models** if needed in `src/core/models.py`
4. **Add tests** in `tests/` directory

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **YOLOv8**: Ultralytics for the detection model
- **Google Vision API**: High-quality OCR capabilities
- **Open Library**: Comprehensive book database
- **Sentence Transformers**: Semantic similarity models

## 📞 Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Check the documentation
- Review the test examples

---

**Happy book hunting! 📚🔍**
