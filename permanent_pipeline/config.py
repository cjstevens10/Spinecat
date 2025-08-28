#!/usr/bin/env python3
"""
Configuration file for Spinecat OCR Pipeline
"""

import os

# Google Vision API Configuration
GOOGLE_VISION_API_KEY = os.environ.get("GOOGLE_VISION_API_KEY", "AIzaSyCwwk0DZ0sTwGKcCJrpt_fNiT0gNfGTcDo")

# OCR Pipeline Settings
DEFAULT_CONFIDENCE_THRESHOLD = 0.5
DEFAULT_PADDING_PIXELS = 25
DEFAULT_ANGLE_TOLERANCE = 5.0

# Output Directories
OCR_RESULTS_DIR = "ocr_results"
DEBUG_IMAGES_DIR = "debug_images"

# YOLO Model Settings
YOLO_MODEL_PATH = "models/yolo-spine-obb-final2/weights/best.pt"
YOLO_CONFIDENCE_THRESHOLD = 0.5

# Image Processing Settings
MAX_IMAGE_DIMENSION = 4096
SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']

# Logging Settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

