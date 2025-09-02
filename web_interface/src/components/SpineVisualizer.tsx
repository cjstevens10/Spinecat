import React, { useState, useRef, useEffect, useCallback } from 'react';

import { BookOpen, AlertCircle, Plus, Save, X, Move } from 'lucide-react';

import { SpineRegion, BookMatch } from '../types';

interface SpineVisualizerProps {
  imageUrl: string;
  spineRegions: SpineRegion[];
  bookMatches: BookMatch[];
  selectedSpineId: string | null;
  onSpineSelected: (spineId: string) => void;
  isFinalized: boolean;
  onSpineRegionsUpdated?: (updatedRegions: SpineRegion[]) => void;
  onManualSpineAdded?: (newSpine: SpineRegion) => void;
  onStopEditing?: () => void;
  editingBookId?: string | null; // ID of the book being edited
}

interface EditingState {
  mode: 'none' | 'drawing' | 'editing';
  spineId: string | null;
  vertexIndex: number | null;
  isDragging: boolean;
}

const SpineVisualizer: React.FC<SpineVisualizerProps> = ({
  imageUrl,
  spineRegions,
  bookMatches,
  selectedSpineId,
  onSpineSelected,
  isFinalized,
  onSpineRegionsUpdated,
  onManualSpineAdded,
  onStopEditing,
  editingBookId
}) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [hoveredSpineId, setHoveredSpineId] = useState<string | null>(null);
  const [imageScale, setImageScale] = useState({ scaleX: 1, scaleY: 1, offsetX: 0, offsetY: 0 });
  const [overlayRect, setOverlayRect] = useState<{ left: number; top: number; width: number; height: number } | null>(null);
  const [editingState, setEditingState] = useState<EditingState>({
    mode: 'none',
    spineId: null,
    vertexIndex: null,
    isDragging: false
  });
  const [drawingPoints, setDrawingPoints] = useState<[number, number][]>([]);
  const [localSpineRegions, setLocalSpineRegions] = useState<SpineRegion[]>(spineRegions);
  
  const imageRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);



  // Auto-enter editing mode when editingBookId changes
  useEffect(() => {
    if (editingBookId) {
      // Find the spine region for this book
      const book = bookMatches.find(b => b.id === editingBookId);
      if (book && book.spine_region_id) {
        const spine = spineRegions.find(s => s.id === book.spine_region_id);
        if (spine) {
          setEditingState({
            mode: 'editing',
            spineId: spine.id,
            vertexIndex: null,
            isDragging: false
          });
        } else {
          setEditingState({
            mode: 'drawing',
            spineId: editingBookId,
            vertexIndex: null,
            isDragging: false
          });
        }
      } else {
        setEditingState({
          mode: 'drawing',
          spineId: editingBookId,
          vertexIndex: null,
          isDragging: false
        });
      }
    } else {
      setEditingState({
        mode: 'none',
        spineId: null,
        vertexIndex: null,
        isDragging: false
      });
    }
  }, [editingBookId, bookMatches, spineRegions]);

  // Sync local spine regions when prop changes
  useEffect(() => {
    setLocalSpineRegions(spineRegions);
  }, [spineRegions]);

  // Calculate image scale and offset when image loads
  useEffect(() => {
    if (imageRef.current && imageLoaded) {
      const img = imageRef.current;
      const container = containerRef.current;
      
      if (container) {
        const containerRect = container.getBoundingClientRect();
        const imgRect = img.getBoundingClientRect();
        
        // Calculate scale factors
        const scaleX = imgRect.width / img.naturalWidth;
        const scaleY = imgRect.height / img.naturalHeight;
        
        // Calculate offset (difference between container and image positioning)
        const offsetX = imgRect.left - containerRect.left;
        const offsetY = imgRect.top - containerRect.top;
        
        setImageScale({ scaleX, scaleY, offsetX, offsetY });
        setOverlayRect({ left: offsetX, top: offsetY, width: imgRect.width, height: imgRect.height });
      }
    }
  }, [imageLoaded]);

  // Convert spine polygon to scaled SVG points string
  const getScaledPoints = useCallback((spine: SpineRegion) => {
    if (!spine.coordinates || spine.coordinates.length === 0) return '';
    return spine.coordinates
      .map(([x, y]) => {
        const sx = x * imageScale.scaleX;
        const sy = y * imageScale.scaleY;
        return `${sx},${sy}`;
      })
      .join(' ');
  }, [imageScale.scaleX, imageScale.scaleY]);

  // Convert SVG coordinates back to image coordinates
  const getImageCoordinates = useCallback((svgX: number, svgY: number): [number, number] => {
    return [svgX / imageScale.scaleX, svgY / imageScale.scaleY];
  }, [imageScale.scaleX, imageScale.scaleY]);

  // Compute centroid for label/tooltip positioning within overlay
  const getCentroid = useCallback((spine: SpineRegion) => {
    if (!spine.coordinates || spine.coordinates.length === 0) return { x: 0, y: 0 };
    const pts = spine.coordinates;
    const cx = pts.reduce((a, p) => a + p[0], 0) / pts.length;
    const cy = pts.reduce((a, p) => a + p[1], 0) / pts.length;
    return { x: cx * imageScale.scaleX, y: cy * imageScale.scaleY };
  }, [imageScale.scaleX, imageScale.scaleY]);



  // Helper function to get book data for a spine
  const getBookData = useCallback((spineId: string) => {
    return bookMatches.find(book => book.spine_region_id === spineId);
  }, [bookMatches]);

  // Handle spine region click
  const handleSpineClick = useCallback((spineId: string) => {
    if (editingState.mode === 'drawing') return; // Don't select while drawing
    onSpineSelected(spineId);
  }, [editingState.mode, onSpineSelected]);

  // Handle spine region hover
  const handleSpineHover = useCallback((spineId: string | null) => {
    if (editingState.mode === 'drawing') return; // Don't hover while drawing
    setHoveredSpineId(spineId);
  }, [editingState.mode]);



  // Start drawing mode for manual entry
  const startDrawing = useCallback((spineId: string) => {
    setEditingState({
      mode: 'drawing',
      spineId,
      vertexIndex: null,
      isDragging: false
    });
    setDrawingPoints([]);
    
    // If we're editing an existing book, remove the old spine first
    if (editingBookId && onSpineRegionsUpdated) {
      const book = bookMatches.find(b => b.id === editingBookId);
      if (book && book.spine_region_id) {
        const updatedRegions = localSpineRegions.filter(spine => spine.id !== book.spine_region_id);
        setLocalSpineRegions(updatedRegions);
        onSpineRegionsUpdated(updatedRegions);
      }
    }
  }, [editingBookId, onSpineRegionsUpdated, bookMatches, localSpineRegions]);

  // Cancel editing/drawing mode
  const cancelEditing = useCallback(() => {
    setEditingState({
      mode: 'none',
      spineId: null,
      vertexIndex: null,
      isDragging: false
    });
    setDrawingPoints([]);
  }, []);

  // Save manual drawing
  const saveManualDrawing = useCallback(() => {
    if (drawingPoints.length >= 3 && onManualSpineAdded && editingBookId) {
      const newSpine: SpineRegion = {
        id: `manual_${Date.now()}`,
        x: Math.min(...drawingPoints.map(p => p[0])),
        y: Math.min(...drawingPoints.map(p => p[1])),
        width: Math.max(...drawingPoints.map(p => p[0])) - Math.min(...drawingPoints.map(p => p[0])),
        height: Math.max(...drawingPoints.map(p => p[1])) - Math.min(...drawingPoints.map(p => p[1])),
        rotation: 0,
        confidence: 0.9,
        coordinates: drawingPoints
      };
      
      onManualSpineAdded(newSpine);
      cancelEditing();
    }
  }, [drawingPoints, onManualSpineAdded, editingBookId, cancelEditing]);

  // Handle SVG click for drawing
  const handleSvgClick = useCallback((event: React.MouseEvent<SVGSVGElement>) => {
    if (editingState.mode !== 'drawing') return;
    
    const svg = svgRef.current;
    if (!svg) return;
    
    const rect = svg.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    const imageCoords = getImageCoordinates(x, y);
    setDrawingPoints(prev => [...prev, imageCoords]);
  }, [editingState.mode, getImageCoordinates]);

  // Handle vertex drag start
  const handleVertexDragStart = useCallback((spineId: string, vertexIndex: number) => {
    setEditingState(prev => ({
      ...prev,
      mode: 'editing',
      spineId,
      vertexIndex,
      isDragging: true
    }));
  }, []);

  // Handle vertex drag - use local state for smooth dragging
  const handleVertexDrag = useCallback((spineId: string, vertexIndex: number, newX: number, newY: number) => {
    // Don't call onSpineRegionsUpdated during dragging - just update local state
    // This prevents re-renders and makes dragging smooth
    const imageCoords = getImageCoordinates(newX, newY);
    
    // Update the local spineRegions state for immediate visual feedback
    setLocalSpineRegions(prev => prev.map(spine => {
      if (spine.id === spineId && spine.coordinates) {
        const newCoordinates = [...spine.coordinates];
        newCoordinates[vertexIndex] = imageCoords;
        return { ...spine, coordinates: newCoordinates };
      }
      return spine;
    }));
  }, [getImageCoordinates]);

  // Handle mouse move for vertex dragging
  const handleMouseMove = useCallback((event: React.MouseEvent<SVGSVGElement>) => {
    if (editingState.mode !== 'editing' || !editingState.isDragging || !editingState.spineId || editingState.vertexIndex === null) return;
    
    const svg = svgRef.current;
    if (!svg) return;
    
    const rect = svg.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    handleVertexDrag(editingState.spineId, editingState.vertexIndex, x, y);
  }, [editingState, handleVertexDrag]);

  // Handle vertex drag end
  const handleVertexDragEnd = useCallback(() => {
    setEditingState(prev => ({
      ...prev,
      isDragging: false
    }));
    
    // Sync the local changes back to the parent component
    if (onSpineRegionsUpdated) {
      onSpineRegionsUpdated(localSpineRegions);
    }
  }, [onSpineRegionsUpdated, localSpineRegions]);

  // Render vertex handles for editing
  const renderVertexHandles = useCallback((spine: SpineRegion) => {
    if (editingState.mode !== 'editing' || editingState.spineId !== spine.id) return null;
    
    return spine.coordinates?.map((coord, index) => {
      const [x, y] = coord;
      const svgX = x * imageScale.scaleX;
      const svgY = y * imageScale.scaleY;
      
      return (
        <circle
          key={`vertex-${spine.id}-${index}`}
          cx={svgX}
          cy={svgY}
          r={6}
          fill="#FF6B6B"
          stroke="#FF4757"
          strokeWidth={2}
          cursor="move"
          onMouseDown={(e) => {
            e.stopPropagation();
            handleVertexDragStart(spine.id, index);
          }}
          onMouseUp={handleVertexDragEnd}
          style={{ pointerEvents: editingState.isDragging ? 'none' : 'auto' }}
        />
      );
    });
  }, [editingState.mode, editingState.spineId, editingState.isDragging, imageScale.scaleX, imageScale.scaleY, handleVertexDragStart, handleVertexDragEnd]);

  // Render drawing points
  const renderDrawingPoints = useCallback(() => {
    if (editingState.mode !== 'drawing' || drawingPoints.length === 0) return null;
    
    return (
      <g>
        {/* Draw lines between points */}
        {drawingPoints.length > 1 && (
          <polyline
            points={drawingPoints.map(([x, y]) => `${x * imageScale.scaleX},${y * imageScale.scaleY}`).join(' ')}
            fill="none"
            stroke="#FF6B6B"
            strokeWidth={2}
            strokeDasharray="5,5"
          />
        )}
        
        {/* Draw vertex points */}
        {drawingPoints.map(([x, y], index) => (
          <circle
            key={`drawing-${index}`}
            cx={x * imageScale.scaleX}
            cy={y * imageScale.scaleY}
            r={4}
            fill="#FF6B6B"
            stroke="#FF4757"
            strokeWidth={2}
          />
        ))}
      </g>
    );
  }, [editingState.mode, drawingPoints, imageScale.scaleX, imageScale.scaleY]);

  // Render spine region as polygon within an SVG aligned to the image
  const renderSpineRegion = useCallback((spine: SpineRegion) => {
    const book = getBookData(spine.id);
    const points = getScaledPoints(spine);
    const { x: cx, y: cy } = getCentroid(spine);
    const isSelected = selectedSpineId === spine.id;
    const isHovered = hoveredSpineId === spine.id;
    const isEditing = editingState.mode === 'editing' && editingState.spineId === spine.id;
    const isDrawing = editingState.mode === 'drawing' && editingState.spineId === spine.id;
    const hasSelection = selectedSpineId !== null;
    const isOtherSelected = hasSelection && !isEditing && !isDrawing;

    // Only show spines that are being edited or not in editing mode
    if (editingBookId && !isEditing && !isDrawing) {
      // Check if this spine belongs to the book being edited
      const isTargetBook = book && book.id === editingBookId;
      if (!isTargetBook) {
        return null;
      }
    }

    const fill = isEditing || isDrawing ? 'rgba(255,107,107,0.3)' : 
                 isSelected ? 'rgba(59,130,246,0.25)' : 
                 isHovered ? 'rgba(59,130,246,0.18)' : 
                 'rgba(59,130,246,0.12)';
    const stroke = isEditing || isDrawing ? '#FF6B6B' :
                  isSelected ? '#60A5FA' : 
                  isHovered ? '#3B82F6' : 
                  '#2563EB';
    const opacity = isOtherSelected && !isEditing && !isDrawing ? 0.35 : 1;

    return (
      <g key={spine.id} style={{ opacity }}
         onMouseEnter={() => handleSpineHover(spine.id)}
         onMouseLeave={() => handleSpineHover(null)}
         onClick={() => handleSpineClick(spine.id)}
      >
        <polygon points={points} fill={fill} stroke={stroke} strokeWidth={2} />
        
        {/* Spine number label at centroid */}
        <text x={cx} y={cy} textAnchor="middle" dominantBaseline="middle" fill="#6B7280" fontSize={12} fontWeight={600}>
          {spineRegions.findIndex(s => s.id === spine.id) + 1}
        </text>
        

        
        {/* Vertex handles for editing */}
        {renderVertexHandles(spine)}
        
        {/* Tooltip near centroid */}
        {hoveredSpineId === spine.id && book && overlayRect && !isEditing && (
          <foreignObject x={Math.min(Math.max(cx + 8, 0), overlayRect.width - 200)} y={Math.max(cy - 40, 0)} width={200} height={80}>
            <div className="bg-gray-900 text-white text-xs px-3 py-2 rounded-lg shadow-lg" style={{ pointerEvents: 'none' }}>
              <div className="font-medium mb-1 truncate">{book.title}</div>
              <div className="text-gray-300 truncate">by {Array.isArray(book.author_name) ? book.author_name.join(', ') : book.author_name || 'Unknown Author'}</div>
              {book.first_publish_year && (
                <div className="text-gray-400">{book.first_publish_year}</div>
              )}
            </div>
          </foreignObject>
        )}
      </g>
    );
  }, [getBookData, getScaledPoints, getCentroid, selectedSpineId, hoveredSpineId, editingState, editingBookId, spineRegions, overlayRect, renderVertexHandles, handleSpineHover, handleSpineClick]);

  return (
    <div className="card p-0 overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-500 mb-2">
              Book Spine Detection
            </h3>
            <p className="text-sm text-gray-400">
              {spineRegions.length} spine{spineRegions.length !== 1 ? 's' : ''} detected
              {bookMatches.length > 0 && ` • ${bookMatches.length} book${bookMatches.length !== 1 ? 's' : ''} identified`}
            </p>
          </div>
          
          {/* Editing Controls */}
          {!isFinalized && (
            <div className="flex items-center space-x-2">
                             {editingState.mode === 'none' && editingBookId && (
                 <>
                   <button
                     onClick={() => startDrawing(editingBookId)}
                     className="btn-secondary text-sm px-3 py-1 flex items-center space-x-1"
                   >
                     <Plus className="w-4 h-4" />
                     <span>Draw OBB</span>
                   </button>
                 </>
               )}
              
              {editingState.mode === 'drawing' && (
                <>
                  <button
                    onClick={saveManualDrawing}
                    disabled={drawingPoints.length < 3}
                    className="btn-primary text-sm px-3 py-1 flex items-center space-x-1 disabled:opacity-50"
                  >
                    <Save className="w-4 h-4" />
                    <span>Save OBB</span>
                  </button>
                  <button
                    onClick={cancelEditing}
                    className="btn-danger text-sm px-3 py-1 flex items-center space-x-1"
                  >
                    <X className="w-4 h-4" />
                    <span>Cancel</span>
                  </button>
                </>
              )}
              
                            {editingState.mode === 'editing' && (
                <>
                  <button
                    onClick={() => startDrawing(editingBookId || '')}
                    className="btn-secondary text-sm px-3 py-1 flex items-center space-x-1"
                  >
                    <Plus className="w-4 h-4" />
                    <span>Draw New OBB</span>
                  </button>
                  <div className="text-sm text-gray-400 px-3 py-1 flex items-center space-x-1">
                    <Move className="w-4 h-4" />
                    <span>Drag vertices to edit</span>
                  </div>
                  <button
                    onClick={() => {
                      cancelEditing();
                      if (onStopEditing) onStopEditing();
                    }}
                    className="btn-primary text-sm px-3 py-1 flex items-center space-x-1"
                  >
                    <Save className="w-4 h-4" />
                    <span>Done</span>
                  </button>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Image Container */}
      <div 
        ref={containerRef}
        className="relative bg-gray-100 min-h-[400px] flex items-center justify-center"
      >
        {!imageLoaded && (
          <div className="text-center text-gray-400">
            <BookOpen className="w-12 h-12 mx-auto mb-2 text-gray-400" />
            <p>Loading image...</p>
          </div>
        )}

        {/* Main Image */}
        <img
          ref={imageRef}
          src={imageUrl}
          alt="Book spines"
          className="max-w-full max-h-[600px] object-contain"
          onLoad={() => setImageLoaded(true)}
          onError={() => setImageLoaded(false)}
        />

        {/* Spine Regions Overlay */}
        {imageLoaded && overlayRect && (
          <svg
            ref={svgRef}
            className="absolute cursor-crosshair"
            style={{ left: overlayRect.left, top: overlayRect.top }}
            width={overlayRect.width}
            height={overlayRect.height}
            onClick={handleSvgClick}
            onMouseMove={handleMouseMove}
            onMouseUp={handleVertexDragEnd}
          >
            {localSpineRegions.map(renderSpineRegion)}
            {renderDrawingPoints()}
          </svg>
        )}

        {/* No Spines Detected */}
        {imageLoaded && spineRegions.length === 0 && editingState.mode !== 'drawing' && (
          <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-90">
            <div className="text-center text-gray-400">
              <AlertCircle className="w-12 h-12 mx-auto mb-2 text-gray-400" />
              <p className="text-lg font-medium">No book spines detected</p>
              <p className="text-sm">Try uploading a clearer image or draw spines manually</p>
            </div>
          </div>
        )}

        {/* Drawing Instructions */}
        {imageLoaded && editingState.mode === 'drawing' && (
          <div className="absolute top-4 left-4 bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg">
            <p className="text-sm font-medium">Click to add vertices. Need at least 3 points.</p>
            <p className="text-xs opacity-90">Click "Save OBB" when done</p>
          </div>
        )}
      </div>

      {/* Legend */}
      {spineRegions.length > 0 && (
        <div className="p-4 bg-gray-50 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm text-gray-400">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-primary-500 rounded"></div>
                <span>Detected spine</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-primary-600 rounded ring-2 ring-primary-400"></div>
                <span>Selected</span>
              </div>
              {!isFinalized && (
                <>
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-red-500 rounded"></div>
                    <span>Editing</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-red-400 rounded"></div>
                    <span>Drawing</span>
                  </div>
                </>
              )}
            </div>
            
            <div className="text-xs">
              {editingState.mode === 'none' && 'Click on spine regions to select books'}
              {editingState.mode === 'drawing' && 'Click on image to draw spine outline'}
              {editingState.mode === 'editing' && 'Drag red vertices to edit spine shape'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SpineVisualizer;
