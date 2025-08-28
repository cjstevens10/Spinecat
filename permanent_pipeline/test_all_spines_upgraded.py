#!/usr/bin/env python3
"""
Comprehensive test of all spines with the upgraded pipeline
Tests the end-to-end performance improvements
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_all_spines_upgraded():
    """Test all spines with the upgraded pipeline"""
    print("🧪 COMPREHENSIVE TEST: ALL SPINES WITH UPGRADED PIPELINE")
    print("=" * 70)
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        from core.pipeline import SpinecatPipeline
        from core.models import PipelineResult
        
        # Load configuration
        from core.config import SpinecatConfig
        config = SpinecatConfig.from_env()
        
        # Create pipeline
        pipeline = SpinecatPipeline(
            yolo_model_path=config.yolo_model_path,
            google_vision_api_key=config.google_vision_api_key,
            use_semantic_matching=config.use_semantic_matching
        )
        
        # Test image with all spines
        test_image = "real_books1.jpg"
        
        if not Path(test_image).exists():
            print(f"❌ Test image '{test_image}' not found!")
            return False
        
        print(f"📚 Processing image: {test_image}")
        print("=" * 50)
        
        # Process the image
        results = pipeline.process_image(test_image, conf_threshold=0.3)
        
        if not results:
            print("❌ No results returned!")
            return False
        
        print(f"✅ Detected {len(results)} spines")
        print()
        
        # Process each spine through the full pipeline
        successful_matches = 0
        perfect_matches = 0
        total_spines = len(results)
        
        spine_results = []
        
        for i, result in enumerate(results, 1):
            print(f"📖 Processing Spine {i}/{total_spines}")
            print("-" * 40)
            
            # Extract spine info
            spine_id = result.spine_id
            confidence = result.spine_data.confidence_score if result.spine_data else 0.0
            bbox = result.spine_data.obb_data.get('xyxyxyxy', []) if result.spine_data else []
            
            print(f"🆔 Spine ID: {spine_id}")
            print(f"📊 Detection Confidence: {confidence:.3f}")
            print(f"📍 Bounding Box: {bbox}")
            
            # Get OCR results for this spine
            if result.spine_data and result.spine_data.consolidated_text:
                ocr_text = result.spine_data.consolidated_text
                print(f"🔤 OCR Text: '{ocr_text}'")
                print(f"📊 OCR Confidence: {confidence:.3f}")
                
                # Get denoised text
                if result.denoised_text:
                    print(f"🧹 Denoised: '{result.denoised_text.denoised_text}'")
                    print(f"📊 Denoising Confidence: {result.denoised_text.confidence:.3f}")
                
                # Get library matches
                if result.matches:
                    print(f"📚 Library Matches: {len(result.matches)} found")
                    
                    # Show top 3 matches
                    for j, match in enumerate(result.matches[:3], 1):
                        book = match.library_book
                        score = match.match_score
                        match_type = match.match_type
                        
                        title = book.title or "Unknown Title"
                        author = book.author_name or ["Unknown Author"]
                        author_str = ', '.join(author) if isinstance(author, list) else str(author)
                        year = book.first_publish_year or "Unknown Year"
                        
                        print(f"   {j}. '{title}' by {author_str} ({year})")
                        print(f"      Score: {score:.3f} | Type: {match_type}")
                        
                        # Check if this is a good match
                        if score >= 0.85:
                            print(f"      🎯 EXCELLENT MATCH!")
                            if score >= 0.95:
                                perfect_matches += 1
                            successful_matches += 1
                        elif score >= 0.70:
                            print(f"      ✅ GOOD MATCH")
                            successful_matches += 1
                        elif score >= 0.55:
                            print(f"      ⚠️  MODERATE MATCH")
                        else:
                            print(f"      ❌ POOR MATCH")
                    
                    # Store results for analysis
                    spine_results.append({
                        'spine_id': spine_id,
                        'ocr_text': ocr_text,
                        'denoised_text': result.denoised_text.denoised_text if result.denoised_text else "",
                        'top_match': result.matches[0] if result.matches else None,
                        'total_matches': len(result.matches)
                    })
                else:
                    print("❌ No library matches found")
                    spine_results.append({
                        'spine_id': spine_id,
                        'ocr_text': ocr_text,
                        'denoised_text': result.denoised_text.denoised_text if result.denoised_text else "",
                        'top_match': None,
                        'total_matches': 0
                    })
            else:
                print("❌ No OCR results for this spine")
                spine_results.append({
                    'spine_id': spine_id,
                    'ocr_text': "",
                    'denoised_text': "",
                    'top_match': None,
                    'total_matches': 0
                })
            
            print()
        
        # Summary statistics
        print("📊 PIPELINE PERFORMANCE SUMMARY")
        print("=" * 50)
        print(f"📚 Total Spines Processed: {total_spines}")
        print(f"✅ Successful Matches (≥0.70): {successful_matches}")
        print(f"🎯 Perfect Matches (≥0.95): {perfect_matches}")
        print(f"📈 Success Rate: {(successful_matches/total_spines)*100:.1f}%")
        print(f"🏆 Perfect Match Rate: {(perfect_matches/total_spines)*100:.1f}%")
        
        # Save detailed results
        output_file = f"pipeline_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Prepare results for JSON serialization
        serializable_results = []
        for spine_result in spine_results:
            serializable_result = {
                'spine_id': spine_result['spine_id'],
                'ocr_text': spine_result['ocr_text'],
                'denoised_text': spine_result['denoised_text'],
                'total_matches': spine_result['total_matches']
            }
            
            if spine_result['top_match']:
                match = spine_result['top_match']
                serializable_result['top_match'] = {
                    'title': match.library_book.title,
                    'author_name': match.library_book.author_name,
                    'first_publish_year': match.library_book.first_publish_year,
                    'score': match.match_score,
                    'match_type': match.match_type
                }
            
            serializable_results.append(serializable_result)
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump({
                'test_timestamp': datetime.now().isoformat(),
                'total_spines': total_spines,
                'successful_matches': successful_matches,
                'perfect_matches': perfect_matches,
                'success_rate': (successful_matches/total_spines)*100,
                'perfect_match_rate': (perfect_matches/total_spines)*100,
                'spine_results': serializable_results
            }, f, indent=2)
        
        print(f"💾 Detailed results saved to: {output_file}")
        print()
        print("✅ Comprehensive pipeline test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_all_spines_upgraded()
    sys.exit(0 if success else 1)
