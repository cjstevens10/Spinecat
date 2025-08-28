# Spinecat Backend API

FastAPI backend for the Spinecat web interface that integrates with your existing pipeline.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `env.template` to `.env` and fill in your configuration:
```bash
cp env.template .env
```

Required environment variables:
- `GOOGLE_VISION_API_KEY`: Your Google Cloud Vision API key
- `YOLO_MODEL_PATH`: Path to your YOLO model (default: `../models/yolo-spine-obb.pt`)

### 3. Run the Server
```bash
python run.py
```

The API will be available at `http://localhost:8000`

## 📚 API Endpoints

### Health Check
- `GET /` - Basic health check
- `GET /health` - Detailed health check with pipeline status

### Core Functionality
- `POST /api/process-image` - Process uploaded images through the pipeline
- `GET /api/search-books` - Search for books using Open Library API

## 🔧 Configuration

The backend automatically loads configuration from:
1. Environment variables
2. `.env` file
3. Default values

### Key Settings
- **API Host/Port**: Server binding (default: 0.0.0.0:8000)
- **CORS**: Configured for frontend at localhost:3000
- **File Upload**: Max 10MB, supports JPG/PNG
- **Pipeline**: Integrates with your existing Spinecat pipeline

## 🔗 Integration

The backend connects to your existing pipeline in `../permanent_pipeline/`:
- YOLOv8-OBB spine detection
- Google Vision OCR
- Text denoising
- Open Library book matching

## 📖 API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

## 🐛 Troubleshooting

### Common Issues
1. **Pipeline not initialized**: Check YOLO model path and Google Vision API key
2. **Import errors**: Ensure `permanent_pipeline` directory exists and is accessible
3. **CORS issues**: Verify frontend URL in configuration

### Logs
Check console output for detailed error messages and pipeline status.






