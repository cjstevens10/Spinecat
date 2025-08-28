#!/usr/bin/env python3
"""
Startup script for the Spinecat FastAPI backend
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add the permanent_pipeline to the path so we can import the pipeline
sys.path.append(str(Path(__file__).parent.parent.parent / "permanent_pipeline"))

from main import app
from config import config

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=False,  # Disable auto-reload to prevent restart loops
        log_level=config.LOG_LEVEL.lower()
    )
