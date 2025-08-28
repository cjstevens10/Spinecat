# 🚀 Spinecat Web Interface Setup Guide

Complete setup guide for the Spinecat web interface with FastAPI backend.

## 📋 Prerequisites

- Python 3.8+ with pip
- Node.js 16+ with npm
- Google Cloud Vision API key
- YOLO model file (`yolo-spine-obb.pt`)

## 🏗️ Project Structure

```
web_interface/
├── src/                    # React frontend
├── backend/               # FastAPI backend
│   ├── main.py           # Main API application
│   ├── config.py         # Configuration management
│   ├── run.py            # Startup script
│   └── requirements.txt  # Python dependencies
├── start_backend.bat     # Windows backend starter
└── SETUP.md              # This file
```

## 🔧 Backend Setup

### 1. Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment
Copy the template and fill in your details:
```bash
cp env.template .env
```

Edit `.env` with your configuration:
```env
GOOGLE_VISION_API_KEY=your_actual_api_key_here
YOLO_MODEL_PATH=../models/yolo-spine-obb.pt
```

### 3. Start Backend Server
```bash
python run.py
```

**Or use the Windows batch file:**
```bash
start_backend.bat
```

The backend will be available at `http://localhost:8000`

## 🎨 Frontend Setup

### 1. Install Node Dependencies
```bash
npm install
```

### 2. Start Development Server
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

## 🔗 Integration Points

### Backend → Pipeline
- **Path**: `../permanent_pipeline/`
- **Components**: YOLO detection, OCR, denoising, matching
- **API**: FastAPI endpoints for image processing

### Frontend → Backend
- **API Service**: `src/services/api.ts`
- **Endpoints**: Image upload, book search, health checks
- **CORS**: Configured for localhost:3000

## 🧪 Testing the System

### 1. Health Check
Visit `http://localhost:8000/health` to verify backend status

### 2. API Documentation
Visit `http://localhost:8000/docs` for interactive API docs

### 3. Frontend Integration
Upload an image through the web interface to test the full pipeline

## 🐛 Troubleshooting

### Backend Issues
- **Import errors**: Check that `permanent_pipeline` directory exists
- **Model not found**: Verify YOLO model path in `.env`
- **API key error**: Ensure Google Vision API key is set

### Frontend Issues
- **CORS errors**: Verify backend is running on port 8000
- **API calls failing**: Check backend health endpoint
- **Build errors**: Ensure all dependencies are installed

### Common Solutions
1. **Restart both servers** after configuration changes
2. **Check console logs** for detailed error messages
3. **Verify file paths** are correct for your system
4. **Ensure ports 3000 and 8000** are available

## 🚀 Production Deployment

### Backend
- Use `uvicorn` with production settings
- Set `reload=False` in production
- Configure proper CORS origins
- Use environment variables for secrets

### Frontend
- Build with `npm run build`
- Serve static files from backend or web server
- Update API base URL for production

## 📚 Next Steps

1. **Test with real images** to verify pipeline integration
2. **Add error handling** for edge cases
3. **Implement user authentication** if needed
4. **Add image caching** for better performance
5. **Create deployment scripts** for production

## 🆘 Getting Help

- Check the backend logs for detailed error messages
- Verify all environment variables are set correctly
- Ensure the `permanent_pipeline` directory structure matches expectations
- Test individual components (YOLO, OCR, API) separately if needed






