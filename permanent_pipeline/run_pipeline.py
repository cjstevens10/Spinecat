#!/usr/bin/env python3
"""
Simple pipeline runner for the permanent Spinecat pipeline
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.pipeline import create_pipeline
from config import GOOGLE_VISION_API_KEY

def main():
    """Run the pipeline on a test image"""
    
    # Check if API key is available
    if not GOOGLE_VISION_API_KEY:
        print("❌ Google Vision API key not found in config.py")
        print("Please add your API key to config.py")
        return
    
    # Path to YOLO model (you'll need to add your trained model here)
    yolo_model_path = "models/your_trained_model.pt"  # Update this path
    
    if not os.path.exists(yolo_model_path):
        print(f"❌ YOLO model not found at: {yolo_model_path}")
        print("Please add your trained YOLO model to the models/ directory")
        return
    
    # Test image path
    test_image = "test_image.jpg"  # Update this path
    
    if not os.path.exists(test_image):
        print(f"❌ Test image not found at: {test_image}")
        print("Please add a test image to run the pipeline")
        return
    
    try:
        # Create pipeline
        print("🚀 Initializing Spinecat Pipeline...")
        pipeline = create_pipeline(
            yolo_model_path=yolo_model_path,
            google_vision_api_key=GOOGLE_VISION_API_KEY,
            use_semantic_matching=True
        )
        
        # Process image
        print(f"📚 Processing image: {test_image}")
        results = pipeline.process_image(test_image, conf_threshold=0.3)
        
        # Display results
        print(f"\n✅ Pipeline completed successfully!")
        print(f"📊 Processed {len(results)} spines")
        
        for i, result in enumerate(results):
            if result.success:
                print(f"\n📖 Spine {i+1}: {result.spine_id}")
                if result.best_match:
                    print(f"   Best match: {result.best_match.library_book.title}")
                    print(f"   Score: {result.best_match.match_score:.3f}")
            else:
                print(f"\n❌ Spine {i+1}: {result.spine_id} - Failed")
                for error in result.errors:
                    print(f"   Error: {error}")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()





