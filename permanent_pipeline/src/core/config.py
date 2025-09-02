"""
Configuration management for Spinecat
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class SpinecatConfig:
    """Configuration for Spinecat pipeline"""
    
    # OCR Configuration
    easyocr_enabled: bool = True
    
    # Model paths
    yolo_model_path: str = "models/yolo-spine-obb-final2/weights/best.pt"
    
    # OCR settings
    padding_pixels: int = 25
    angle_tolerance: float = 5.0
    min_text_length: int = 3
    confidence_threshold: float = 0.5
    
    # Advanced Matching Configuration
    advanced_matching_confidence_threshold: float = 0.65
    advanced_matching_top_k: int = 10
    
    # Open Library settings
    open_library_rate_limit: float = 0.1  # seconds between requests
    max_library_results: int = 20
    
    # Output settings
    default_output_dir: str = "results"
    save_intermediate_results: bool = True
    
    @classmethod
    def from_env(cls) -> 'SpinecatConfig':
        """Create configuration from environment variables"""
        # Load .env file if it exists
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)
        
        return cls(
            easyocr_enabled=os.getenv("EASYOCR_ENABLED", "true").lower() == "true",
            yolo_model_path=os.getenv("YOLO_MODEL_PATH", "models/yolo-spine-obb-final2/weights/best.pt"),
            padding_pixels=int(os.getenv("PADDING_PIXELS", "25")),
            angle_tolerance=float(os.getenv("ANGLE_TOLERANCE", "5.0")),
            min_text_length=int(os.getenv("MIN_TEXT_LENGTH", "3")),
            confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.5")),
            use_semantic_matching=os.getenv("USE_SEMANTIC_MATCHING", "true").lower() == "true",
            match_confidence_threshold=float(os.getenv("MATCH_CONFIDENCE_THRESHOLD", "0.3")),
            open_library_rate_limit=float(os.getenv("OPEN_LIBRARY_RATE_LIMIT", "0.1")),
            max_library_results=int(os.getenv("MAX_LIBRARY_RESULTS", "20")),
            default_output_dir=os.getenv("DEFAULT_OUTPUT_DIR", "results"),
            save_intermediate_results=os.getenv("SAVE_INTERMEDIATE_RESULTS", "true").lower() == "true"
        )
    
    @classmethod
    def from_file(cls, config_path: str) -> 'SpinecatConfig':
        """Create configuration from config file"""
        import json
        
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        return cls(**config_data)
    
    def save_to_file(self, config_path: str):
        """Save configuration to file"""
        import json
        
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(self.__dict__, f, indent=2)
    
    def validate(self) -> bool:
        """Validate configuration"""
        errors = []
        
        # Check OCR configuration
        if not self.easyocr_enabled:
            errors.append("EasyOCR is disabled")
        
        # Check model path
        if not Path(self.yolo_model_path).exists():
            errors.append(f"YOLO model not found: {self.yolo_model_path}")
        
        # Check numeric ranges
        if self.padding_pixels < 0:
            errors.append("Padding pixels must be non-negative")
        
        if self.angle_tolerance < 0 or self.angle_tolerance > 90:
            errors.append("Angle tolerance must be between 0 and 90 degrees")
        
        if self.confidence_threshold < 0 or self.confidence_threshold > 1:
            errors.append("Confidence threshold must be between 0 and 1")
        
        if self.match_confidence_threshold < 0 or self.match_confidence_threshold > 1:
            errors.append("Match confidence threshold must be between 0 and 1")
        
        if self.open_library_rate_limit < 0:
            errors.append("Open Library rate limit must be non-negative")
        
        if self.max_library_results < 1:
            errors.append("Max library results must be at least 1")
        
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors))
        
        return True

def load_config(config_path: Optional[str] = None) -> SpinecatConfig:
    """Load configuration from file or environment"""
    if config_path:
        return SpinecatConfig.from_file(config_path)
    else:
        return SpinecatConfig.from_env()

def create_default_config(config_path: str = "spinecat_config.json"):
    """Create a default configuration file"""
    config = SpinecatConfig.from_env()
    config.save_to_file(config_path)
    return config

def create_env_template(env_path: str = ".env.example"):
    """Create a .env template file"""
    env_template = """# Spinecat Configuration
# Copy this file to .env and fill in your actual values

        # Required: EasyOCR Configuration
        EASYOCR_ENABLED=true

# Optional: Model and processing settings
YOLO_MODEL_PATH=models/yolo-spine-obb-final2/weights/best.pt
PADDING_PIXELS=25
ANGLE_TOLERANCE=5.0
MIN_TEXT_LENGTH=3
CONFIDENCE_THRESHOLD=0.5

# Optional: Matching settings
USE_SEMANTIC_MATCHING=true
MATCH_CONFIDENCE_THRESHOLD=0.3

# Optional: Open Library settings
OPEN_LIBRARY_RATE_LIMIT=0.1
MAX_LIBRARY_RESULTS=20

# Optional: Output settings
DEFAULT_OUTPUT_DIR=results
SAVE_INTERMEDIATE_RESULTS=true
"""
    
    with open(env_path, 'w') as f:
        f.write(env_template)
    
    return env_path

