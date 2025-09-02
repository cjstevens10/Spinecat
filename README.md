# Spinecat

**Automated Book Spine Recognition and Library Matching System**

Spinecat is an intelligent system that automatically identifies books from photographs of book spines. It uses computer vision to detect book spines, extracts text using optical character recognition, cleans up the text, and matches it against a comprehensive library database to identify the books.

## What This System Does

When you take a photo of a bookshelf or a stack of books, Spinecat can:

1. **Detect individual book spines** in the image using a trained computer vision model
2. **Extract text** from each spine using advanced OCR technology
3. **Clean up the text** to fix common OCR errors and formatting issues
4. **Search a library database** to find matching books
5. **Provide detailed results** showing which books were identified

This is particularly useful for librarians, book collectors, or anyone who needs to quickly catalog or identify books from photographs.

## How the Pipeline Works

The system processes images through several interconnected stages:

### Stage 1: Spine Detection
The system uses a YOLO (You Only Look Once) computer vision model that has been specifically trained to recognize book spines in images. This model can detect spines even when they are rotated, angled, or partially obscured. It creates bounding boxes around each detected spine region.

### Stage 2: Text Extraction
For each detected spine, the system extracts the text using Google's Vision API, which provides high-quality optical character recognition. The system is smart enough to try multiple angles if the initial text extraction doesn't produce good results, since book spines can be oriented in different directions.

### Stage 3: Text Cleaning
OCR systems often make mistakes, especially with book spines that may have unusual fonts, colors, or orientations. The text cleaning stage fixes common problems like:
- Character recognition errors (confusing '0' with 'O', 'l' with '1', etc.)
- Jumbled word order that sometimes occurs with OCR
- Extra symbols or formatting artifacts
- Inconsistent spacing and punctuation

### Stage 4: Library Matching
The cleaned text is then searched against the Open Library database, which contains information about millions of books. The system uses advanced matching algorithms that can handle:
- Partial matches when only part of a title is visible
- Fuzzy matching to account for remaining OCR errors
- Character-level similarity using TF-IDF (Term Frequency-Inverse Document Frequency) analysis
- Multi-feature scoring that considers title similarity, author names, and other book metadata

### Stage 5: Results Generation
The system provides detailed results showing:
- Which spines were successfully identified
- Confidence scores for each match
- Alternative matches when the top result might not be correct
- Processing statistics and timing information

## System Architecture

The system consists of several key components that work together:

- **SpinecatPipeline**: The main coordinator that manages the entire process
- **MultiAngleOCRProcessor**: Handles text extraction with intelligent angle detection
- **TextDenoiser**: Cleans and corrects OCR output
- **OpenLibraryClient**: Searches the Open Library database
- **AdvancedBookMatcher**: Uses machine learning for accurate book matching

## Installation and Setup

### Requirements
- Python 3.8 or higher
- Google Vision API key (for OCR processing)
- Trained YOLO model file

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Spinecat
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your Google Vision API key**
   ```bash
   export GOOGLE_VISION_API_KEY="your_actual_api_key_here"
   ```

4. **Download required language data**
   ```bash
   python -c "import nltk; nltk.download('punkt'); nltk.download('words')"
   ```

## Usage

### Basic Usage

To process a single image using the pipeline directly:
```bash
python -c "
from permanent_pipeline.src.core.pipeline import create_pipeline
pipeline = create_pipeline()
results = pipeline.process_image('your_book_photo.jpg')
print(results)
"
```

### Web Interface

The system also includes a web interface for easier use:

1. **Start the backend server**
   ```bash
   cd web_interface/backend
   python main.py
   ```

2. **Start the frontend** (in a new terminal)
   ```bash
   cd web_interface
   npm start
   ```

3. **Open your browser** to `http://localhost:3000` and upload your book images

### Configuration Options

You can customize the system behavior through environment variables:

- `PADDING_PIXELS`: Amount of padding around detected spines (default: 25)
- `ANGLE_TOLERANCE`: Degrees before rotation is applied (default: 5.0)
- `CONFIDENCE_THRESHOLD`: Minimum confidence for spine detection (default: 0.3)
- `ADVANCED_MATCHING_CONFIDENCE_THRESHOLD`: Minimum confidence for book matches (default: 0.65)
- `ADVANCED_MATCHING_TOP_K`: Number of top matches to return (default: 10)

## Output Format

The system generates detailed JSON results for each processed image:

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

## Performance Characteristics

The system is designed for efficiency:

- **Spine Detection**: Approximately 100 milliseconds per image (with GPU acceleration)
- **Text Extraction**: Approximately 500 milliseconds per spine
- **Text Cleaning**: Approximately 50 milliseconds per text
- **Library Matching**: Approximately 200 milliseconds per spine
- **Total Processing Time**: 1-2 seconds per spine end-to-end

## Technical Details

### Machine Learning Components

The system uses several machine learning techniques:

- **YOLO Object Detection**: For identifying book spines in images
- **Character N-gram TF-IDF**: For robust text similarity matching that handles OCR errors
- **Multi-feature Scoring**: Combines multiple similarity measures for accurate matching
- **Confidence-based Classification**: Categorizes matches as exact, strong, moderate, weak, or poor

### Text Processing Pipeline

The text processing uses natural language processing techniques:

- **Tokenization**: Breaks text into meaningful units
- **Character-level Analysis**: Handles OCR character confusion patterns
- **Fuzzy Matching**: Accounts for spelling variations and OCR errors
- **Semantic Similarity**: Considers meaning beyond exact text matches

## Development and Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Test specific components
python -m permanent_pipeline.src.core.ocr_processor
python -m permanent_pipeline.src.core.denoising
```

### Project Structure

```
permanent_pipeline/
├── src/
│   └── core/
│       ├── models.py           # Data structures and models
│       ├── pipeline.py         # Main processing pipeline
│       ├── ocr_processor.py    # Text extraction logic
│       ├── denoising.py        # Text cleaning algorithms
│       ├── open_library.py     # Library database client
│       ├── matching_v2.py      # Advanced matching algorithms
│       └── config.py           # Configuration management

└── requirements.txt            # Python dependencies

web_interface/
├── backend/                    # FastAPI server
├── src/                        # React frontend
└── build/                      # Compiled frontend
```

## Common Issues

1. **Poor spine detection**: Try adjusting the confidence threshold or ensure good lighting in your images
2. **OCR errors**: The text cleaning system should handle most issues, but very blurry or low-contrast text may still cause problems
3. **No matches found**: Check that the book exists in the Open Library database, or try adjusting the matching confidence threshold

## Tools Used

This system builds upon several excellent open-source projects and services:

- **YOLOv8**: For the computer vision model used in spine detection
- **Google Vision API**: For high-quality optical character recognition
- **Open Library**: For the comprehensive book database
- **scikit-learn**: For machine learning algorithms and text processing
- **FastAPI**: For the web interface backend
- **React**: For the user interface frontend
