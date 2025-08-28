import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, BookOpen, CheckCircle, Search, Loader2 } from 'lucide-react';

import { BookMatch, OpenLibraryBook } from '../types';
import { apiService } from '../services/api';

interface AlternativesModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentBook: BookMatch;
  onBookSwitched: (newBook: BookMatch) => void;
  onScrollToBook?: (bookTitle: string) => void;
}

interface AlternativeMatch {
  book: OpenLibraryBook;
  match_score: number;
  match_type: 'exact' | 'strong' | 'moderate' | 'weak' | 'poor';
}

const AlternativesModal: React.FC<AlternativesModalProps> = ({
  isOpen,
  onClose,
  currentBook,
  onBookSwitched,
  onScrollToBook
}) => {
  const [alternatives, setAlternatives] = useState<AlternativeMatch[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<OpenLibraryBook[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const alternativesRef = useRef<HTMLDivElement>(null);

  // Calculate match score between two book titles (for search results only)
  const calculateMatchScore = (searchTitle: string, bookTitle: string): { score: number; type: 'exact' | 'strong' | 'moderate' | 'weak' | 'poor' } => {
    const search = searchTitle.toLowerCase().trim();
    const book = bookTitle.toLowerCase().trim();
    
    // Exact match
    if (search === book) {
      return { score: 1.0, type: 'exact' };
    }
    
    // Contains match
    if (search.includes(book) || book.includes(search)) {
      const overlap = Math.min(search.length, book.length) / Math.max(search.length, book.length);
      if (overlap > 0.8) return { score: 0.9, type: 'strong' };
      if (overlap > 0.6) return { score: 0.8, type: 'strong' };
      if (overlap > 0.4) return { score: 0.7, type: 'moderate' };
      return { score: 0.6, type: 'moderate' };
    }
    
    // Word-based matching
    const searchWords = search.split(/\s+/).filter(w => w.length > 2);
    const bookWords = book.split(/\s+/).filter(w => w.length > 2);
    
    if (searchWords.length === 0 || bookWords.length === 0) {
      return { score: 0.3, type: 'weak' };
    }
    
    const commonWords = searchWords.filter(word => bookWords.includes(word));
    const wordScore = commonWords.length / Math.max(searchWords.length, bookWords.length);
    
    if (wordScore > 0.7) return { score: 0.8, type: 'strong' };
    if (wordScore > 0.5) return { score: 0.7, type: 'moderate' };
    if (wordScore > 0.3) return { score: 0.6, type: 'moderate' };
    if (wordScore > 0.1) return { score: 0.4, type: 'weak' };
    
    return { score: 0.2, type: 'poor' };
  };

  // Load alternatives when modal opens
  useEffect(() => {
    if (isOpen && currentBook) {
      const loadAlternatives = async () => {
        setIsLoading(true);
        try {
          // Use the actual backend pipeline to get alternatives with real scores
          // This ensures we get the same scoring and matching logic as the initial processing
          const response = await fetch(`${apiService.getBaseUrl()}/api/alternatives?ocr_text=${encodeURIComponent(currentBook.ocr_text)}&limit=10`);
          
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          
          const data = await response.json();
          console.log('🔍 Raw response from alternatives API:', data);
          
          if (!data.success || !Array.isArray(data.results)) {
            console.warn('Alternatives API returned invalid data:', data);
            console.warn('data.success:', data.success);
            console.warn('data.results type:', typeof data.results);
            console.warn('data.results is array:', Array.isArray(data.results));
            setAlternatives([]);
            return;
          }
          
          console.log('🔍 Data validation passed, processing', data.results.length, 'results');
          
          // Convert backend results to alternative matches with REAL scores
          const alternativesList: AlternativeMatch[] = data.results
            .map((book: any, index: number) => {
              console.log(`🔍 Processing book ${index}:`, book);
              
              // Ensure book has required properties
              if (!book || typeof book.title !== 'string') {
                console.warn('Invalid book data:', book);
                return null;
              }
              
              // Use the ACTUAL backend scores - no fake calculations!
              const alternative: AlternativeMatch = {
                book: {
                  key: book.key,
                  title: book.title,
                  author_name: book.author_name,
                  first_publish_year: book.first_publish_year,
                  publisher: book.publisher
                },
                match_score: book.match_score, // REAL score from backend
                match_type: book.match_type    // REAL type from backend
              };
              
              console.log(`🔍 Created alternative ${index}:`, alternative);
              return alternative;
            })
            .filter((item: any): item is AlternativeMatch => {
              if (item === null) return false;
              
              // Only remove exact duplicates, keep everything else
              const currentTitle = currentBook.title.toLowerCase();
              const alternativeTitle = item.book.title.toLowerCase();
              
              if (currentTitle === alternativeTitle) {
                console.log(`🔍 Filtering out exact duplicate: ${alternativeTitle}`);
                return false;
              }
              
              console.log(`🔍 Keeping alternative: ${alternativeTitle}`);
              return true;
            });
          
          // Sort by match score (highest first) - using REAL scores
          alternativesList.sort((a, b) => b.match_score - a.match_score);
          
          console.log('Loaded alternatives with REAL backend scores:', alternativesList);
          setAlternatives(alternativesList);
        } catch (error) {
          console.error('Failed to load alternatives:', error);
          setAlternatives([]);
        } finally {
          setIsLoading(false);
        }
      };
      
      loadAlternatives();
    }
  }, [isOpen, currentBook]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    try {
      const results = await apiService.searchBooks(searchQuery, 10);
      
      // Ensure results is an array
      if (Array.isArray(results)) {
        // Calculate match scores for search results
        const scoredResults = results.map((book: OpenLibraryBook) => {
          const matchResult = calculateMatchScore(searchQuery, book.title);
          
          // Use realistic score range for search results too
          const realisticScore = Math.min(0.95, Math.max(0.6, matchResult.score));
          
          return {
            ...book,
            _matchScore: realisticScore,
            _matchType: matchResult.type
          };
        })
        .filter(book => {
          // Filter out books that are too similar to the current book
          return !currentBook.title.toLowerCase().includes(book.title.toLowerCase()) &&
                 !book.title.toLowerCase().includes(currentBook.title.toLowerCase());
        });
        
        // Sort by match score (highest first)
        scoredResults.sort((a: any, b: any) => b._matchScore - a._matchScore);
        setSearchResults(scoredResults);
      } else {
        console.warn('Search results is not an array:', results);
        setSearchResults([]);
      }
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSwitchBook = (alternative: AlternativeMatch) => {
    // Create a new BookMatch with the alternative book data
    const newBook: BookMatch = {
      ...currentBook,
      title: alternative.book.title,
      author_name: Array.isArray(alternative.book.author_name) ? alternative.book.author_name : [alternative.book.author_name || 'Unknown Author'],
      first_publish_year: alternative.book.first_publish_year,
      publisher: alternative.book.publisher || '',
      match_score: alternative.match_score,
      match_type: alternative.match_type,
      open_library_id: alternative.book.key,
      // Preserve the original OCR text to maintain context
      ocr_text: currentBook.ocr_text
    };
    
    console.log('Switching to book:', alternative.book.title, 'with score:', alternative.match_score);
    onBookSwitched(newBook);
    onClose();
  };

  // Scroll to a specific book in the alternatives list
  const scrollToBook = (bookTitle: string) => {
    if (!alternativesRef.current) return;
    
    const alternativesContainer = alternativesRef.current;
    const bookElements = alternativesContainer.querySelectorAll('[data-book-title]');
    
    Array.from(bookElements).forEach((element) => {
      if (element instanceof HTMLElement && element.dataset.bookTitle === bookTitle) {
        element.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'center',
          inline: 'nearest'
        });
        // Add highlight effect
        element.classList.add('ring-2', 'ring-blue-400', 'ring-opacity-75');
        setTimeout(() => {
          element.classList.remove('ring-2', 'ring-blue-400', 'ring-opacity-75');
        }, 2000);
      }
    });
    
    // Notify parent component
    if (onScrollToBook) {
      onScrollToBook(bookTitle);
    }
  };

  // Auto-scroll to current book when alternatives load
  useEffect(() => {
    if (alternatives.length > 0 && currentBook) {
      // Small delay to ensure DOM is rendered
      setTimeout(() => {
        scrollToBook(currentBook.title);
      }, 100);
    }
  }, [alternatives, currentBook]);

  // Expose scroll function to parent component
  const scrollToBookByTitle = (bookTitle: string) => {
    scrollToBook(bookTitle);
  };

  // Make function available globally for parent component access
  useEffect(() => {
    (window as any).scrollToBookInAlternativesModal = scrollToBookByTitle;
    return () => {
      delete (window as any).scrollToBookInAlternativesModal;
    };
  }, []);

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

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-slate-800 rounded-2xl shadow-xl border border-slate-600 max-w-4xl w-full max-h-[90vh] flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-slate-600">
            <div>
              <h2 className="text-2xl font-bold text-white">Possible Alternatives</h2>
              <p className="text-slate-400 mt-1">
                Current: <span className="text-white font-medium">{currentBook.title}</span>
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-slate-700 rounded-lg transition-colors duration-200"
            >
              <X className="w-6 h-6 text-slate-400" />
            </button>
          </div>

          {/* Search Bar */}
          <div className="p-6 border-b border-slate-600">
            <div className="flex space-x-3">
              <input
                type="text"
                placeholder="Search for other books..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1 input-field"
              />
              <button
                onClick={handleSearch}
                disabled={isSearching || !searchQuery.trim()}
                className="btn-primary px-6 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSearching ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Search className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
                <span className="ml-3 text-slate-400">Loading alternatives...</span>
              </div>
            ) : (
              <div className="h-full flex flex-col">
                {/* Current Book - Fixed at top */}
                <div className="p-6 pb-4">
                  <div className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
                    <div className="flex items-center space-x-3 mb-3">
                      <BookOpen className="w-5 h-5 text-blue-400" />
                      <h3 className="text-lg font-semibold text-white">Current Selection</h3>
                    </div>
                    <div className="bg-slate-800 rounded-lg p-4">
                      <h4 className="font-medium text-white mb-2">{currentBook.title}</h4>
                      <p className="text-slate-300 text-sm mb-2">
                        by {Array.isArray(currentBook.author_name) ? currentBook.author_name.join(', ') : currentBook.author_name || 'Unknown Author'}
                      </p>
                      {currentBook.first_publish_year && (
                        <p className="text-slate-400 text-sm">{currentBook.first_publish_year}</p>
                      )}
                      <div className="mt-3 flex items-center space-x-2">
                        <span className="text-xs bg-blue-900/50 text-blue-300 px-2 py-1 rounded border border-blue-700">
                          Current Match
                        </span>
                        <span className="text-xs bg-slate-700 text-slate-300 px-2 py-1 rounded">
                          {Math.round(currentBook.match_score * 100)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Alternatives Section */}
                <div 
                  ref={alternativesRef} 
                  className="px-6 pb-6"
                >
                  <div className="space-y-4">
                    {/* Alternatives */}
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-4 sticky top-0 bg-slate-900 py-2 z-10">
                        Alternative Matches ({alternatives.length})
                      </h3>
                      <p className="text-xs text-slate-400 mb-4">
                        Using actual backend pipeline scores. Percentages show real match confidence from the matching algorithm.
                      </p>
                      
                      {alternatives.length === 0 ? (
                        <div className="text-center py-8 text-slate-400">
                          <BookOpen className="w-12 h-12 mx-auto mb-3 text-slate-500" />
                          <p>No alternatives found</p>
                          <p className="text-sm text-slate-500 mt-1">Try searching for a different book</p>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          {alternatives.map((alternative, index) => (
                            <motion.div
                              key={alternative.book.key}
                              data-book-title={alternative.book.title}
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ delay: index * 0.1 }}
                              className="bg-slate-700/50 rounded-lg p-4 border border-slate-600 hover:border-slate-500 transition-colors duration-200"
                            >
                              <div className="flex items-start justify-between mb-3">
                                <div className="flex-1 min-w-0">
                                  <h4 className="font-medium text-white text-sm mb-1 truncate">
                                    {alternative.book.title}
                                  </h4>
                                  <p className="text-xs text-slate-300">
                                    by {Array.isArray(alternative.book.author_name) ? alternative.book.author_name.join(', ') : alternative.book.author_name || 'Unknown Author'}
                                  </p>
                                </div>
                                <span className={`text-xs px-2 py-1 rounded-full ml-2 border ${getMatchTypeColor(alternative.match_type)}`}>
                                  {getMatchTypeLabel(alternative.match_type)}
                                </span>
                              </div>

                              <div className="flex items-center justify-between text-xs text-slate-400 mb-3">
                                <div className="flex items-center space-x-3">
                                  {alternative.book.first_publish_year && (
                                    <span>{alternative.book.first_publish_year}</span>
                                  )}
                                  {alternative.book.publisher && (
                                    <span className="truncate max-w-[100px]" title={alternative.book.publisher}>
                                      {alternative.book.publisher}
                                    </span>
                                  )}
                                </div>
                                <span className="text-xs bg-slate-700 px-2 py-1 rounded text-slate-300">
                                  {Math.round(alternative.match_score * 100)}%
                                </span>
                              </div>

                              <button
                                onClick={() => handleSwitchBook(alternative)}
                                className="w-full btn-primary text-sm py-2 flex items-center justify-center space-x-2"
                              >
                                <CheckCircle className="w-4 h-4" />
                                <span>Switch to This Book</span>
                              </button>
                            </motion.div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Search Results */}
                    {searchResults.length > 0 && (
                      <div className="mt-8">
                        <h3 className="text-lg font-semibold text-white mb-4 sticky top-0 bg-slate-900 py-2 z-10">
                          Search Results ({searchResults.length})
                        </h3>
                        <p className="text-xs text-slate-400 mb-4">
                          Manual search results. Percentages show calculated similarity to search query.
                        </p>
                        <div className="space-y-3">
                          {searchResults.map((book, index) => (
                            <motion.div
                              key={book.key}
                              data-book-title={book.title}
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ delay: index * 0.1 }}
                              className="bg-slate-700/50 rounded-lg p-4 border border-slate-600 hover:border-slate-500 transition-colors duration-200"
                            >
                              <div className="flex items-start justify-between mb-3">
                                <div className="flex-1 min-w-0">
                                  <h4 className="font-medium text-white text-sm mb-1 truncate">
                                    {book.title}
                                  </h4>
                                  <p className="text-xs text-slate-300">
                                    by {Array.isArray(book.author_name) ? book.author_name.join(', ') : book.author_name || 'Unknown Author'}
                                  </p>
                                </div>
                                <span className={`text-xs px-2 py-1 rounded-full ml-2 border ${getMatchTypeColor((book as any)._matchType || 'moderate')}`}>
                                  {getMatchTypeLabel((book as any)._matchType || 'moderate')}
                                </span>
                              </div>

                              <div className="flex items-center justify-between text-xs text-slate-400 mb-3">
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
                                <span className="text-xs bg-slate-700 px-2 py-1 rounded text-slate-300">
                                  {Math.round((book as any)._matchScore * 100)}%
                                </span>
                              </div>

                              <button
                                onClick={() => handleSwitchBook({
                                  book,
                                  match_score: (book as any)._matchScore || 0.6,
                                  match_type: (book as any)._matchType || 'moderate'
                                })}
                                className="w-full btn-secondary text-sm py-2 flex items-center justify-center space-x-2"
                              >
                                <CheckCircle className="w-4 h-4" />
                                <span>Switch to This Book</span>
                              </button>
                            </motion.div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default AlternativesModal;
