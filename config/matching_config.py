"""
Configuration for book matching systems
Easily switch between legacy and advanced matching
"""

import os
from typing import Dict, Any

class MatchingConfig:
    """Configuration for book matching systems"""
    
    # Main matching system selection
    USE_ADVANCED_MATCHING = os.getenv("USE_ADVANCED_MATCHING", "true").lower() == "true"
    USE_LEGACY_MATCHING = os.getenv("USE_LEGACY_MATCHING", "false").lower() == "true"
    
    # Advanced matching settings
    ADVANCED_MATCHING_CONFIDENCE_THRESHOLD = float(os.getenv("ADVANCED_MATCHING_CONFIDENCE_THRESHOLD", "0.65"))
    ADVANCED_MATCHING_TOP_K = int(os.getenv("ADVANCED_MATCHING_TOP_K", "10"))
    ADVANCED_MATCHING_USE_CHARACTER_NGRAMS = os.getenv("ADVANCED_MATCHING_USE_CHARACTER_NGRAMS", "true").lower() == "true"
    
    # Legacy matching settings (kept for compatibility)
    LEGACY_MATCHING_CONFIDENCE_THRESHOLD = float(os.getenv("LEGACY_MATCHING_CONFIDENCE_THRESHOLD", "0.5"))
    LEGACY_MATCHING_MATCH_CONFIDENCE_THRESHOLD = float(os.getenv("LEGACY_MATCHING_MATCH_CONFIDENCE_THRESHOLD", "0.3"))
    LEGACY_MATCHING_USE_SEMANTIC_MATCHING = os.getenv("LEGACY_MATCHING_USE_SEMANTIC_MATCHING", "true").lower() == "true"
    
    @classmethod
    def get_pipeline_config(cls) -> Dict[str, Any]:
        """Get configuration for pipeline initialization"""
        return {
            "use_semantic_matching": cls.LEGACY_MATCHING_USE_SEMANTIC_MATCHING,
            "use_advanced_matching": cls.USE_ADVANCED_MATCHING
        }
    
    @classmethod
    def get_advanced_matcher_config(cls) -> Dict[str, Any]:
        """Get configuration for advanced matcher"""
        return {
            "use_character_ngrams": cls.ADVANCED_MATCHING_USE_CHARACTER_NGRAMS,
            "confidence_threshold": cls.ADVANCED_MATCHING_CONFIDENCE_THRESHOLD,
            "top_k": cls.ADVANCED_MATCHING_TOP_K
        }
    
    @classmethod
    def print_config(cls):
        """Print current configuration"""
        print("🔧 Book Matching Configuration")
        print("=" * 40)
        print(f"Advanced Matching: {'✅ Enabled' if cls.USE_ADVANCED_MATCHING else '❌ Disabled'}")
        print(f"Legacy Matching: {'✅ Enabled' if cls.USE_LEGACY_MATCHING else '❌ Disabled'}")
        print()
        
        if cls.USE_ADVANCED_MATCHING:
            print("📊 Advanced Matching Settings:")
            print(f"  - Confidence Threshold: {cls.ADVANCED_MATCHING_CONFIDENCE_THRESHOLD}")
            print(f"  - Top K Results: {cls.ADVANCED_MATCHING_TOP_K}")
            print(f"  - Character N-grams: {'✅ Enabled' if cls.ADVANCED_MATCHING_USE_CHARACTER_NGRAMS else '❌ Disabled'}")
            print()
        
        if cls.USE_LEGACY_MATCHING:
            print("🔍 Legacy Matching Settings:")
            print(f"  - Confidence Threshold: {cls.LEGACY_MATCHING_CONFIDENCE_THRESHOLD}")
            print(f"  - Match Confidence Threshold: {cls.LEGACY_MATCHING_MATCH_CONFIDENCE_THRESHOLD}")
            print(f"  - Semantic Matching: {'✅ Enabled' if cls.LEGACY_MATCHING_USE_SEMANTIC_MATCHING else '❌ Disabled'}")
            print()
        
        print("💡 Environment Variables:")
        print("  - USE_ADVANCED_MATCHING: true/false")
        print("  - USE_LEGACY_MATCHING: true/false")
        print("  - ADVANCED_MATCHING_CONFIDENCE_THRESHOLD: 0.0-1.0")
        print("  - ADVANCED_MATCHING_TOP_K: integer")

if __name__ == "__main__":
    MatchingConfig.print_config()


