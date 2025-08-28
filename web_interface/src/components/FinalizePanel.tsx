import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Download, FileText, Image as ImageIcon, RotateCcw, CheckCircle } from 'lucide-react';

import { ProcessingResult } from '../types';

interface FinalizePanelProps {
  processingResult: ProcessingResult;
  onUnfinalize: () => void;
}

const FinalizePanel: React.FC<FinalizePanelProps> = ({
  processingResult,
  onUnfinalize
}) => {
  const [exportFormat, setExportFormat] = useState<'png' | 'jpg' | 'pdf'>('png');
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

  // Handle export
  const handleExport = async () => {
    setIsExporting(true);
    
    try {
      // TODO: Implement actual export functionality
      await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate export
      
      // For now, just show success message
      console.log('Export completed:', {
        format: exportFormat,
        includeMetadata,
        includeOCRText,
        includeConfidenceScores
      });
      
    } catch (error) {
      console.error('Export failed:', error);
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
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-semibold text-gray-500">
            Finalize & Export
          </h3>
          <p className="text-gray-400 mt-1">
            Review your results and generate the final labeled image
          </p>
        </div>
        
        <button
          onClick={onUnfinalize}
          className="btn-secondary flex items-center space-x-2"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Continue Editing</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Summary & Export Options */}
        <div className="space-y-6">
          {/* Summary Statistics */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-500 mb-3">Processing Summary</h4>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-primary-600">
                  {totalSpines}
                </div>
                <div className="text-sm text-gray-400">Total Spines</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-success-600">
                  {successfulMatches}
                </div>
                <div className="text-sm text-gray-400">Successful Matches</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-primary-600">
                  {successRate.toFixed(1)}%
                </div>
                <div className="text-sm text-gray-400">Success Rate</div>
              </div>
              
              <div className="text-center">
                <div className="text-2xl font-bold text-success-600">
                  {perfectRate.toFixed(1)}%
                </div>
                <div className="text-sm text-gray-400">Perfect Matches</div>
              </div>
            </div>
            
            {/* Detailed Match Breakdown */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <h5 className="text-sm font-medium text-gray-500 mb-3">Match Breakdown</h5>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-400">Perfect (90%+):</span>
                  <span className="font-medium text-gray-500">{perfectMatches}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Strong (80%+):</span>
                  <span className="font-medium text-gray-500">{strongMatches}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Moderate (60%+):</span>
                  <span className="font-medium text-gray-500">{moderateMatches}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Manual Entries:</span>
                  <span className="font-medium text-gray-500">{manualEntries}</span>
                </div>
              </div>
            </div>
            
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Processing Time:</span>
                <span className="font-medium text-gray-500">{processingResult.processing_time.toFixed(1)}s</span>
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
              <h4 className="font-medium text-gray-500">Export Options</h4>
            
            {/* Format Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-2">
                Export Format
              </label>
              <div className="grid grid-cols-3 gap-2">
                {(['png', 'jpg', 'pdf'] as const).map((format) => (
                  <button
                    key={format}
                    onClick={() => setExportFormat(format)}
                    className={`
                      p-3 border rounded-lg text-center transition-colors duration-200
                      ${exportFormat === format
                        ? 'border-primary-500 bg-primary-50 text-primary-700'
                        : 'border-gray-300 hover:border-gray-400'
                      }
                    `}
                  >
                    <div className="flex flex-col items-center space-y-1">
                      {format === 'png' && <ImageIcon className="w-5 h-5" />}
                      {format === 'jpg' && <ImageIcon className="w-5 h-5" />}
                      {format === 'pdf' && <FileText className="w-5 h-5" />}
                      <span className="text-sm font-medium uppercase">{format}</span>
                    </div>
                  </button>
                ))}
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
                <span className="ml-2 text-sm text-gray-400">
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
                <span className="ml-2 text-sm text-gray-400">
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
                <span className="ml-2 text-sm text-gray-400">
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
                  <span>Exporting...</span>
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  <span>Export {exportFormat.toUpperCase()}</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right: Preview */}
        <div className="space-y-4">
          <h4 className="font-medium text-gray-500">Final Image Preview</h4>
          
          <div className="bg-gray-100 rounded-lg p-4 min-h-[300px] flex items-center justify-center">
            <div className="text-center text-gray-400">
              <ImageIcon className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <p className="text-lg font-medium mb-2">Preview Coming Soon</p>
              <p className="text-sm">
                The final labeled image will appear here with:
              </p>
              <ul className="text-xs text-gray-400 mt-2 space-y-1">
                <li>• Numbered spine regions</li>
                <li>• Book titles and authors</li>
                <li>• Confidence indicators</li>
                <li>• Professional labeling</li>
              </ul>
            </div>
          </div>

          {/* Export Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <CheckCircle className="w-5 h-5 text-blue-600 mt-0.5" />
              <div className="text-sm text-blue-800">
                <p className="font-medium mb-1">Export Ready</p>
                <p>
                  Your image has been processed with {successfulMatches} book{successfulMatches !== 1 ? 's' : ''} identified 
                  ({successRate.toFixed(1)}% success rate). The final image will include numbered spine regions with 
                  corresponding book information below.
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




