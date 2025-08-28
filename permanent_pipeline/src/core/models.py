"""
Core data models for the Spinecat pipeline
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import json

@dataclass
class OCRResult:
    """Stores OCR result for a specific orientation"""
    text: str
    confidence: float
    angle: float
    bbox: List[List[int]]
    orientation: str

@dataclass
class SpineTextData:
    """Complete text data for a book spine"""
    book_id: str
    obb_data: Dict[str, Any]
    ocr_results: List[OCRResult]
    consolidated_text: str
    primary_orientation: str
    confidence_score: float
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class DenoisedText:
    """Denoised and cleaned OCR text"""
    original_text: str
    denoised_text: str
    confidence: float
    cleaning_steps: List[str]
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class OpenLibraryBook:
    """Book data from Open Library API"""
    key: str
    title: str
    author_name: List[str]
    first_publish_year: Optional[int]
    cover_i: Optional[int]
    isbn: List[str]
    publisher: List[str]
    language: List[str]
    subject: List[str]
    score: float = 0.0

@dataclass
class BookMatch:
    """Match between OCR text and library book"""
    ocr_text: str
    denoised_text: str
    library_book: OpenLibraryBook
    match_score: float
    match_type: str  # 'exact', 'fuzzy', 'ml_enhanced'
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class PipelineResult:
    """Complete pipeline result for a book spine"""
    spine_id: str
    spine_data: SpineTextData
    denoised_text: Optional[DenoisedText]
    matches: List[BookMatch]
    best_match: Optional[BookMatch]
    processing_time: float
    success: bool
    errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary"""
        return {
            'spine_id': self.spine_id,
            'spine_data': {
                'book_id': self.spine_data.book_id,
                'consolidated_text': self.spine_data.consolidated_text,
                'primary_orientation': self.spine_data.primary_orientation,
                'confidence_score': self.spine_data.confidence_score,
                'timestamp': self.spine_data.timestamp.isoformat()
            },
            'denoised_text': {
                'original_text': self.denoised_text.original_text if self.denoised_text else None,
                'denoised_text': self.denoised_text.denoised_text if self.denoised_text else None,
                'confidence': self.denoised_text.confidence if self.denoised_text else None,
                'cleaning_steps': self.denoised_text.cleaning_steps if self.denoised_text else []
            } if self.denoised_text else None,
            'matches': [
                {
                    'ocr_text': m.ocr_text,
                    'denoised_text': m.denoised_text,
                    'library_book': {
                        'key': m.library_book.key,
                        'title': m.library_book.title,
                        'author_name': m.library_book.author_name,
                        'first_publish_year': m.library_book.first_publish_year,
                        'isbn': m.library_book.isbn,
                        'publisher': m.library_book.publisher
                    },
                    'match_score': m.match_score,
                    'match_type': m.match_type,
                    'confidence': m.confidence
                }
                for m in self.matches
            ],
            'best_match': {
                'title': self.best_match.library_book.title,
                'author': self.best_match.library_book.author_name[0] if self.best_match.library_book.author_name else None,
                'match_score': self.best_match.match_score,
                'match_type': self.best_match.match_type
            } if self.best_match else None,
            'processing_time': self.processing_time,
            'success': self.success,
            'errors': self.errors,
            'timestamp': self.timestamp.isoformat()
        }

    def save_to_file(self, output_dir: str = "results"):
        """Save result to JSON file"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{self.spine_id}_pipeline_result.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        
        return filepath

