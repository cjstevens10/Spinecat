"""
Main pipeline orchestrator for the complete Spinecat system
Coordinates spine detection, OCR, denoising, and library matching
"""

import time
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO

from .models import (
    SpineTextData, DenoisedText, OpenLibraryBook, BookMatch, 
    PipelineResult, OCRResult
)
from .denoising import TextDenoiser
from .open_library import OpenLibraryClient, OpenLibraryBookMapper

from .matching_v2 import AdvancedBookMatcher, create_advanced_book_matcher
from .ocr_processor import MultiAngleOCRProcessor

logger = logging.getLogger(__name__)

class SpinecatPipeline:
    """Complete pipeline for book spine processing"""
    
    def __init__(self, 
                 yolo_model_path: str,
                 google_vision_api_key: str):
        """
        Initialize the pipeline
        
        Args:
            yolo_model_path: Path to trained YOLO model
            google_vision_api_key: Google Vision API key
        """
        self.yolo_model_path = yolo_model_path
        self.google_vision_api_key = google_vision_api_key
        
        # Initialize components
        self.yolo_model = None
        self.ocr_processor = None
        self.denoiser = None
        self.library_client = None
        self.advanced_book_matcher = None
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all pipeline components"""
        try:
            # Load YOLO model
            logger.info(f"Loading YOLO model from {self.yolo_model_path}")
            self.yolo_model = YOLO(self.yolo_model_path)
            logger.info("YOLO model loaded successfully")
            
            # Initialize OCR processor
            logger.info("Initializing EasyOCR processor")
            self.ocr_processor = MultiAngleOCRProcessor("easyocr_enabled")
            
            # Initialize text denoiser
            logger.info("Initializing text denoiser")
            self.denoiser = TextDenoiser()
            
            # Initialize Open Library client
            logger.info("Initializing Open Library client")
            self.library_client = OpenLibraryClient()
            
            # Initialize advanced book matcher
            logger.info("Initializing advanced book matcher (character n-gram)")
            self.advanced_book_matcher = create_advanced_book_matcher(use_character_ngrams=True)
            
            logger.info("All pipeline components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize pipeline components: {e}")
            raise
    
    def process_image(self, image_path: str, conf_threshold: float = 0.3, progress_callback=None) -> List[PipelineResult]:
        """
        Process a complete image through the entire pipeline
        
        Args:
            image_path: Path to image file
            conf_threshold: YOLO confidence threshold
            progress_callback: Optional callback function for progress updates
            
        Returns:
            List of pipeline results for each detected spine
        """
        logger.info(f"Starting pipeline processing for {image_path}")
        start_time = time.time()
        
        try:
            # Step 1: Detect book spines
            if progress_callback:
                progress_callback(20, "Detecting book spines with YOLO...")
            
            detections = self._detect_spines(image_path, conf_threshold)
            if not detections:
                logger.warning("No book spines detected")
                return []
            
            logger.info(f"Detected {len(detections)} book spines")
            
            if progress_callback:
                progress_callback(30, f"Detected {len(detections)} book spines. Starting OCR processing...")
            
            # Step 2: Load image for processing
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Failed to load image: {image_path}")
            
            # Step 3: Process each spine
            results = []
            for i, detection in enumerate(detections):
                if progress_callback:
                    # Calculate progress: 30% to 70% for OCR processing
                    progress = 30 + (i / len(detections)) * 40
                    progress_callback(progress, f"OCR processing spine {i+1}/{len(detections)}")
                
                try:
                    result = self._process_single_spine(image, detection, i+1)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to process spine {i+1}: {e}")
                    # Create error result
                    error_result = self._create_error_result(detection, i+1, str(e))
                    results.append(error_result)
            
            if progress_callback:
                progress_callback(70, "OCR processing completed. Starting book matching...")
            
            total_time = time.time() - start_time
            logger.info(f"Pipeline completed in {total_time:.2f} seconds")
            
            if progress_callback:
                progress_callback(100, f"Processing complete! Found {len(detections)} spines.")
            
            return results
            
        except Exception as e:
            logger.error(f"Pipeline processing failed: {e}")
            raise
    
    def _detect_spines(self, image_path: str, conf_threshold: float) -> List[Dict[str, Any]]:
        """Detect book spines using YOLO model"""
        try:
            results = self.yolo_model(image_path, conf=conf_threshold, verbose=False)
            
            if not results or len(results) == 0:
                return []
            
            result = results[0]
            detections = []
            
            if hasattr(result, 'obb') and result.obb is not None:
                # OBB (Oriented Bounding Box) detections
                obb_xyxyxyxy = result.obb.xyxyxyxy.cpu().numpy()
                obb_conf = result.obb.conf.cpu().numpy()
                obb_cls = result.obb.cls.cpu().numpy()
                
                for i, (xyxyxyxy, conf, cls) in enumerate(zip(obb_xyxyxyxy, obb_conf, obb_cls)):
                    # Convert 8-point polygon to center, width, height, rotation
                    points = xyxyxyxy.reshape(4, 2)
                    center = np.mean(points, axis=0)
                    
                    # Calculate width and height
                    width = np.linalg.norm(points[1] - points[0])
                    height = np.linalg.norm(points[2] - points[1])
                    
                    # Calculate rotation angle
                    angle = np.arctan2(points[1][1] - points[0][1], points[1][0] - points[0][0])
                    
                    detection = {
                        'id': f'spine_{i+1}',
                        'xywhr': [float(center[0]), float(center[1]), float(width), float(height), float(angle)],
                        'xyxyxyxy': xyxyxyxy.tolist(),
                        'confidence': float(conf),
                        'class': int(cls)
                    }
                    detections.append(detection)
            
            # Sort by confidence
            detections.sort(key=lambda x: x['confidence'], reverse=True)
            return detections
            
        except Exception as e:
            logger.error(f"Spine detection failed: {e}")
            return []
    
    def _process_single_spine(self, image: np.ndarray, detection: Dict[str, Any], spine_id: int) -> PipelineResult:
        """Process a single book spine through the complete pipeline"""
        spine_start_time = time.time()
        
        try:
            # Step 1: Extract spine region and run OCR
            spine_data = self._extract_and_ocr_spine(image, detection, spine_id)
            
            # Step 2: Denoise OCR text
            denoised_text = self._denoise_text(spine_data.consolidated_text)
            
            # Step 3: Search Open Library
            library_books = self._search_library(denoised_text.denoised_text if denoised_text else spine_data.consolidated_text)
            
            # Step 4: Match books
            matches = self._match_books(spine_data.consolidated_text, denoised_text, library_books)
            
            # Step 5: Create pipeline result
            processing_time = time.time() - spine_start_time
            
            result = PipelineResult(
                spine_id=f"spine_{spine_id}",
                spine_data=spine_data,
                denoised_text=denoised_text,
                matches=matches,
                best_match=matches[0] if matches else None,
                processing_time=processing_time,
                success=True
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process spine {spine_id}: {e}")
            processing_time = time.time() - spine_start_time
            
            return PipelineResult(
                spine_id=f"spine_{spine_id}",
                spine_data=None,
                denoised_text=None,
                matches=[],
                best_match=None,
                processing_time=processing_time,
                success=False,
                errors=[str(e)]
            )
    
    def _extract_and_ocr_spine(self, image: np.ndarray, detection: Dict[str, Any], spine_id: int) -> SpineTextData:
        """Extract spine region and run OCR"""
        obb_data = {
            'xywhr': detection['xywhr'],
            'confidence': detection['confidence'],
            'class': detection['class']
        }
        
        return self.ocr_processor.process_spine(image, obb_data, f"spine_{spine_id}")
    
    def _denoise_text(self, text: str) -> Optional[DenoisedText]:
        """Denoise OCR text"""
        if not text or not text.strip():
            return None
        
        denoised_text, confidence, steps = self.denoiser.denoise_text(text)
        
        if denoised_text and denoised_text != text:
            return DenoisedText(
                original_text=text,
                denoised_text=denoised_text,
                confidence=confidence,
                cleaning_steps=[step.name for step in steps]
            )
        
        return None
    
    def _search_library(self, text: str) -> List[Dict[str, Any]]:
        """Search Open Library for matching books"""
        if not text or len(text.strip()) < 3:
            return []
        
        try:
            # Use flexible search for better results with OCR text
            results = self.library_client.search_flexible(text, limit=20)
            
            # Map results to our format
            mapped_results = []
            for result in results:
                mapped = OpenLibraryBookMapper.map_search_result(result)
                mapped_results.append(mapped)
            
            return mapped_results
            
        except Exception as e:
            logger.error(f"Library search failed: {e}")
            return []
    
    def _match_books(self, ocr_text: str, denoised_text: Optional[DenoisedText], library_books: List[Dict[str, Any]]) -> List[BookMatch]:
        """Match OCR text with library books using advanced or legacy matching"""
        if not library_books:
            return []
        
        try:
            # Get denoised text or fall back to OCR text
            search_text = denoised_text.denoised_text if denoised_text else ocr_text
            
            # Use advanced character n-gram matching
            logger.info("Using advanced character n-gram matching")
            
            # Fit the advanced matcher to the current library books
            self.advanced_book_matcher.fit(library_books)
            
            # Get matches using advanced matching
            matches = self.advanced_book_matcher.match_books(
                ocr_text=search_text,
                top_k=5,
                confidence_threshold=0.65
            )
            
            # Convert to BookMatch objects
            book_matches = []
            for book, match_score in matches:
                book_match = BookMatch(
                    ocr_text=ocr_text,
                    denoised_text=search_text,
                    library_book=OpenLibraryBook(**book),
                    match_score=match_score.score,
                    match_type=match_score.match_type,
                    confidence=match_score.confidence
                )
                book_matches.append(book_match)
            
            logger.info(f"Advanced matching found {len(book_matches)} matches")
            return book_matches
            
        except Exception as e:
            logger.error(f"Advanced matching failed: {e}")
            return []
    
    def get_alternatives(self, ocr_text: str, top_k: int = 10) -> List[tuple]:
        """
        Get alternative book matches using the same matching algorithm as the main pipeline
        This ensures consistency with the initial processing results
        
        Args:
            ocr_text: Raw OCR text from spine
            top_k: Number of top results to return
            
        Returns:
            List of (book, match_score) tuples sorted by score
        """
        try:
            # Get library books for matching
            logger.info(f"Searching for library books with OCR text: '{ocr_text}'")
            
            # Use flexible search for OCR text (handles jumbled/incomplete text better)
            # Reduce limit for better performance - we only need top_k results anyway
            search_limit = min(50, top_k * 3)  # Get 3x more than needed for better matching
            library_books = self.library_client.search_flexible(ocr_text, limit=search_limit)
            logger.info(f"Found {len(library_books) if library_books else 0} library books (search limit: {search_limit})")
            
            if library_books:
                logger.info(f"Sample book titles: {[book.get('title', 'Unknown')[:50] for book in library_books[:3]]}")
            
            if not library_books:
                logger.warning(f"No library books found for OCR text: {ocr_text}")
                return []
            
            # Use advanced character n-gram matching for alternatives
            logger.info("Using advanced character n-gram matching for alternatives")
            
            # Fit the advanced matcher to the current library books
            logger.info(f"Fitting advanced matcher to {len(library_books)} library books")
            self.advanced_book_matcher.fit(library_books)
            
            # Get matches using advanced matching
            logger.info(f"Running advanced matching with threshold 0.0")
            matches = self.advanced_book_matcher.match_books(
                ocr_text=ocr_text,
                top_k=top_k,
                confidence_threshold=0.0  # Lower threshold to get more alternatives
            )
            
            logger.info(f"Advanced matching found {len(matches)} alternatives")
            if matches:
                logger.info(f"Sample match scores: {[f'{m[1].score:.3f}' for m in matches[:3]]}")
            return matches
            
        except Exception as e:
            logger.error(f"Failed to get alternatives: {e}")
            return []
    
    def _create_error_result(self, detection: Dict[str, Any], spine_id: int, error_msg: str) -> PipelineResult:
        """Create a result object for failed processing"""
        return PipelineResult(
            spine_id=f"spine_{spine_id}",
            spine_data=None,
            denoised_text=None,
            matches=[],
            best_match=None,
            processing_time=0.0,
            success=False,
            errors=[error_msg]
        )
    
    def save_results(self, results: List[PipelineResult], output_dir: str = "results"):
        """Save all pipeline results to files"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        saved_files = []
        for result in results:
            if result.success:
                filepath = result.save_to_file(output_dir)
                saved_files.append(filepath)
        
        logger.info(f"Saved {len(saved_files)} results to {output_dir}")
        return saved_files

def create_pipeline(yolo_model_path: str, google_vision_api_key: str) -> SpinecatPipeline:
    """Factory function to create a SpinecatPipeline instance"""
    return SpinecatPipeline(yolo_model_path, google_vision_api_key)

