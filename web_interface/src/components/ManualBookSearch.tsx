import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, BookOpen, Loader2, X, Filter, Bookmark } from 'lucide-react';
import { OpenLibraryBook } from '../types';
import { apiService } from '../services/api';

// Extended interface for search results that includes backend-added properties
interface SearchResultBook extends OpenLibraryBook {
  editions_count?: number;
  search_score?: number;
}

interface ManualBookSearchProps {
  isOpen: boolean;
  onClose: () => void;
  onBookSelected?: (book: SearchResultBook) => void;
}

interface SearchFilters {
  title: string;
  author: string;
  publisher: string;
}

const ManualBookSearch: React.FC<ManualBookSearchProps> = ({
  isOpen,
  onClose,
  onBookSelected
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResultBook[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchType, setSearchType] = useState<'basic' | 'advanced'>('basic');
  const [filters, setFilters] = useState<SearchFilters>({
    title: '',
    author: '',
    publisher: ''
  });
  const [showFilters, setShowFilters] = useState(false);

  const handleBasicSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    try {
      const results = await apiService.searchBooks(searchQuery, 20);
      setSearchResults(results as SearchResultBook[]);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleAdvancedSearch = async () => {
    if (!filters.title && !filters.author && !filters.publisher) return;
    
    setIsSearching(true);
    try {
      // Build query string for advanced search
      const queryParams = new URLSearchParams();
      if (filters.title) queryParams.append('title', filters.title);
      if (filters.author) queryParams.append('author', filters.author);
      if (filters.publisher) queryParams.append('publisher', filters.publisher);
      queryParams.append('limit', '20');
      
      const response = await fetch(`${apiService.getBaseUrl()}/api/search-books-advanced?${queryParams.toString()}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      if (data.success && Array.isArray(data.results)) {
        setSearchResults(data.results as SearchResultBook[]);
      } else {
        setSearchResults([]);
      }
    } catch (error) {
      console.error('Advanced search failed:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearch = () => {
    if (searchType === 'basic') {
      handleBasicSearch();
    } else {
      handleAdvancedSearch();
    }
  };

  const handleBookSelect = (book: SearchResultBook) => {
    if (onBookSelected) {
      onBookSelected(book);
    }
    onClose();
  };

  const clearSearch = () => {
    setSearchQuery('');
    setFilters({ title: '', author: '', publisher: '' });
    setSearchResults([]);
  };

  if (!isOpen) return null;

  return (
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
          <div className="flex items-center space-x-3">
            <BookOpen className="w-6 h-6 text-blue-400" />
            <div>
              <h2 className="text-2xl font-bold text-white">Manual Book Search</h2>
              <p className="text-slate-400 text-sm">Search Open Library database for books</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-700 rounded-lg transition-colors duration-200"
          >
            <X className="w-6 h-6 text-slate-400" />
          </button>
        </div>

        {/* Search Type Toggle */}
        <div className="px-6 pt-4">
          <div className="flex space-x-2 mb-4">
            <button
              onClick={() => setSearchType('basic')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                searchType === 'basic'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              Basic Search
            </button>
            <button
              onClick={() => setSearchType('advanced')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                searchType === 'advanced'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              Advanced Search
            </button>
          </div>
        </div>

        {/* Search Interface */}
        <div className="px-6 pb-4">
          {searchType === 'basic' ? (
            /* Basic Search */
            <div className="flex space-x-3">
              <input
                type="text"
                placeholder="Search for books by title, author, or keywords..."
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
          ) : (
            /* Advanced Search */
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <input
                  type="text"
                  placeholder="Title..."
                  value={filters.title}
                  onChange={(e) => setFilters({ ...filters, title: e.target.value })}
                  className="input-field"
                />
                <input
                  type="text"
                  placeholder="Author..."
                  value={filters.author}
                  onChange={(e) => setFilters({ ...filters, author: e.target.value })}
                  className="input-field"
                />
                <input
                  type="text"
                  placeholder="Publisher..."
                  value={filters.publisher}
                  onChange={(e) => setFilters({ ...filters, publisher: e.target.value })}
                  className="input-field"
                />
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={handleSearch}
                  disabled={isSearching || (!filters.title && !filters.author && !filters.publisher)}
                  className="btn-primary px-6 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSearching ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Search className="w-4 h-4" />
                  )}
                  <span className="ml-2">Search</span>
                </button>
                <button
                  onClick={clearSearch}
                  className="btn-secondary px-4"
                >
                  Clear
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Search Results */}
        <div className="flex-1 overflow-y-auto custom-scrollbar px-6 pb-6">
          {isSearching ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
              <span className="ml-3 text-slate-400">Searching...</span>
            </div>
          ) : searchResults.length > 0 ? (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">
                  Search Results ({searchResults.length})
                </h3>
                <button
                  onClick={clearSearch}
                  className="text-sm text-slate-400 hover:text-white transition-colors"
                >
                  Clear Results
                </button>
              </div>
              
              <div className="space-y-3">
                {searchResults.map((book, index) => (
                  <motion.div
                    key={book.key}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
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
                      <Bookmark className="w-4 h-4 text-slate-400" />
                    </div>

                    <div className="flex items-center justify-between text-xs text-slate-400 mb-3">
                      <div className="flex items-center space-x-3">
                        {book.first_publish_year && (
                          <span>{book.first_publish_year}</span>
                        )}
                        {book.publisher && (
                          <span className="truncate max-w-[150px]" title={book.publisher}>
                            {book.publisher}
                          </span>
                        )}
                      </div>
                      {book.editions_count && (
                        <span className="text-xs bg-slate-600 px-2 py-1 rounded">
                          {book.editions_count} edition{book.editions_count !== 1 ? 's' : ''}
                        </span>
                      )}
                    </div>

                    <button
                      onClick={() => handleBookSelect(book)}
                      className="w-full btn-primary text-sm py-2 flex items-center justify-center space-x-2"
                    >
                      <BookOpen className="w-4 h-4" />
                      <span>Select This Book</span>
                    </button>
                  </motion.div>
                ))}
              </div>
            </div>
          ) : searchQuery || Object.values(filters).some(v => v) ? (
            <div className="text-center py-12 text-slate-400">
              <BookOpen className="w-16 h-16 mx-auto mb-4 text-slate-500" />
              <p className="text-lg">No books found</p>
              <p className="text-sm text-slate-500 mt-2">Try adjusting your search terms</p>
            </div>
          ) : (
            <div className="text-center py-12 text-slate-400">
              <Search className="w-16 h-16 mx-auto mb-4 text-slate-500" />
              <p className="text-lg">Ready to search</p>
              <p className="text-sm text-slate-500 mt-2">Enter search terms above to find books</p>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};

export default ManualBookSearch;
