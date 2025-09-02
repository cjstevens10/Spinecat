import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { FileSpreadsheet, CheckCircle } from 'lucide-react';
import * as XLSX from 'xlsx';

import { ProcessingResult } from '../types';

interface FinalizePanelProps {
  processingResult: ProcessingResult;
  onUnfinalize: () => void;
}

const FinalizePanel: React.FC<FinalizePanelProps> = ({
  processingResult,
  onUnfinalize
}) => {
  const [includeMetadata, setIncludeMetadata] = useState(true);
  const [includeOCRText, setIncludeOCRText] = useState(false);
  const [includeConfidenceScores, setIncludeConfidenceScores] = useState(true);
  const [isExporting, setIsExporting] = useState(false);

  // Calculate summary statistics from actual book matches
  const totalSpines = processingResult.spine_regions.length;
  const successfulMatches = processingResult.book_matches.length;
  
  // Count different types of matches
  const perfectMatches = processingResult.book_matches.filter(book => 
    book.match_type === 'exact' && book.match_score >= 0.9
  ).length;
  
  const strongMatches = processingResult.book_matches.filter(book => 
    book.match_type === 'strong' && book.match_score >= 0.8
  ).length;
  
  const moderateMatches = processingResult.book_matches.filter(book => 
    book.match_type === 'moderate' && book.match_score >= 0.6
  ).length;
  
  const manualEntries = processingResult.book_matches.filter(book => 
    book.ocr_text === 'Manually added' || book.ocr_text === 'Manually drawn spine'
  ).length;
  
  const successRate = totalSpines > 0 ? (successfulMatches / totalSpines) * 100 : 0;
  const perfectRate = successfulMatches > 0 ? (perfectMatches / successfulMatches) * 100 : 0;

  // Handle Excel export
  const handleExport = async () => {
    setIsExporting(true);
    
    try {
      // Prepare data for Excel export
      const exportData = processingResult.book_matches.map((book, index) => {
        const row: any = {
          'Spine #': index + 1,
          'Title': book.title || 'Unknown Title',
          'Author(s)': Array.isArray(book.author_name) ? book.author_name.join(', ') : book.author_name || 'Unknown Author',
          'Publication Year': book.first_publish_year || 'Unknown',
          'Match Type': book.match_type || 'Unknown',
          'Open Library ID': book.open_library_id || 'N/A'
        };

        // Add optional fields based on user preferences
        if (includeOCRText) {
          row['OCR Text'] = book.ocr_text || 'N/A';
        }
        
        if (includeConfidenceScores) {
          row['Confidence'] = book.confidence ? `${Math.round(book.confidence * 100)}%` : 'N/A';
        }

        return row;
      });

      // Add metadata row if requested
      if (includeMetadata) {
        const metadataRow = {
          'Spine #': 'METADATA',
          'Title': `Processing completed on ${new Date().toLocaleString()}`,
          'Author(s)': `Total spines: ${totalSpines}`,
          'Publication Year': `Successful matches: ${successfulMatches}`,
          'Match Type': `Success rate: ${successRate.toFixed(1)}%`,
          'Open Library ID': `Processing time: ${processingResult.processing_time.toFixed(1)}s`
        };
        exportData.unshift(metadataRow);
      }

      // Create workbook and worksheet
      const workbook = XLSX.utils.book_new();
      const worksheet = XLSX.utils.json_to_sheet(exportData);

      // Set column widths for better readability
      const columnWidths = [
        { wch: 8 },   // Spine #
        { wch: 30 },  // Title
        { wch: 25 },  // Author(s)
        { wch: 15 },  // Publication Year
        { wch: 12 },  // Match Type
        { wch: 20 }   // Open Library ID
      ];

      // Add OCR Text and Confidence columns if included
      if (includeOCRText) {
        columnWidths.push({ wch: 25 }); // OCR Text
      }
      if (includeConfidenceScores) {
        columnWidths.push({ wch: 12 }); // Confidence
      }

      worksheet['!cols'] = columnWidths;

      // Add worksheet to workbook
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Book List');

      // Generate filename with timestamp
      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
      const filename = `spinecat-books-${timestamp}.xlsx`;

      // Write and download the file
      XLSX.writeFile(workbook, filename);
      
      console.log('Excel export completed:', filename);
      
    } catch (error) {
      console.error('Excel export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="card"
    >
      {/* Header */}
      <div className="mb-6">
        <div>
          <h3 className="text-xl font-semibold text-gray-300">
            Finalize & Export
          </h3>
          <p className="text-gray-300 mt-1">
            Review your results and export the book list to Excel
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Summary & Export Options */}
        <div className="space-y-6">
          {/* Summary Statistics */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-700 mb-3">Processing Summary</h4>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {totalSpines}
                </div>
                <div className="text-sm text-gray-900 font-medium">Total Spines</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {successfulMatches}
                </div>
                <div className="text-sm text-gray-900 font-medium">Successful Matches</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {successRate.toFixed(1)}%
                </div>
                <div className="text-sm text-gray-900 font-medium">Success Rate</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {perfectRate.toFixed(1)}%
                </div>
                <div className="text-sm text-gray-900 font-medium">Perfect Matches</div>
              </div>
            </div>
            
            {/* Detailed Match Breakdown */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <h5 className="text-sm font-medium text-gray-700 mb-3">Match Breakdown</h5>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-900 font-medium">Perfect (90%+):</span>
                  <span className="font-bold text-gray-900">{perfectMatches}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-900 font-medium">Strong (80%+):</span>
                  <span className="font-bold text-gray-900">{strongMatches}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-900 font-medium">Moderate (60%+):</span>
                  <span className="font-bold text-gray-900">{moderateMatches}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-900 font-medium">Manual Entries:</span>
                  <span className="font-bold text-gray-900">{manualEntries}</span>
                </div>
              </div>
            </div>
            
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-900 font-medium">Processing Time:</span>
                <span className="font-bold text-gray-900">{processingResult.processing_time.toFixed(1)}s</span>
              </div>
            </div>
          </div>

                      {/* Current Book Status */}
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <h4 className="font-medium text-blue-800 mb-3">Current Book Status</h4>
              <div className="space-y-2 text-sm">
                {processingResult.book_matches.map((book, index) => (
                  <div key={book.id} className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-blue-700 truncate">{book.title}</div>
                      <div className="text-blue-600 text-xs truncate">
                        {Array.isArray(book.author_name) ? book.author_name.join(', ') : book.author_name}
                      </div>
                    </div>
                    <div className="ml-3 text-right">
                      {book.ocr_text === 'Manually added' || book.ocr_text === 'Manually drawn spine' ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                          Manual Entry
                        </span>
                      ) : (
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          book.match_score >= 0.9 ? 'bg-green-100 text-green-800' :
                          book.match_score >= 0.8 ? 'bg-blue-100 text-blue-800' :
                          book.match_score >= 0.6 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {Math.round(book.match_score * 100)}%
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Export Options */}
            <div className="space-y-4">
              <h4 className="font-medium text-gray-300">Excel Export Options</h4>
            
            {/* Excel Format Info */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center space-x-3">
                <FileSpreadsheet className="w-6 h-6 text-green-600" />
                <div>
                  <h5 className="font-medium text-green-800">Excel Export Ready</h5>
                  <p className="text-sm text-green-700">
                    Your book list will be exported as a professional Excel spreadsheet with all book details.
                  </p>
                </div>
              </div>
            </div>

            {/* Metadata Options */}
            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={includeMetadata}
                  onChange={(e) => setIncludeMetadata(e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-300">
                  Include metadata (processing time, confidence scores, etc.)
                </span>
              </label>
              
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={includeOCRText}
                  onChange={(e) => setIncludeOCRText(e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-300">
                  Include original OCR text readings
                </span>
              </label>
              
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={includeConfidenceScores}
                  onChange={(e) => setIncludeConfidenceScores(e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-300">
                  Include confidence scores for each detection
                </span>
              </label>
            </div>

            {/* Export Button */}
            <button
              onClick={handleExport}
              disabled={isExporting}
              className="w-full btn-primary flex items-center justify-center space-x-2 py-3"
            >
              {isExporting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Generating Excel...</span>
                </>
              ) : (
                <>
                  <FileSpreadsheet className="w-4 h-4" />
                  <span>Export Excel</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right: Excel Preview */}
        <div className="space-y-4">
          <h4 className="font-medium text-gray-300">Excel Export Preview</h4>
          
          <div className="bg-gray-50 rounded-lg p-4 min-h-[300px]">
            <div className="text-center mb-4">
              <FileSpreadsheet className="w-8 h-8 mx-auto mb-2 text-gray-400" />
              <p className="text-sm font-medium text-gray-600">Excel Preview</p>
            </div>
            
            {/* Sample Excel Data Preview */}
            <div className="bg-white rounded border overflow-hidden">
              <div className="bg-gray-100 px-3 py-2 border-b">
                <div className="grid grid-cols-6 gap-2 text-xs font-medium text-gray-700">
                  <div>Spine #</div>
                  <div>Title</div>
                  <div>Author(s)</div>
                  <div>Year</div>
                  <div>Type</div>
                  <div>ID</div>
                </div>
              </div>
              
              <div className="max-h-48 overflow-y-auto">
                {processingResult.book_matches.slice(0, 5).map((book, index) => (
                  <div key={book.id} className="grid grid-cols-6 gap-2 px-3 py-2 border-b border-gray-100 text-xs">
                    <div className="text-gray-600 font-medium">{index + 1}</div>
                    <div className="text-gray-800 truncate" title={book.title}>
                      {book.title || 'Unknown Title'}
                    </div>
                    <div className="text-gray-700 truncate" title={Array.isArray(book.author_name) ? book.author_name.join(', ') : book.author_name}>
                      {Array.isArray(book.author_name) ? book.author_name.join(', ') : book.author_name || 'Unknown'}
                    </div>
                    <div className="text-gray-600">{book.first_publish_year || 'N/A'}</div>
                    <div className="text-gray-600">{book.match_type || 'N/A'}</div>
                    <div className="text-gray-500 truncate" title={book.open_library_id}>
                      {book.open_library_id ? book.open_library_id.slice(-8) : 'N/A'}
                    </div>
                  </div>
                ))}
                
                {processingResult.book_matches.length > 5 && (
                  <div className="px-3 py-2 text-xs text-gray-500 text-center">
                    ... and {processingResult.book_matches.length - 5} more books
                  </div>
                )}
                
                {processingResult.book_matches.length === 0 && (
                  <div className="px-3 py-4 text-xs text-gray-500 text-center">
                    No books to export
                  </div>
                )}
              </div>
            </div>
            
            <div className="mt-3 text-xs text-gray-500">
              {includeMetadata && <div>• Includes processing metadata</div>}
              {includeOCRText && <div>• Includes OCR text column</div>}
              {includeConfidenceScores && <div>• Includes confidence scores</div>}
            </div>
          </div>

          {/* Export Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <CheckCircle className="w-5 h-5 text-blue-600 mt-0.5" />
              <div className="text-sm text-blue-800">
                <p className="font-medium mb-1">Excel Export Ready</p>
                <p>
                  Your image has been processed with {successfulMatches} book{successfulMatches !== 1 ? 's' : ''} identified 
                  ({successRate.toFixed(1)}% success rate). The Excel file will contain all book details in a professional spreadsheet format.
                </p>
                {manualEntries > 0 && (
                  <p className="mt-2 text-blue-700">
                    Includes {manualEntries} manual entr{manualEntries !== 1 ? 'ies' : 'y'} that you've added or drawn.
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default FinalizePanel;




