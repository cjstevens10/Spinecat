import React, { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings, Download } from 'lucide-react';

import { ProcessingState, ProcessingResult } from './types';
import { apiService } from './services/api';
import ImageUploader from './components/ImageUploader';
import SpineVisualizer from './components/SpineVisualizer';
import BookListManager from './components/BookListManager';
import ProcessingStatus from './components/ProcessingStatus';
import FinalizePanel from './components/FinalizePanel';
import ManualBookSearch from './components/ManualBookSearch';

const App: React.FC = () => {
  const [processingState, setProcessingState] = useState<ProcessingState>({
    status: 'idle',
    progress: 0,
    message: 'Ready to process images'
  });
  
  const [processingResult, setProcessingResult] = useState<ProcessingResult | null>(null);
  const [selectedSpineId, setSelectedSpineId] = useState<string | null>(null);
  const [isFinalized, setIsFinalized] = useState(false);
  
  // Function to scroll to book when spine is clicked
  const handleSpineSelected = (spineId: string) => {
    console.log('🎯 Spine clicked:', spineId);
    setSelectedSpineId(spineId);
    
    // Find the corresponding book and scroll to it
    if (processingResult) {
      const book = processingResult.book_matches.find(b => b.spine_region_id === spineId);
      console.log('🔍 Found book for spine:', book);
      if (book) {
        // Small delay to ensure DOM is updated
        setTimeout(() => {
          const bookElement = document.querySelector(`[data-book-id="${book.id}"]`);
          console.log('🔍 Looking for book element:', book.id, bookElement);
          if (bookElement) {
            console.log('✅ Scrolling to book:', book.title);
            bookElement.scrollIntoView({ 
              behavior: 'smooth', 
              block: 'center',
              inline: 'nearest'
            });
            
            // Add highlight effect
            bookElement.classList.add('ring-2', 'ring-blue-400', 'ring-opacity-75');
            setTimeout(() => {
              bookElement.classList.remove('ring-2', 'ring-blue-400', 'ring-opacity-75');
            }, 2000);
          } else {
            console.warn('❌ Book element not found for ID:', book.id);
          }
        }, 100);
      } else {
        console.warn('❌ No book found for spine ID:', spineId);
      }
    }
  };
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [isManualSearchOpen, setIsManualSearchOpen] = useState(false);
  const [editingBookId, setEditingBookId] = useState<string | null>(null);
  
  // Progress polling for current task
  useEffect(() => {
    let intervalId: NodeJS.Timeout;
    
    if (processingState.status === 'processing' && currentTaskId) {
      console.log('🔄 App: Starting progress polling for task:', currentTaskId);
      intervalId = setInterval(async () => {
        try {
          const data = await apiService.getProgress(currentTaskId);
          console.log('📡 App: Polled progress:', data);
          
          setProcessingState(prev => ({
            ...prev,
            status: data.status === 'completed' ? 'completed' : 'processing',
            progress: data.progress,
            message: data.message
          }));
          
          // If task is completed, fetch the result
          if (data.status === 'completed') {
            try {
              const result = await apiService.getResult(currentTaskId);
              console.log('✅ App: Got result:', result);
              console.log('🔍 App: Result structure:', {
                total_spines: result.total_spines,
                successful_matches: result.successful_matches,
                book_matches_length: result.book_matches?.length,
                spine_regions_length: result.spine_regions?.length,
                ocr_failures_length: result.ocr_failures?.length
              });
              if (result.book_matches && result.book_matches.length > 0) {
                console.log('🔍 App: First book match:', result.book_matches[0]);
              }
              setProcessingResult(result);
              setProcessingState(prev => ({
                ...prev,
                status: 'completed',
                progress: 100,
                message: `Processed ${result.total_spines} spines with ${result.successful_matches} successful matches`
              }));
            } catch (error) {
              console.error('❌ App: Failed to get result:', error);
              setProcessingState(prev => ({
                ...prev,
                status: 'error',
                message: 'Failed to get processing result'
              }));
            }
          }
          
        } catch (error) {
          console.error('❌ App: Failed to poll progress:', error);
        }
      }, 200); // Poll every 200ms
    }

    return () => {
      if (intervalId) {
        console.log('🔄 App: Stopping progress polling...');
        clearInterval(intervalId);
      }
    };
  }, [processingState.status, currentTaskId]);

  const handleImageProcessed = (result: ProcessingResult) => {
    setProcessingResult(result);
    setProcessingState({
      status: 'completed',
      progress: 100,
      message: `Processed ${result.total_spines} spines with ${result.successful_matches} successful matches`
    });
  };

  const handleImageUpload = async (file: File) => {
    try {
      setProcessingState({
        status: 'processing',
        progress: 0,
        message: 'Starting image processing...'
      });

      // Start the processing task
      const { task_id } = await apiService.startProcess(file);
      setCurrentTaskId(task_id);
      console.log('🚀 App: Started task:', task_id);

    } catch (error) {
      console.error('❌ App: Failed to start processing:', error);
      setProcessingState({
        status: 'error',
        progress: 0,
        message: `Failed to start processing: ${error instanceof Error ? error.message : 'Unknown error'}`
      });
    }
  };

  const handleReset = () => {
    setProcessingState({
      status: 'idle',
      progress: 0,
      message: 'Ready to process images'
    });
    setProcessingResult(null);
    setSelectedSpineId(null);
    setIsFinalized(false);
    setCurrentTaskId(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <Toaster position="top-right" />
      
      {/* Header */}
      <header className="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-xl font-semibold text-slate-200">
              Book Spine Analyzer
            </h1>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => window.open('http://127.0.0.1:8002/docs', '_blank')}
                className="flex items-center space-x-2 px-3 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-700/50 rounded-md transition-colors"
              >
                <Settings className="w-4 h-4" />
                <span>API Docs</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <AnimatePresence mode="wait">
          {processingState.status === 'idle' && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <ImageUploader onImageUpload={handleImageUpload} />
            </motion.div>
          )}

          {processingState.status === 'processing' && (
            <motion.div
              key="processing"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <ProcessingStatus state={processingState} />
            </motion.div>
          )}

          {processingState.status === 'completed' && processingResult && (
            <motion.div
              key="results"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <div className="space-y-8">
                {/* Results Header */}
                <div className="text-center">
                  <h2 className="text-3xl font-bold text-slate-100 mb-2">
                    Analysis Complete!
                  </h2>
                  <p className="text-slate-400">
                    Found {processingResult.total_spines} spines with {processingResult.successful_matches} successful matches
                  </p>
                  <button
                    onClick={handleReset}
                    className="mt-4 px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
                  >
                    Process Another Image
                  </button>
                </div>

                {/* Main Results Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {/* Image with Spine Overlays */}
                  <div className="space-y-4">
                    <h3 className="text-xl font-semibold text-slate-200">Detected Spines</h3>
                    <SpineVisualizer
                      imageUrl={`${apiService.getBaseUrl()}${processingResult.image_url}`}
                      spineRegions={processingResult.spine_regions}
                      bookMatches={processingResult.book_matches}
                      selectedSpineId={selectedSpineId}
                      onSpineSelected={handleSpineSelected}
                      isFinalized={isFinalized}
                      onSpineRegionsUpdated={(updatedRegions) => {
                        setProcessingResult(prev => prev ? {
                          ...prev,
                          spine_regions: updatedRegions
                        } : null);
                      }}
                      onManualSpineAdded={(newSpine) => {
                        setProcessingResult(prev => prev ? {
                          ...prev,
                          spine_regions: [...prev.spine_regions, newSpine],
                          // Update the existing book's spine_region_id to point to the new spine
                          book_matches: prev.book_matches.map(book => 
                            book.id === editingBookId 
                              ? { ...book, spine_region_id: newSpine.id }
                              : book
                          )
                        } : null);
                        // Stop editing mode
                        setEditingBookId(null);
                      }}
                      onStopEditing={() => setEditingBookId(null)}
                      editingBookId={editingBookId}
                    />
                  </div>

                  {/* Book Matches and Management */}
                  <div className="space-y-4">
                    <h3 className="text-xl font-semibold text-slate-200">Identified Books</h3>
                    <BookListManager
                      bookMatches={processingResult.book_matches}
                      ocrFailures={processingResult.ocr_failures}
                      selectedSpineId={selectedSpineId}
                      onSpineSelected={handleSpineSelected}
                      onBookListUpdated={(updatedMatches) => {
                        setProcessingResult(prev => prev ? {
                          ...prev,
                          book_matches: updatedMatches,
                          // Filter out spine regions that no longer have corresponding books
                          spine_regions: prev.spine_regions.filter(spine => 
                            updatedMatches.some(book => book.spine_region_id === spine.id)
                          )
                        } : null);
                      }}
                      onStartEditing={(bookId) => {
                        console.log('🔄 Starting edit for book:', bookId);
                        console.log('🔄 Current editingBookId before set:', editingBookId);
                        if (editingBookId === bookId) {
                          console.log('🔄 Book is already in editing mode, toggling off');
                          setEditingBookId(null);
                        } else {
                          console.log('🔄 Setting editingBookId to:', bookId);
                          setEditingBookId(bookId);
                        }
                      }}
                      onStopEditing={() => setEditingBookId(null)}
                    />
                  </div>
                </div>

                {/* Finalize Panel */}
                <FinalizePanel
                  processingResult={processingResult}
                  onUnfinalize={() => setIsFinalized(false)}
                />
              </div>
            </motion.div>
          )}

          {processingState.status === 'error' && (
            <motion.div
              key="error"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <div className="text-center">
                <h2 className="text-2xl font-bold text-red-400 mb-4">
                  Processing Failed
                </h2>
                <p className="text-slate-300 mb-6">
                  {processingState.message}
                </p>
                <button
                  onClick={handleReset}
                  className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
                >
                  Try Again
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Manual Book Search Modal */}
      <ManualBookSearch
        isOpen={isManualSearchOpen}
        onClose={() => setIsManualSearchOpen(false)}
        onBookSelected={(book) => {
          console.log('Selected book from manual search:', book);
          // You can add logic here to handle the selected book
          // For example, add it to a list or replace a failed match
        }}
      />
    </div>
  );
};

export default App;
