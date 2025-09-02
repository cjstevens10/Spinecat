"""
OCR processor for book spines using Tesseract OCR
Handles multi-angle OCR and text extraction
"""

import cv2
import numpy as np
import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass

from .models import OCRResult, SpineTextData
from .easyocr_ocr import EasyOCREngine

logger = logging.getLogger(__name__)

@dataclass
class OCRProcessorConfig:
    """Configuration for OCR processing"""
    padding_pixels: int = 25
    angle_tolerance: float = 5.0
    min_text_length: int = 3
    confidence_threshold: float = 0.5

class MultiAngleOCRProcessor:
    """Handles multi-angle OCR for book spines with mixed orientations using EasyOCR"""
    
    # Class-level EasyOCR instance to avoid reloading
    _ocr_instance = None
    
    def __init__(self, easyocr_enabled: str = "easyocr_enabled", config: OCRProcessorConfig = None):
        """Initialize EasyOCR with appropriate settings"""
        self.config = config or OCRProcessorConfig()
        
        if MultiAngleOCRProcessor._ocr_instance is None:
            MultiAngleOCRProcessor._ocr_instance = EasyOCREngine()
        
        self.ocr = MultiAngleOCRProcessor._ocr_instance
    
    def extract_spine_region(self, image: np.ndarray, obb_data: Dict) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
        """Extracts the oriented spine region using larger padding but masking outside OBB"""
        x_center, y_center, width, height, rotation = obb_data['xywhr']
        
        # Create rotated rectangle for the OBB
        rect = ((x_center, y_center), (width, height), np.degrees(rotation))
        box_points = cv2.boxPoints(rect)
        box_points = box_points.astype(np.int32)
        
        # Get the bounding box that encompasses the rotated rectangle
        x, y, w, h = cv2.boundingRect(box_points)
        
        # Use larger padding to ensure we capture the full spine
        larger_padding = self.config.padding_pixels
        x1 = max(0, x - larger_padding)
        y1 = max(0, y - larger_padding)
        x2 = min(image.shape[1], x + w + larger_padding)
        y2 = min(image.shape[0], y + h + larger_padding)
        
        # Extract the rectangular region that contains the rotated spine
        spine_region = image[y1:y2, x1:x2]
        
        # Create a mask for the rotated rectangle (OBB area only)
        mask = np.zeros((y2-y1, x2-x1), dtype=np.uint8)
        
        # Adjust box points to the cropped region coordinates
        adjusted_points = box_points - np.array([x1, y1])
        
        # Fill the rotated rectangle area in the mask (this is the OBB)
        cv2.fillPoly(mask, [adjusted_points], 255)
        
        # Apply the mask to get ONLY the spine area (OBB + padding, but masked to OBB)
        if len(spine_region.shape) == 3:
            mask_3ch = np.stack([mask] * 3, axis=2)
            masked_spine = cv2.bitwise_and(spine_region, mask_3ch)
        else:
            masked_spine = cv2.bitwise_and(spine_region, mask)
        
        return masked_spine, (x1, y1, x2, y2)
    
    def run_ocr_at_angle(self, image: np.ndarray, angle: float) -> OCRResult:
        """Run OCR at a specific rotation angle"""
        # Skip rotation if angle is close to 0
        if abs(angle) < self.config.angle_tolerance:
            rotated_image = image
        else:
            height, width = image.shape[:2]
            center = (width // 2, height // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated_image = cv2.warpAffine(image, rotation_matrix, (width, height))
        
        # Run EasyOCR
        try:
            result = self.ocr.detect_text_advanced(rotated_image)
            
            # Debug logging
            logger.info(f"EasyOCR result: {result}")
            
            if result and result.get('success'):
                blocks = result.get('blocks', [])
                all_texts = []
                all_confidences = []
                
                # Process each text block
                for block in blocks:
                    if 'text' in block and block['text']:
                        block_text = block['text'].strip()
                        if block_text and len(block_text) > self.config.min_text_length:
                            all_texts.append(block_text)
                            # Use actual confidence from EasyOCR result
                            block_confidence = result.get('confidence', 0.8)
                            all_confidences.append(block_confidence)
                
                # If we found valid text blocks, combine them
                if all_texts:
                    combined_text = ' '.join(all_texts)
                    avg_confidence = sum(all_confidences) / len(all_confidences)
                    
                    # Determine orientation based on angle
                    if abs(angle) < 45:
                        orientation = 'horizontal'
                    elif abs(angle - 90) < 45:
                        orientation = 'vertical'
                    else:
                        orientation = 'angled'
                    
                    return OCRResult(
                        text=combined_text,
                        confidence=avg_confidence,
                        angle=angle,
                        bbox=[],
                        orientation=orientation
                    )
            
            # Return empty result if no text detected
            return OCRResult(
                text="",
                confidence=0.0,
                angle=angle,
                bbox=[],
                orientation='none'
            )
            
        except Exception as e:
            logger.warning(f"OCR error at angle {angle}: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                angle=angle,
                bbox=[],
                orientation='error'
            )

    def detect_mixed_orientations(self, spine_region: np.ndarray, obb_rotation: float) -> List[OCRResult]:
        """Detect text in multiple orientations on the same spine"""
        # Test only the most likely angles
        base_angle = np.degrees(obb_rotation)
        angles_to_test = [
            base_angle,           # Original orientation
            base_angle + 90,      # Perpendicular
        ]
        
        # Normalize angles to 0-360 range
        angles_to_test = [angle % 360 for angle in angles_to_test]
        
        ocr_results = []
        
        for angle in angles_to_test:
            result = self.run_ocr_at_angle(spine_region, angle)
            
            if result.text and result.confidence > self.config.confidence_threshold:
                ocr_results.append(result)
        
        return ocr_results

    def consolidate_text_results(self, ocr_results: List[OCRResult]) -> Tuple[str, str, float]:
        """Smart consolidation - prioritize complete text over fragments"""
        if not ocr_results:
            return "", "none", 0.0
        
        # Sort by confidence first
        sorted_results = sorted(ocr_results, key=lambda x: x.confidence, reverse=True)
        
        # Strategy: Look for the most complete text, not just highest confidence
        best_result = None
        best_score = 0
        
        for result in sorted_results:
            if not result.text:
                continue
                
            # Calculate a score that balances confidence and completeness
            text_length = len(result.text.strip())
            confidence = result.confidence
            completeness_score = text_length * confidence
            
            if completeness_score > best_score:
                best_score = completeness_score
                best_result = result
        
        if not best_result:
            return "", "none", 0.0
        
        # Return the most complete text
        final_text = best_result.text
        overall_orientation = best_result.orientation
        overall_confidence = best_result.confidence
        
        return final_text, overall_orientation, overall_confidence
    
    def process_spine(self, image: np.ndarray, obb_data: Dict, book_id: str) -> SpineTextData:
        """Process a single book spine through the complete OCR pipeline"""
        # Process spine
        
        # Extract spine region
        spine_region, bbox = self.extract_spine_region(image, obb_data)
        
        # Run multi-angle OCR
        ocr_results = self.detect_mixed_orientations(spine_region, obb_data['xywhr'][4])
        
        # Consolidate results
        consolidated_text, primary_orientation, confidence_score = self.consolidate_text_results(ocr_results)
        
        # Create result object
        spine_data = SpineTextData(
            book_id=book_id,
            obb_data=obb_data,
            ocr_results=ocr_results,
            consolidated_text=consolidated_text,
            primary_orientation=primary_orientation,
            confidence_score=confidence_score
        )
        
        # Final results
        
        return spine_data

def create_ocr_processor(easyocr_enabled: str = "easyocr_enabled", config: OCRProcessorConfig = None) -> MultiAngleOCRProcessor:
    """Factory function to create an OCR processor instance"""
    return MultiAngleOCRProcessor(easyocr_enabled, config)

