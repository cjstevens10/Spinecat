from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import sys
import logging
import traceback
from pathlib import Path
import uuid
from threading import Thread
from typing import Dict, Any
import numpy as np
import uvicorn
import requests

# Add the permanent_pipeline to the path so we can import the pipeline
sys.path.append(str(Path(__file__).parent.parent.parent / "permanent_pipeline"))

from src.core.pipeline import SpinecatPipeline
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global pipeline instance
pipeline: SpinecatPipeline = None

# Task registry for background processing
tasks: Dict[str, Dict[str, Any]] = {}

# Static uploads directory
BASE_DIR = Path(__file__).parent
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app"""
    global pipeline
    
    try:
        # Validate configuration
        config.validate()
        
        # Get the path to the YOLO model
        yolo_model_path = config.YOLO_MODEL_PATH
        easyocr_enabled = config.EASYOCR_ENABLED
        
        if not easyocr_enabled:
            logger.error("EasyOCR is disabled")
            return
        
        logger.info(f"Using YOLO model path: {yolo_model_path}")
        
        # Initialize the pipeline with advanced matching enabled
        # Note: The pipeline expects google_vision_api_key but we're using EasyOCR
        # We'll pass a dummy key since the OCR processor uses EasyOCR internally
        pipeline = SpinecatPipeline(
            yolo_model_path=yolo_model_path,
            google_vision_api_key="dummy_key_for_easyocr"  # Dummy key since we use EasyOCR
        )
        
        logger.info("Spinecat pipeline initialized successfully")
        
        # Log advanced matching configuration
        logger.info("Advanced matching system (character n-gram) is ENABLED")
        logger.info(f"   - Confidence threshold: {config.ADVANCED_MATCHING_CONFIDENCE_THRESHOLD}")
        logger.info(f"   - Top K results: {config.ADVANCED_MATCHING_TOP_K}")
        
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}")
    
    yield
    
    # Cleanup (if needed)
    logger.info("Shutting down Spinecat API")

def update_task_progress(task_id: str, progress: int, message: str) -> None:
    """Update progress for a specific task"""
    if task_id in tasks:
        tasks[task_id]["progress"] = progress
        tasks[task_id]["message"] = message
        tasks[task_id]["status"] = "processing"
        print(f"📡 [{task_id}] {progress}% - {message}")

def _to_float(value: Any) -> Any:
    """Convert value to float, return original if conversion fails"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return value

def _run_pipeline_background(task_id: str, image_file_path: str):
    """Run the pipeline in a background thread"""
    try:
        update_task_progress(task_id, 10, "Initializing pipeline...")
        
        if not pipeline:
            raise Exception("Pipeline not initialized")
        
        update_task_progress(task_id, 20, "Starting spine detection...")

        def progress_callback(progress: int, message: str):
            update_task_progress(task_id, progress, message)

        results = pipeline.process_image(image_file_path, conf_threshold=config.CONFIDENCE_THRESHOLD, progress_callback=progress_callback)
        
        # Debug logging
        logger.info(f"Pipeline results type: {type(results)}")
        logger.info(f"Pipeline results length: {len(results) if results else 'None'}")
        if results and len(results) > 0:
            logger.info(f"First result type: {type(results[0])}")
            logger.info(f"First result attributes: {dir(results[0])}")

        # Build response payload
        total_spines = len(results) if results else 0
        successful_matches = 0
        perfect_matches = 0
        spine_regions = []
        book_matches = []
        ocr_failures = []
        
        # Store top matches for each spine for alternatives lookup
        stored_alternatives = {}

        for i, result in enumerate(results or []):
            logger.info(f"Processing result {i}: {type(result)}")
            logger.info(f"Result attributes: {dir(result)}")
            
            if hasattr(result, 'best_match') and result.best_match:
                successful_matches += 1
                if getattr(result.best_match, 'confidence', 0.0) > 0.8:
                    perfect_matches += 1

            if hasattr(result, 'spine_data') and result.spine_data:
                bbox = []
                if hasattr(result.spine_data, 'obb_data') and result.spine_data.obb_data:
                    if 'xyxyxyxy' in result.spine_data.obb_data:
                        raw = result.spine_data.obb_data['xyxyxyxy']
                        bbox = raw.tolist() if hasattr(raw, 'tolist') else raw
                    elif 'xywhr' in result.spine_data.obb_data:
                        xywhr = result.spine_data.obb_data['xywhr']
                        if hasattr(xywhr, 'tolist'):
                            xywhr = xywhr.tolist()
                        cx, cy, w, h, r = xywhr
                        cos_r, sin_r = np.cos(r), np.sin(r)
                        half_w, half_h = w / 2, h / 2
                        corners = [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]
                        rotated = []
                        for x, y in corners:
                            rx = x * cos_r - y * sin_r + cx
                            ry = x * sin_r + y * cos_r + cy
                            rotated.append([rx, ry])
                        bbox = [coord for point in rotated for coord in point]

                # Normalize to plain floats
                coords = [[_to_float(bbox[i]), _to_float(bbox[i+1])] for i in range(0, len(bbox), 2)] if len(bbox) >= 8 else []
                x = _to_float(bbox[0]) if len(bbox) >= 8 else 0.0
                y = _to_float(bbox[1]) if len(bbox) >= 8 else 0.0
                w = _to_float(abs(bbox[2] - bbox[0])) if len(bbox) >= 8 else 0.0
                h = _to_float(abs(bbox[3] - bbox[1])) if len(bbox) >= 8 else 0.0
                confidence_score = _to_float(getattr(result.spine_data, 'confidence_score', 0.0))

                spine_regions.append({
                    "id": getattr(result, 'spine_id', str(uuid.uuid4())),
                    "x": x,
                    "y": y,
                    "width": w,
                    "height": h,
                    "rotation": 0,
                    "confidence": confidence_score,
                    "coordinates": coords,
                })

            if hasattr(result, 'best_match') and result.best_match:
                bm = result.best_match
                spine_id = getattr(result, 'spine_id', str(uuid.uuid4()))
                lb = getattr(bm, 'library_book', None)
                title = getattr(lb, 'title', "") if lb else ""
                author_list = getattr(lb, 'author_name', []) if lb else []
                first_year = getattr(lb, 'first_publish_year', None) if lb else None
                publisher_list = getattr(lb, 'publisher', []) if lb else []
                openlib_key = getattr(lb, 'key', "") if lb else ""
                # Prefer denoised text from match; fallback to result.denoised_text
                ocr_text_value = getattr(bm, 'denoised_text', '') or (getattr(result, 'denoised_text', None).denoised_text if getattr(result, 'denoised_text', None) else '') or ''
                
                # Store top matches for alternatives (excluding the best match)
                if hasattr(result, 'matches') and result.matches:
                    stored_alternatives[spine_id] = []
                    for match in result.matches[1:10]:  # Skip the best match (index 0), take next 9
                        match_lb = getattr(match, 'library_book', None)
                        if match_lb:
                            stored_alternatives[spine_id].append({
                                "key": getattr(match_lb, 'key', ""),
                                "title": getattr(match_lb, 'title', ""),
                                "author_name": getattr(match_lb, 'author_name', []),
                                "first_publish_year": getattr(match_lb, 'first_publish_year', None),
                                "publisher": ", ".join(getattr(match_lb, 'publisher', [])) if isinstance(getattr(match_lb, 'publisher', []), list) else (getattr(match_lb, 'publisher', "") or ""),
                                "match_score": _to_float(getattr(match, 'match_score', getattr(match, 'confidence', 0.0))),
                                "match_type": getattr(match, 'match_type', 'moderate'),
                                "confidence": _to_float(getattr(match, 'confidence', getattr(match, 'match_score', 0.0)))
                            })
                
                book_matches.append({
                    "id": str(uuid.uuid4()),
                    "spine_region_id": spine_id,
                    "title": title,
                    "author_name": author_list or [],
                    "first_publish_year": first_year,
                    "publisher": ", ".join(publisher_list) if isinstance(publisher_list, list) else (publisher_list or ""),
                    "match_score": _to_float(getattr(bm, 'match_score', getattr(bm, 'confidence', 0.0))),
                    "match_type": getattr(bm, 'match_type', 'moderate'),
                    "confidence": _to_float(getattr(bm, 'confidence', getattr(bm, 'match_score', 0.0))),
                    "open_library_id": openlib_key,
                    "ocr_text": ocr_text_value,
                })
            else:
                spine_id = getattr(result, 'spine_id', str(uuid.uuid4()))
                ocr_failures.append({
                    "id": str(uuid.uuid4()),
                    "spine_region_id": spine_id,
                    "coordinates": spine_regions[-1]["coordinates"] if spine_regions else [],
                    "error_type": "no_text_detected",
                    "message": "No text could be extracted from this spine region"
                })

        result_data = {
            "image_url": tasks[task_id].get("image_url", ""),
            "total_spines": total_spines,
            "successful_matches": successful_matches,
            "perfect_matches": perfect_matches,
            "spine_regions": spine_regions,
            "book_matches": book_matches,
            "ocr_failures": ocr_failures,
            "processing_time": 0.0,
            "stored_alternatives": stored_alternatives,  # Store alternatives for fast lookup
        }
        
        logger.info(f"Final result data: {result_data}")
        logger.info(f"Book matches count: {len(book_matches)}")
        if book_matches:
            logger.info(f"First book match: {book_matches[0]}")
        
        tasks[task_id]["result"] = result_data
        update_task_progress(task_id, 100, f"Processing complete! Found {total_spines} spines.")
        tasks[task_id]["status"] = "completed"
    except Exception as e:
        logger.error(f"Pipeline processing failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        tasks[task_id]["status"] = "error"
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["message"] = "Processing failed"

app = FastAPI(title="Spinecat API", version="1.0.0", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8002",
        "http://127.0.0.1:8002"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static uploads
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Spinecat API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "pipeline": "initialized" if pipeline else "not_initialized"
    }

@app.get("/api/debug")
async def debug_endpoint():
    """Debug endpoint to test basic functionality"""
    print("DEBUG ENDPOINT HIT!")
    logger.info("DEBUG ENDPOINT HIT!")
    return {
        "message": "Debug endpoint working",
        "pipeline_status": "initialized" if pipeline else "not_initialized",
        "tasks": {k: {"status": v.get("status"), "progress": v.get("progress"), "message": v.get("message")} for k, v in tasks.items()}
    }



@app.get("/api/progress/{task_id}")
async def get_progress(task_id: str):
    """Get progress for a specific task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Unknown task_id")
    task = tasks[task_id]
    return {
        "status": task.get("status", "pending"),
        "progress": task.get("progress", 0),
        "message": task.get("message", "Ready")
    }

@app.get("/api/result/{task_id}")
async def get_result(task_id: str):
    """Get result for a completed task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Unknown task_id")
    task = tasks[task_id]
    if task.get("status") != "completed":
        return {"status": task.get("status", "processing")}
    return {"status": "completed", **task.get("result", {})}

@app.post("/api/process-image")
async def process_image_start(file: UploadFile = File(...)):
    """Start processing an uploaded image - returns task_id for progress tracking"""
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Save to uploads directory with unique name so we can serve it
    suffix = Path(file.filename).suffix or ".jpg"
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    saved_path = UPLOADS_DIR / f"{task_id}{suffix}"

    content = await file.read()
    with open(saved_path, "wb") as f:
        f.write(content)

    # Register task with image_url for frontend display
    tasks[task_id] = {
        "status": "processing",
        "progress": 0,
        "message": "Queued",
        "result": None,
        "image_url": f"/uploads/{saved_path.name}"
    }

    worker = Thread(target=_run_pipeline_background, args=(task_id, str(saved_path)), daemon=True)
    worker.start()

    return {"task_id": task_id}

@app.get("/api/alternatives-by-spine")
async def get_alternatives_by_spine(
    task_id: str,
    spine_id: str,
    limit: int = 10
):
    """
    Get alternative book matches from stored results (fast)
    This uses the matches that were already computed during initial processing
    """
    if not task_id or not spine_id:
        raise HTTPException(status_code=400, detail="Task ID and spine ID are required")
    
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    if task.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Task not completed")
    
    result = task.get("result", {})
    stored_alternatives = result.get("stored_alternatives", {})
    
    if spine_id not in stored_alternatives:
        return {
            "success": True,
            "spine_id": spine_id,
            "total_results": 0,
            "results": [],
            "note": "No stored alternatives found for this spine"
        }
    
    alternatives = stored_alternatives[spine_id][:limit]
    
    return {
        "success": True,
        "spine_id": spine_id,
        "total_results": len(alternatives),
        "results": alternatives
    }

@app.get("/api/alternatives")
async def get_alternatives(
    ocr_text: str,
    limit: int = 10
):
    """
    Get alternative book matches using the actual backend matching algorithm
    This uses the same algorithm that was used during initial processing
    """
    if not ocr_text or not ocr_text.strip():
        raise HTTPException(status_code=400, detail="OCR text is required")
    
    if not pipeline:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")
    
    if limit > 50:
        limit = 50
    
    try:
        # Use the actual backend matching algorithm to get alternatives
        logger.info(f"Getting alternatives for OCR text: '{ocr_text}' with limit: {limit}")
        
        alternatives = pipeline.get_alternatives(ocr_text, limit)
        logger.info(f"Pipeline returned {len(alternatives) if alternatives else 0} alternatives")
        
        if not alternatives:
            logger.warning(f"No alternatives found for OCR text: '{ocr_text}'")
            return {
                "success": True,
                "ocr_text": ocr_text,
                "total_results": 0,
                "limit": limit,
                "results": []
            }
        
        # Map the results to the expected format
        mapped_results = []
        for book, match_score in alternatives:
            # Extract author names
            author_names = book.get("author_name", [])
            if isinstance(author_names, list):
                author_display = ", ".join(author_names) if author_names else "Unknown Author"
            else:
                author_display = str(author_names) if author_names else "Unknown Author"
            
            mapped = {
                "key": book.get("key", ""),
                "title": book.get("title", "Unknown Title"),
                "author_name": author_display,
                "first_publish_year": book.get("first_publish_year"),
                "publisher": book.get("publisher", "Unknown Publisher"),
                "match_score": match_score.score,
                "match_type": match_score.match_type,
                "confidence": match_score.confidence
            }
            mapped_results.append(mapped)
        
        logger.info(f"Returning {len(mapped_results)} mapped results")
        
        return {
            "success": True,
            "ocr_text": ocr_text,
            "total_results": len(mapped_results),
            "results": mapped_results
        }
        
    except Exception as e:
        logger.error(f"Failed to get alternatives: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get alternatives: {str(e)}")

@app.get("/api/search-books")
async def search_books(query: str, limit: int = 20):
    """
    Manual search endpoint for users to search Open Library database
    This allows users to manually search for book replacements when OCR fails
    """
    if not query or len(query.strip()) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
    
    if limit > 100:
        limit = 100  # Cap at 100 results
    
    try:
        logger.info(f"Manual search for query: '{query}' with limit: {limit}")
        
        # Direct search to Open Library API
        search_url = "https://openlibrary.org/search.json"
        params = {
            "q": query.strip(),
            "limit": limit,
            "fields": "key,title,author_name,first_publish_year,publisher,editions"
        }
        
        headers = {
            'User-Agent': 'Spinecat/1.0 (Manual Book Search)'
        }
        
        response = requests.get(search_url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        search_results = data.get("docs", [])
        logger.info(f"Found {len(search_results)} results from Open Library")
        
        # Map results to a clean format for the frontend
        mapped_results = []
        for result in search_results:
            # Extract author name(s)
            author_names = result.get("author_name", [])
            if isinstance(author_names, list):
                author_display = ", ".join(author_names) if author_names else "Unknown Author"
            else:
                author_display = str(author_names) if author_names else "Unknown Author"
            
            # Extract publisher from editions if available
            publisher = "Unknown Publisher"
            editions = result.get("editions", [])
            
            # Handle different editions formats from Open Library
            try:
                if editions and isinstance(editions, list) and len(editions) > 0:
                    first_edition = editions[0]
                    if isinstance(first_edition, dict):
                        pub_info = first_edition.get("publisher", [])
                        if isinstance(pub_info, list) and pub_info:
                            publisher = ", ".join(pub_info)
                        elif pub_info:
                            publisher = str(pub_info)
                elif editions and isinstance(editions, dict):
                    # Sometimes editions is a dict with keys
                    pub_info = editions.get("publisher", [])
                    if isinstance(pub_info, list) and pub_info:
                        publisher = ", ".join(pub_info)
                    elif pub_info:
                        publisher = str(pub_info)
            except (KeyError, IndexError, TypeError) as e:
                logger.warning(f"Could not extract publisher from editions: {e}")
                publisher = "Unknown Publisher"
            
            mapped = {
                "key": result.get("key", ""),
                "title": result.get("title", "Unknown Title"),
                "author_name": author_display,
                "first_publish_year": result.get("first_publish_year"),
                "publisher": publisher,
                "editions_count": len(editions) if editions else 0,
                "search_score": result.get("score", 0.0)
            }
            mapped_results.append(mapped)
        
        logger.info(f"Successfully mapped {len(mapped_results)} results")
        
        return {
            "success": True,
            "query": query,
            "total_results": len(mapped_results),
            "limit": limit,
            "results": mapped_results
        }
        
    except Exception as e:
        logger.error(f"Manual book search failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/api/search-books-advanced")
async def search_books_advanced(
    title: str = "", 
    author: str = "", 
    publisher: str = "", 
    limit: int = 20
):
    """
    Advanced search endpoint for more specific book searches
    Allows users to search by title, author, and publisher separately
    """
    
    if not title and not author and not publisher:
        raise HTTPException(status_code=400, detail="At least one search parameter (title, author, or publisher) is required")
    
    if limit > 100:
        limit = 100
    
    try:
        # Build search query based on available parameters
        search_parts = []
        if title:
            search_parts.append(f"title:{title}")
        if author:
            search_parts.append(f"author:{author}")
        if publisher:
            search_parts.append(f"publisher:{publisher}")
        
        search_query = " ".join(search_parts)
        
        # Direct, simple search to Open Library API - no pipeline complexity
        search_url = "https://openlibrary.org/search.json"
        params = {
            "q": search_query.strip(),
            "limit": limit,
            "fields": "key,title,author_name,first_publish_year,publisher,editions"
        }
        
        headers = {
            'User-Agent': 'Spinecat/1.0 (Manual Book Search)'
        }
        
        response = requests.get(search_url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        search_results = data.get("docs", [])
        
        # Map results (same as basic search)
        mapped_results = []
        for result in search_results:
            author_names = result.get("author_name", [])
            if isinstance(author_names, list):
                author_display = ", ".join(author_names) if author_names else "Unknown Author"
            else:
                author_display = str(author_names) if author_names else "Unknown Author"
            
            publisher_info = "Unknown Publisher"
            editions = result.get("editions", [])
            
            # Handle different editions formats from Open Library
            try:
                if editions and isinstance(editions, list) and len(editions) > 0:
                    first_edition = editions[0]
                    if isinstance(first_edition, dict):
                        pub_info = first_edition.get("publisher", [])
                        if isinstance(pub_info, list) and pub_info:
                            publisher_info = ", ".join(pub_info)
                        elif pub_info:
                            publisher_info = str(pub_info)
                elif editions and isinstance(editions, dict):
                    # Sometimes editions is a dict with keys
                    pub_info = editions.get("publisher", [])
                    if isinstance(pub_info, list) and pub_info:
                        publisher_info = ", ".join(pub_info)
                    elif pub_info:
                        publisher_info = str(pub_info)
            except (KeyError, IndexError, TypeError) as e:
                logger.warning(f"Could not extract publisher from editions: {e}")
                publisher_info = "Unknown Publisher"
            
            mapped = {
                "key": result.get("key", ""),
                "title": result.get("title", "Unknown Title"),
                "author_name": author_display,
                "first_publish_year": result.get("first_publish_year"),
                "publisher": publisher_info,
                "editions_count": len(editions) if editions else 0,
                "search_score": result.get("score", 0.0)
            }
            mapped_results.append(mapped)
        
        return {
            "success": True,
            "search_query": search_query,
            "parameters": {"title": title, "author": author, "publisher": publisher},
            "total_results": len(mapped_results),
            "limit": limit,
            "results": mapped_results
        }
        
    except Exception as e:
        logger.error(f"Advanced book search failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Advanced search failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT, log_level=config.LOG_LEVEL.lower())
