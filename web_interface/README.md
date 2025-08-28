# Spinecat Web Interface

A modern, minimalist web application for book spine detection and identification using AI-powered OCR and matching algorithms.

## 🚀 **Features**

### **Core Functionality**
- **Smart Image Upload**: Drag & drop interface with quality validation
- **AI-Powered Detection**: YOLOv8-OBB spine detection with confidence scoring
- **Advanced OCR**: Google Cloud Vision API integration for text extraction
- **Intelligent Matching**: ML-based book matching against Open Library database
- **Interactive Visualization**: Clickable spine regions with real-time highlighting

### **User Experience**
- **Real-time Processing**: Live progress updates and status tracking
- **Interactive Management**: Edit, replace, or delete book matches
- **Open Library Search**: Custom search with autocomplete for corrections
- **OCR Failure Handling**: Manual entry for failed text detection
- **Export Options**: Generate labeled images and detailed reports

### **Quality Assurance**
- **Image Validation**: Resolution, blur detection, and format checking
- **100% Accuracy Goal**: User-editable results for perfect identification
- **Professional Export**: Numbered labeling system for clean output

## 🛠 **Technology Stack**

### **Frontend**
- **React 18** with TypeScript for robust development
- **Tailwind CSS** for minimalist, responsive design
- **Framer Motion** for smooth animations and transitions
- **React Dropzone** for intuitive file uploads
- **Lucide React** for consistent iconography

### **Backend Integration**
- **FastAPI** backend (planned) for pipeline integration
- **WebSocket** support for real-time updates
- **Open Library API** for book metadata
- **Google Cloud Vision** for OCR processing

## 📁 **Project Structure**

```
web_interface/
├── public/
│   └── index.html              # HTML template
├── src/
│   ├── components/             # React components
│   │   ├── ImageUploader.tsx   # File upload & validation
│   │   ├── ProcessingStatus.tsx # Progress tracking
│   │   ├── SpineVisualizer.tsx # Interactive image display
│   │   ├── BookListManager.tsx # Book list management
│   │   └── FinalizePanel.tsx   # Export & finalization
│   ├── types/                  # TypeScript definitions
│   │   └── index.ts           # Core data types
│   ├── utils/                  # Utility functions
│   │   └── imageUtils.ts      # Image validation & processing
│   ├── hooks/                  # Custom React hooks
│   ├── App.tsx                 # Main application component
│   ├── index.tsx               # Application entry point
│   └── index.css               # Global styles & Tailwind
├── package.json                # Dependencies & scripts
├── tailwind.config.js          # Tailwind CSS configuration
├── postcss.config.js           # PostCSS configuration
└── README.md                   # This file
```

## 🚀 **Getting Started**

### **Prerequisites**
- Node.js 16+ and npm
- Modern web browser with ES6+ support

### **Installation**
```bash
# Clone the repository
git clone <repository-url>
cd web_interface

# Install dependencies
npm install

# Start development server
npm start
```

### **Development Commands**
```bash
npm start          # Start development server
npm run build      # Build for production
npm run test       # Run tests
npm run eject      # Eject from Create React App
```

## 🎨 **Design Principles**

### **Minimalist & Smooth**
- Clean, uncluttered interface design
- Smooth animations and micro-interactions
- Consistent visual hierarchy and spacing
- Intuitive user flow and navigation

### **Responsive Design**
- Desktop-first approach for precise interactions
- Mobile-friendly responsive layout
- Touch-optimized controls for tablets

### **Accessibility**
- Keyboard navigation support
- Screen reader compatibility
- High contrast color schemes
- Clear visual feedback

## 🔧 **Configuration**

### **Environment Variables**
```bash
# API Keys (to be configured)
REACT_APP_GOOGLE_VISION_API_KEY=your_api_key
REACT_APP_OPEN_LIBRARY_BASE_URL=https://openlibrary.org
```

### **Tailwind Customization**
The design system uses custom color palettes and animations defined in `tailwind.config.js`:

- **Primary Colors**: Blue-based theme for main actions
- **Status Colors**: Success (green), warning (yellow), error (red)
- **Custom Animations**: Fade-in, slide-up, and pulse effects

## 📱 **Component Architecture**

### **Core Components**

#### **ImageUploader**
- Handles file upload with drag & drop
- Performs image quality validation
- Integrates with processing pipeline
- Provides user feedback and guidance

#### **SpineVisualizer**
- Displays uploaded image with spine overlays
- Interactive spine region selection
- Real-time highlighting and tooltips
- Numbered labeling system

#### **BookListManager**
- Dynamic book list with real-time updates
- Edit, replace, and delete functionality
- Open Library search integration
- OCR failure handling

#### **ProcessingStatus**
- Real-time progress tracking
- Step-by-step processing visualization
- Error handling and user feedback
- Smooth state transitions

## 🔄 **Data Flow**

```
1. Image Upload → Validation → Processing
2. YOLO Detection → Spine Region Extraction
3. OCR Processing → Text Extraction & Denoising
4. Library Search → Book Matching & Scoring
5. User Review → Interactive Management
6. Finalization → Export & Download
```

## 🚧 **Development Status**

### **Phase 1: Core Infrastructure** ✅
- [x] React application setup
- [x] TypeScript configuration
- [x] Tailwind CSS integration
- [x] Basic component structure
- [x] Image upload and validation

### **Phase 2: Interactive Features** 🚧
- [ ] Spine visualization component
- [ ] Book list management
- [ ] Open Library search integration
- [ ] Real-time updates

### **Phase 3: Polish & Export** 📋
- [ ] Finalization workflow
- [ ] Export functionality
- [ ] Performance optimization
- [ ] User testing & refinement

## 🤝 **Contributing**

### **Development Guidelines**
- Follow TypeScript best practices
- Use functional components with hooks
- Maintain consistent code formatting
- Write comprehensive component documentation

### **Code Quality**
- ESLint configuration for code standards
- Prettier for consistent formatting
- TypeScript strict mode enabled
- Component prop validation

## 📄 **License**

This project is part of the Spinecat book spine detection system. Please refer to the main project license for usage terms.

## 🆘 **Support**

For technical support or feature requests:
- Check the main project documentation
- Review existing issues and discussions
- Contact the development team

---

**Built with ❤️ for book lovers and librarians everywhere**






