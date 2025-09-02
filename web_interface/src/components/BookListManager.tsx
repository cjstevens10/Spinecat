import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, Trash2, Search, AlertTriangle, Plus, RefreshCw, CheckCircle, Edit3 } from 'lucide-react';
import toast from 'react-hot-toast';

import { BookMatch, OCRFailure } from '../types';
import AlternativesModal from './AlternativesModal';
import ManualBookSearch from './ManualBookSearch';

interface BookListManagerProps {
  bookMatches: BookMatch[];
  ocrFailures: OCRFailure[];
  selectedSpineId: string | null;
  taskId: string | null;  // Add task ID for alternatives lookup
  onSpineSelected: (spineId: string) => void;
  onBookListUpdated: (updatedMatches: BookMatch[]) => void;
  onStartEditing?: (bookId: string) => void;
  onStopEditing?: () => void;
}

const BookListManager: React.FC<BookListManagerProps> = ({
  bookMatches,
  ocrFailures,
  selectedSpineId,
  taskId,
  onSpineSelected,
  onBookListUpdated,
  onStartEditing,
  onStopEditing
}) => {
  const [showSearchModal, setShowSearchModal] = useState(false);
  const [showAlternativesModal, setShowAlternativesModal] = useState(false);
  const [selectedBookForAlternatives, setSelectedBookForAlternatives] = useState<BookMatch | null>(null);
  const [selectedBookForSearch, setSelectedBookForSearch] = useState<BookMatch | null>(null);
  const [modifiedBooks, setModifiedBooks] = useState<Set<string>>(new Set());



  // Handle book selection
  const handleBookClick = (book: BookMatch) => {
    onSpineSelected(book.spine_region_id);
    
    // Scroll to the book in the list
    const bookElement = document.querySelector(`[data-book-id="${book.id}"]`);
    if (bookElement) {
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
    }
  };

  // Handle book deletion
  const handleDeleteBook = (bookId: string) => {
    const updatedMatches = bookMatches.filter(book => book.id !== bookId);
    onBookListUpdated(updatedMatches);
  };

  // Handle OCR failure deletion
  const handleDeleteOCRFailure = (failureId: string) => {
    // This would update the OCR failures list
    console.log('Delete OCR failure:', failureId);
  };

  // Handle opening alternatives modal
  const handleShowAlternatives = (book: BookMatch) => {
    setSelectedBookForAlternatives(book);
    setShowAlternativesModal(true);
  };

  // Handle book switching
  const handleBookSwitched = (newBook: BookMatch) => {
    const updatedMatches = bookMatches.map(book => 
      book.id === newBook.id ? newBook : book
    );
    onBookListUpdated(updatedMatches);
    
    // Mark this book as modified
    setModifiedBooks(prev => new Set(prev).add(newBook.id));
    
    toast.success('Book switched successfully!');
  };

  // Get match type color
  const getMatchTypeColor = (matchType: string) => {
    switch (matchType) {
      case 'exact':
        return 'bg-green-900/50 text-green-300 border-green-700';
      case 'strong':
        return 'bg-blue-900/50 text-blue-300 border-blue-700';
      case 'moderate':
        return 'bg-yellow-900/50 text-yellow-300 border-yellow-700';
      case 'weak':
      case 'poor':
        return 'bg-red-900/50 text-red-300 border-red-700';
      default:
        return 'bg-slate-700 text-slate-300 border-slate-600';
    }
  };

  // Get match type label
  const getMatchTypeLabel = (matchType: string) => {
    switch (matchType) {
      case 'exact':
        return 'Perfect Match';
      case 'strong':
        return 'Strong Match';
      case 'moderate':
        return 'Moderate Match';
      case 'weak':
        return 'Weak Match';
      case 'poor':
        return 'Poor Match';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="space-y-4">
      {/* Book Matches */}
      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-white">
            Identified Books
          </h3>
          <span className="text-sm text-slate-300 bg-slate-700 px-2 py-1 rounded-full">
            {bookMatches.length}
          </span>
        </div>

        {bookMatches.length === 0 ? (
          <div className="text-center py-6 text-slate-400">
            <BookOpen className="w-10 h-10 mx-auto mb-2 text-slate-500" />
            <p>No books identified yet</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            <AnimatePresence>
              {bookMatches.map((book, index) => (
                <motion.div
                  key={book.id}
                  data-book-id={book.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2, delay: index * 0.05 }}
                  className={`
                    p-3 border rounded-lg cursor-pointer transition-all duration-200
                    ${selectedSpineId === book.spine_region_id
                      ? 'border-blue-400 bg-blue-900/30 ring-2 ring-blue-400/50'
                      : 'border-slate-500 hover:border-slate-400 hover:bg-slate-700/50'
                    }
                  `}
                  onClick={() => handleBookClick(book)}
                >
                  {/* Book Header - More Compact */}
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <h4 className="font-medium text-white truncate text-sm">
                          {book.title}
                        </h4>
                        {modifiedBooks.has(book.id) && (
                          <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs bg-green-900/50 text-green-300 border border-green-700">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Modified
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-300">
                        by {Array.isArray(book.author_name) ? book.author_name.join(', ') : book.author_name || 'Unknown Author'}
                      </p>
                    </div>
                    
                    {/* Match Type Badge */}
                    <span className={`text-xs px-2 py-1 rounded-full ml-2 border ${getMatchTypeColor(book.match_type)}`}>
                      {getMatchTypeLabel(book.match_type)}
                    </span>
                  </div>

                  {/* Book Details - More Compact */}
                  <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                    <div className="flex items-center space-x-3">
                      {book.first_publish_year && (
                        <span>{book.first_publish_year}</span>
                      )}
                      {book.publisher && (
                        <span className="truncate max-w-[100px]" title={book.publisher}>
                          {book.publisher}
                        </span>
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <span className="text-xs bg-slate-700 px-2 py-1 rounded text-slate-300">
                        {Math.round(book.match_score * 100)}%
                      </span>
                    </div>
                  </div>

                  {/* OCR Text - Now Visible */}
                  <div className="text-xs text-slate-400 bg-slate-800/50 p-2 rounded border border-slate-700 mb-2">
                    <span className="font-medium text-slate-300">OCR Text:</span> {book.ocr_text}
                  </div>

                  {/* Action Buttons - More Compact */}
                  <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-600">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleShowAlternatives(book);
                      }}
                      className="btn-secondary text-xs py-1 px-2 flex items-center space-x-1"
                    >
                      <RefreshCw className="w-3 h-3" />
                      <span>Possible Alternatives</span>
                    </button>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedBookForSearch(book);
                        setShowSearchModal(true);
                      }}
                      className="btn-secondary text-xs py-1 px-2 flex items-center space-x-1"
                    >
                      <Search className="w-3 h-3" />
                      <span>Search</span>
                    </button>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (onStartEditing) {
                          onStartEditing(book.id);
                        }
                      }}
                      className="btn-secondary text-xs py-1 px-2 flex items-center space-x-1"
                    >
                      <Edit3 className="w-3 h-3" />
                      <span>Edit OBB</span>
                    </button>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteBook(book.id);
                      }}
                      className="btn-danger text-xs py-1 px-2 flex items-center space-x-1"
                    >
                      <Trash2 className="w-3 h-3" />
                      <span>Delete</span>
                    </button>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>

      {/* OCR Failures */}
      {ocrFailures.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-white">
              OCR Failures
            </h3>
            <span className="text-sm text-yellow-300 bg-yellow-900/50 text-yellow-300 px-2 py-1 rounded-full border border-yellow-700">
              {ocrFailures.length}
            </span>
          </div>

          <div className="space-y-2 max-h-48 overflow-y-auto">
            <AnimatePresence>
              {ocrFailures.map((failure, index) => (
                <motion.div
                  key={failure.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2, delay: index * 0.05 }}
                  className="p-3 border border-yellow-700 rounded-lg bg-yellow-900/20"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <AlertTriangle className="w-4 h-4 text-yellow-400" />
                      <span className="font-medium text-yellow-300 text-sm">
                        {failure.error_type === 'no_text_detected' && 'No Text Detected'}
                        {failure.error_type === 'low_confidence' && 'Low Confidence'}
                        {failure.error_type === 'processing_error' && 'Processing Error'}
                      </span>
                    </div>
                    
                    <button
                      onClick={() => handleDeleteOCRFailure(failure.id)}
                      className="btn-danger text-xs py-1 px-2"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>

                  <p className="text-sm text-yellow-200 mb-2">
                    {failure.message}
                  </p>

                  <div className="flex items-center justify-between">
                    <button
                      onClick={() => {
                        setSelectedBookForSearch(null); // No specific book to replace
                        setShowSearchModal(true);
                      }}
                      className="btn-primary text-xs py-1 px-2 flex items-center space-x-1"
                    >
                      <Search className="w-3 h-3" />
                      <span>Search & Add</span>
                    </button>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-3">
          Quick Actions
        </h3>
        
        <div className="space-y-2">
          <button
            onClick={() => {
              setSelectedBookForSearch(null); // No specific book to replace
              setShowSearchModal(true);
            }}
            className="w-full btn-primary flex items-center justify-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Add Manual Entry</span>
          </button>
        </div>
      </div>

      {/* Manual Book Search Modal */}
      <ManualBookSearch
        isOpen={showSearchModal}
        onClose={() => {
          setShowSearchModal(false);
          setSelectedBookForSearch(null); // Clear selection when closing
        }}
        onBookSelected={(book) => {
          if (selectedBookForSearch) {
            // Replace the existing book
            const updatedMatches = bookMatches.map(existingBook => 
              existingBook.id === selectedBookForSearch.id 
                ? {
                    ...existingBook,
                    title: book.title,
                    author_name: Array.isArray(book.author_name) ? book.author_name : [book.author_name || 'Unknown Author'],
                    first_publish_year: book.first_publish_year,
                    publisher: book.publisher || '',
                    open_library_id: book.key,
                    match_score: 0.9, // High score for manually selected book
                    match_type: 'exact' as const
                  }
                : existingBook
            );
            
            onBookListUpdated(updatedMatches);
            toast.success(`Replaced "${selectedBookForSearch.title}" with "${book.title}"`);
          } else {
            // Add as a new book (for OCR failures or manual additions)
            const newBook: BookMatch = {
              id: `manual_${Date.now()}`, // Generate unique ID
              title: book.title,
              author_name: Array.isArray(book.author_name) ? book.author_name : [book.author_name || 'Unknown Author'],
              first_publish_year: book.first_publish_year,
              publisher: book.publisher || '',
              match_score: 0.9,
              match_type: 'exact',
              confidence: 0.9,
              ocr_text: 'Manually added',
              spine_region_id: `manual_${Date.now()}` // Generate unique spine ID
            };
            
            const updatedMatches = [...bookMatches, newBook];
            onBookListUpdated(updatedMatches);
            toast.success(`Added "${book.title}" to the list`);
          }
          
          setShowSearchModal(false);
          setSelectedBookForSearch(null);
        }}
      />

      {/* Alternatives Modal */}
      {showAlternativesModal && selectedBookForAlternatives && (
        <AlternativesModal
          isOpen={showAlternativesModal}
          onClose={() => setShowAlternativesModal(false)}
          currentBook={selectedBookForAlternatives}
          taskId={taskId}
          onBookSwitched={handleBookSwitched}
        />
      )}
    </div>
  );
};

export default BookListManager;


