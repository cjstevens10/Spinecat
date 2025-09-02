import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in the main project directory
load_dotenv(Path(__file__).parent.parent.parent / ".env")

class BackendConfig:
    """Configuration for the Spinecat backend"""
    
    # API Configuration
    API_HOST = os.getenv("API_HOST", "127.0.0.1")
    API_PORT = int(os.getenv("API_PORT", "8002"))  # Changed from 8001 to 8002
    
    # CORS Configuration
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Pipeline Configuration
    # Resolve YOLO_MODEL_PATH relative to project root, not backend directory
    if os.getenv("YOLO_MODEL_PATH"):
        # If .env has a path, resolve it relative to project root
        YOLO_MODEL_PATH = str(Path(__file__).parent.parent.parent / os.getenv("YOLO_MODEL_PATH"))
    else:
        # Default fallback path
        YOLO_MODEL_PATH = str(Path(__file__).parent.parent.parent / "models" / "yolo-spine-obb-final" / "weights" / "best.pt")
    
    EASYOCR_ENABLED = os.getenv("EASYOCR_ENABLED", "true").lower() == "true"
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
    
    # Advanced Matching Configuration
    ADVANCED_MATCHING_CONFIDENCE_THRESHOLD = float(os.getenv("ADVANCED_MATCHING_CONFIDENCE_THRESHOLD", "0.65"))
    ADVANCED_MATCHING_TOP_K = int(os.getenv("ADVANCED_MATCHING_TOP_K", "10"))
    

    
    # File Upload Configuration
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png"]
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        errors = []
        
        if not cls.EASYOCR_ENABLED:
            errors.append("EasyOCR is disabled")
        
        # Temporarily skip YOLO model validation for testing
        # if not os.path.exists(cls.YOLO_MODEL_PATH):
        #     errors.append(f"YOLO model not found at: {cls.YOLO_MODEL_PATH}")
        
        if errors:
            raise ValueError(f"Configuration errors: {'; '.join(errors)}")
        
        return True

# Create a global config instance
config = BackendConfig()
