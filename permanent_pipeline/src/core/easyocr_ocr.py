#!/usr/bin/env python3
"""
EasyOCR Integration for Book Spine Training Data
Uses EasyOCR for high-quality text detection with better rotation handling
"""

import os
import json
import cv2
import numpy as np
import easyocr
from PIL import Image
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import List, Dict, Tuple, Optional
import base64
from pathlib import Path



class EasyOCREngine:
    """EasyOCR client for high-quality text detection with rotation handling"""
    
    def __init__(self, api_key: str = None, credentials_path: str = None):
        """Initialize EasyOCR with appropriate settings"""
        try:
            # Initialize EasyOCR reader with English language
            # Enable GPU if available, otherwise use CPU
            self.reader = easyocr.Reader(['en'], gpu=False)

            
        except Exception as e:
            raise
    
    def detect_text_advanced(self, image: np.ndarray) -> Dict:
        """Detect text using EasyOCR with full document analysis"""
        try:

            
            # Convert numpy array to PIL Image for better EasyOCR compatibility
            if len(image.shape) == 3:
                pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            else:
                pil_image = Image.fromarray(image)
            
            # Convert back to numpy array (EasyOCR expects RGB)
            rgb_image = np.array(pil_image)
            

            
            # Run EasyOCR with rotation detection
            results = self.reader.readtext(rgb_image, 
                                         rotation_info=[0, 90, 180, 270],  # Test multiple rotations
                                         paragraph=True,  # Group text into paragraphs
                                         detail=1)  # Get detailed information including bounding boxes
            

            
            return self._parse_easyocr_response(results, image.shape)
                
        except Exception as e:

            return {"error": str(e)}
    
    def _parse_easyocr_response(self, results: List, image_shape: Tuple) -> Dict:
        """Parse EasyOCR response into the same format as the original OCR"""
        try:
            blocks = []
            current_block = None
            current_block_bounds = []
            
            # Process each detected text element
            for result in results:
                # Handle different possible result formats
                if isinstance(result, list) and len(result) >= 2:
                    # EasyOCR format: [bbox, text] or [bbox, text, confidence]
                    bbox = result[0]
                    text = result[1]
                    confidence = result[2] if len(result) > 2 else 0.8  # Default confidence if not provided
                elif isinstance(result, tuple):
                    if len(result) == 3:
                        # Format: (bbox, text, confidence)
                        bbox, text, confidence = result
                    elif len(result) == 2:
                        # Format: (bbox, text) - no confidence
                        bbox, text = result
                        confidence = 0.8  # Default confidence
                    else:

                        continue
                else:

                    continue
                
                # Skip empty text or very low confidence
                if not text or confidence < 0.3:
                    continue
                
                # Extract bounding box coordinates
                # EasyOCR returns bbox as [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                bbox = np.array(bbox)
                
                # Convert to the same format as the original OCR
                word_bounds = [
                    (int(bbox[0][0]), int(bbox[0][1])),  # top-left
                    (int(bbox[1][0]), int(bbox[1][1])),  # top-right
                    (int(bbox[2][0]), int(bbox[2][1])),  # bottom-right
                    (int(bbox[3][0]), int(bbox[3][1]))   # bottom-left
                ]
                
                # Group words into blocks based on proximity
                if current_block is None:
                    current_block = text
                    current_block_bounds = [word_bounds]
                else:
                    # Check if this word is close to the current block
                    last_bounds = current_block_bounds[-1]
                    last_x, last_y = last_bounds[2]  # bottom-right of last word
                    
                    # If words are close horizontally and vertically, group them
                    current_x, current_y = word_bounds[0]  # top-left of current word
                    
                    if (abs(current_x - last_x) < 100 and abs(current_y - last_y) < 50):
                        current_block += " " + text
                        current_block_bounds.append(word_bounds)
                    else:
                        # Start a new block
                        if current_block.strip():
                            blocks.append({
                                'text': current_block.strip(),
                                'bounds': current_block_bounds,
                                'block_bounds': self._get_block_bounds(current_block_bounds)
                            })
                        
                        current_block = text
                        current_block_bounds = [word_bounds]
            
            # Add the last block
            if current_block and current_block.strip():
                blocks.append({
                    'text': current_block.strip(),
                    'bounds': current_block_bounds,
                    'block_bounds': self._get_block_bounds(current_block_bounds)
                })
            
            # Combine all text
            all_text = " ".join([block['text'] for block in blocks])
            
            # Calculate overall confidence (average of all word confidences)
            confidences = []
            for result in results:
                if isinstance(result, list) and len(result) >= 3:
                    confidences.append(result[2])
                elif isinstance(result, list) and len(result) == 2:
                    confidences.append(0.8)  # Default confidence
                elif isinstance(result, tuple) and len(result) >= 3:
                    confidences.append(result[2])
                elif isinstance(result, tuple) and len(result) == 2:
                    confidences.append(0.8)  # Default confidence
            
            confidences = [c for c in confidences if c > 0.3]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.8
            


            
            return {
                'success': True,
                'text': all_text,
                'blocks': blocks,
                'confidence': avg_confidence
            }
            
        except Exception as e:
            return {"error": f"Parse error: {e}"}
    
    def _get_block_bounds(self, word_bounds: List[List[Tuple[int, int]]]) -> List[Tuple[int, int]]:
        """Calculate the bounding box that encompasses all words in a block"""
        if not word_bounds:
            return []
        
        all_x = []
        all_y = []
        
        for bounds in word_bounds:
            for x, y in bounds:
                all_x.append(x)
                all_y.append(y)
        
        if not all_x or not all_y:
            return []
        
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        
        return [
            (min_x, min_y),      # top-left
            (max_x, min_y),      # top-right
            (max_x, max_y),      # bottom-right
            (min_x, max_y)       # bottom-left
        ]

class BookSpineDatasetCreator:
    """Creates training datasets from EasyOCR results"""
    
    def __init__(self, easyocr_engine: EasyOCREngine, output_dir: str = "training_dataset"):
        self.easyocr_engine = easyocr_engine
        self.output_dir = output_dir
        self.dataset_info = {
            'total_images': 0,
            'successful_ocr': 0,
            'failed_ocr': 0,
            'total_text_blocks': 0
        }
        
        # Create output directories
        os.makedirs(f"{output_dir}/images", exist_ok=True)
        os.makedirs(f"{output_dir}/labels", exist_ok=True)
        os.makedirs(f"{output_dir}/metadata", exist_ok=True)
    
    def process_spine_image(self, image: np.ndarray, spine_region: np.ndarray, 
                          spine_id: str, obb_data: Dict) -> bool:
        """Process a single spine image and create training data"""
        try:

            
            # Run EasyOCR on the spine region
            ocr_result = self.easyocr_engine.detect_text_advanced(spine_region)
            
            if 'error' in ocr_result:
                self.dataset_info['failed_ocr'] += 1
                return False
            
            # Save the spine region image
            image_path = f"{self.output_dir}/images/{spine_id}.jpg"
            cv2.imwrite(image_path, spine_region)
            
            # Create PaddleOCR training format labels
            labels = self._create_paddleocr_labels(ocr_result, spine_region.shape)
            
            # Save labels
            label_path = f"{self.output_dir}/labels/{spine_id}.txt"
            with open(label_path, 'w', encoding='utf-8') as f:
                for label in labels:
                    f.write(f"{label}\n")
            
            # Save metadata
            metadata = {
                'spine_id': spine_id,
                'image_path': image_path,
                'label_path': label_path,
                'ocr_result': ocr_result,
                'obb_data': obb_data,
                'image_shape': spine_region.shape
            }
            
            metadata_path = f"{self.output_dir}/metadata/{spine_id}.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.dataset_info['successful_ocr'] += 1
            self.dataset_info['total_text_blocks'] += len(ocr_result.get('blocks', []))
            

            return True
            
        except Exception as e:

            self.dataset_info['failed_ocr'] += 1
            return False
    
    def _create_paddleocr_labels(self, ocr_result: Dict, image_shape: Tuple) -> List[str]:
        """Convert EasyOCR results to PaddleOCR training format"""
        labels = []
        
        for block in ocr_result.get('blocks', []):
            for word_info in block['bounds']:
                text = word_info['text']
                bounds = word_info['bounds']
                
                if len(bounds) >= 4 and text.strip():
                    # Convert to PaddleOCR format: text x1,y1 x2,y2 x3,y3 x4,y4
                    # Normalize coordinates to 0-1 range
                    h, w = image_shape[:2]
                    
                    normalized_bounds = []
                    for x, y in bounds:
                        norm_x = max(0, min(1, x / w))
                        norm_y = max(0, min(1, y / h))
                        normalized_bounds.extend([norm_x, norm_y])
                    
                    # Ensure we have exactly 8 coordinates (4 points)
                    while len(normalized_bounds) < 8:
                        normalized_bounds.extend([0, 0])
                    
                    label_line = f"{text} {' '.join([f'{coord:.6f}' for coord in normalized_bounds[:8]])}"
                    labels.append(label_line)
        
        return labels
    
    def create_dataset_summary(self) -> Dict:
        """Create a summary of the generated dataset"""
        summary = {
            'dataset_info': self.dataset_info,
            'output_directory': self.output_dir,
            'paddleocr_format': 'detection + recognition',
            'training_instructions': [
                '1. Use PaddleOCR training pipeline',
                '2. Configure for text detection + recognition',
                '3. Use generated images and labels',
                '4. Fine-tune on your book spine domain'
            ]
        }
        
        # Save summary
        summary_path = f"{self.output_dir}/dataset_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return summary


