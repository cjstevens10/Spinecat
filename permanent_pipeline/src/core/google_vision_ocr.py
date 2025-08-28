#!/usr/bin/env python3
"""
Google Cloud Vision OCR Integration for Book Spine Training Data
Uses Google's OCR as a "teacher" to create high-quality training datasets
"""

import os
import json
import cv2
import numpy as np
from google.cloud import vision
from google.oauth2 import service_account
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import List, Dict, Tuple, Optional
import base64
from pathlib import Path

console = Console()

class GoogleVisionOCR:
    """Google Cloud Vision OCR client for high-quality text detection"""
    
    def __init__(self, api_key: str = None, credentials_path: str = None):
        """Initialize Google Cloud Vision client"""
        try:
            if credentials_path and os.path.exists(credentials_path):
                # Use service account credentials
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                self.client = vision.ImageAnnotatorClient(credentials=credentials)
                console.print("✅ Using service account credentials")
            elif api_key:
                # Use API key (for simple REST API calls)
                self.api_key = api_key
                self.client = None
                console.print("✅ Using API key authentication")
            else:
                # Try to use default credentials
                self.client = vision.ImageAnnotatorClient()
                console.print("✅ Using default credentials")
                
        except Exception as e:
            console.print(f"❌ Failed to initialize Google Cloud Vision: {e}")
            console.print("💡 Make sure you have GOOGLE_APPLICATION_CREDENTIALS set or provide valid credentials")
            raise
    
    def detect_text_advanced(self, image: np.ndarray) -> Dict:
        """Detect text using Google Cloud Vision with full document analysis"""
        try:
            # Convert image to bytes
            success, buffer = cv2.imencode('.jpg', image)
            if not success:
                raise ValueError("Failed to encode image")
            
            image_bytes = buffer.tobytes()
            
            if self.client:
                # Use the Vision client
                image_vision = vision.Image(content=image_bytes)
                
                # Request full document text detection
                response = self.client.document_text_detection(image=image_vision)
                
                if response.error.message:
                    raise Exception(f"Google Vision API error: {response.error.message}")
                
                return self._parse_document_response(response)
            else:
                # Use REST API with API key
                return self._call_rest_api(image_bytes)
                
        except Exception as e:
            console.print(f"⚠️  Google Vision OCR error: {e}")
            return {"error": str(e)}
    
    def _parse_document_response(self, response) -> Dict:
        """Parse Google Vision document text detection response"""
        try:
            document = response.full_text_annotation
            
            # Extract text blocks with bounding boxes
            blocks = []
            for page in document.pages:
                for block in page.blocks:
                    block_text = ""
                    block_bounds = []
                    
                    for paragraph in block.paragraphs:
                        for word in paragraph.words:
                            word_text = ''.join([symbol.text for symbol in word.symbols])
                            word_bounds = self._extract_bounds(word.bounding_box)
                            
                            block_text += word_text + " "
                            block_bounds.append({
                                'text': word_text,
                                'bounds': word_bounds,
                                'confidence': 0.95  # Google Vision is very reliable
                            })
                    
                    if block_text.strip():
                        blocks.append({
                            'text': block_text.strip(),
                            'bounds': block_bounds,
                            'block_bounds': self._extract_bounds(block.bounding_box)
                        })
            
            return {
                'success': True,
                'text': document.text,
                'blocks': blocks,
                'confidence': 0.95
            }
            
        except Exception as e:
            console.print(f"⚠️  Error parsing Google Vision response: {e}")
            return {"error": f"Parse error: {e}"}
    
    def _extract_bounds(self, bounding_box) -> List[Tuple[int, int]]:
        """Extract bounding box coordinates from Google Vision response"""
        vertices = []
        for vertex in bounding_box.vertices:
            vertices.append((vertex.x, vertex.y))
        return vertices
    
    def _call_rest_api(self, image_bytes: bytes) -> Dict:
        """Use REST API with API key for Google Cloud Vision"""
        import requests
        import base64
        
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Google Cloud Vision REST API endpoint
            url = f"https://vision.googleapis.com/v1/images:annotate?key={self.api_key}"
            
            # Request payload for document text detection
            payload = {
                "requests": [
                    {
                        "image": {
                            "content": image_base64
                        },
                        "features": [
                            {
                                "type": "DOCUMENT_TEXT_DETECTION",
                                "maxResults": 50
                            }
                        ]
                    }
                ]
            }
            
            # Make API request
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            if 'responses' in result and result['responses']:
                return self._parse_rest_response(result['responses'][0])
            else:
                return {"error": "No response from Google Vision API"}
                
        except Exception as e:
            return {"error": f"REST API error: {e}"}
    
    def _parse_rest_response(self, response: Dict) -> Dict:
        """Parse Google Vision REST API response"""
        try:
            if 'error' in response:
                return {"error": f"Google Vision API error: {response['error']}"}
            
            if 'fullTextAnnotation' not in response:
                return {"error": "No text annotation in response"}
            
            full_text = response['fullTextAnnotation']
            
            # Extract text blocks with bounding boxes
            blocks = []
            if 'pages' in full_text:
                for page in full_text['pages']:
                    for block in page.get('blocks', []):
                        block_text = ""
                        block_bounds = []
                        
                        for paragraph in block.get('paragraphs', []):
                            for word in paragraph.get('words', []):
                                word_text = ''.join([symbol.get('text', '') for symbol in word.get('symbols', [])])
                                
                                # Extract bounding box
                                if 'boundingBox' in word and 'vertices' in word['boundingBox']:
                                    vertices = word['boundingBox']['vertices']
                                    word_bounds = [(v.get('x', 0), v.get('y', 0)) for v in vertices]
                                    
                                    if word_text.strip():
                                        block_text += word_text + " "
                                        block_bounds.append({
                                            'text': word_text,
                                            'bounds': word_bounds,
                                            'confidence': 0.95
                                        })
                        
                        if block_text.strip():
                            blocks.append({
                                'text': block_text.strip(),
                                'bounds': block_bounds,
                                'block_bounds': []  # Could extract block-level bounds if needed
                            })
            
            return {
                'success': True,
                'text': full_text.get('text', ''),
                'blocks': blocks,
                'confidence': 0.95
            }
            
        except Exception as e:
            return {"error": f"Parse error: {e}"}

class BookSpineDatasetCreator:
    """Creates training datasets from Google Vision OCR results"""
    
    def __init__(self, google_ocr: GoogleVisionOCR, output_dir: str = "training_dataset"):
        self.google_ocr = google_ocr
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
            console.print(f"🔍 Processing spine {spine_id} with Google Vision...")
            
            # Run Google Vision OCR on the spine region
            ocr_result = self.google_ocr.detect_text_advanced(spine_region)
            
            if 'error' in ocr_result:
                console.print(f"   ❌ OCR failed: {ocr_result['error']}")
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
            
            console.print(f"   ✅ Processed successfully: {len(ocr_result.get('blocks', []))} text blocks")
            return True
            
        except Exception as e:
            console.print(f"   ❌ Processing error: {e}")
            self.dataset_info['failed_ocr'] += 1
            return False
    
    def _create_paddleocr_labels(self, ocr_result: Dict, image_shape: Tuple) -> List[str]:
        """Convert Google Vision results to PaddleOCR training format"""
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

def main():
    """Test Google Vision OCR integration"""
    console.print("🚀 Google Cloud Vision OCR Integration for Book Spines")
    console.print("=" * 60)
    
    # Initialize Google Vision OCR
    api_key = "AIzaSyCwwk0DZ0sTwGKcCJrpt_fNiT0gNfGTcDo"
    
    try:
        google_ocr = GoogleVisionOCR(api_key=api_key)
        console.print("✅ Google Vision OCR initialized successfully")
        
        # Initialize dataset creator
        dataset_creator = BookSpineDatasetCreator(google_ocr)
        console.print("✅ Dataset creator initialized")
        
        # Test with a sample image
        test_image = "IMG_3105.jpg"
        if os.path.exists(test_image):
            console.print(f"🖼️  Testing with: {test_image}")
            
            # Load image
            image = cv2.imread(test_image)
            if image is not None:
                # Create a mock spine region for testing
                spine_region = image[400:800, 1800:2000]  # Sample region
                
                # Process with Google Vision
                success = dataset_creator.process_spine_image(
                    image, spine_region, "test_spine_001", 
                    {'xywhr': [1900, 600, 200, 400, 0.0]}
                )
                
                if success:
                    console.print("✅ Test completed successfully!")
                    console.print(f"📁 Check {dataset_creator.output_dir} for results")
                else:
                    console.print("❌ Test failed")
            else:
                console.print(f"❌ Failed to load test image")
        else:
            console.print(f"❌ Test image not found: {test_image}")
            
    except Exception as e:
        console.print(f"❌ Initialization failed: {e}")
        console.print("💡 Make sure you have proper Google Cloud credentials")

if __name__ == "__main__":
    main()
