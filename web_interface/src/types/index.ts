// Core data types for the Spinecat web interface

export interface SpineRegion {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  rotation: number;
  confidence: number;
  coordinates: [number, number][]; // Polygon coordinates
}

export interface BookMatch {
  id: string;
  title: string;
  author_name: string[];
  first_publish_year: number | null;
  publisher?: string;
  match_score: number;
  match_type: 'exact' | 'strong' | 'moderate' | 'weak' | 'poor';
  confidence: number;
  ocr_text: string;
  spine_region_id: string;
  open_library_id?: string;
}

export interface OCRFailure {
  id: string;
  spine_region_id: string;
  coordinates: [number, number][];
  error_type: 'no_text_detected' | 'low_confidence' | 'processing_error';
  message: string;
}

export interface ProcessingResult {
  image_url: string;
  spine_regions: SpineRegion[];
  book_matches: BookMatch[];
  ocr_failures: OCRFailure[];
  processing_time: number;
  total_spines: number;
  successful_matches: number;
  perfect_matches: number;
}

export interface OpenLibraryBook {
  key: string;
  title: string;
  author_name: string[];
  first_publish_year: number | null;
  publisher?: string;
  cover_i?: number;
  isbn?: string[];
}

export interface OpenLibrarySearchResult {
  numFound: number;
  start: number;
  docs: OpenLibraryBook[];
}

export interface ImageValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

export interface UserEdit {
  type: 'replace' | 'delete' | 'add' | 'manual_entry';
  spine_id: string;
  original_data?: BookMatch;
  new_data?: BookMatch | OpenLibraryBook;
  timestamp: Date;
}

export interface ProcessingState {
  status: 'idle' | 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  message: string;
  error?: string;
}

export interface ExportOptions {
  format: 'png' | 'jpg' | 'pdf';
  includeMetadata: boolean;
  includeOCRText: boolean;
  includeConfidenceScores: boolean;
  labelStyle: 'numbered' | 'titled';
}

export interface FinalizedResult {
  originalImage: string;
  labeledImage: string;
  bookList: BookMatch[];
  metadata: {
    processingTime: number;
    totalSpines: number;
    userEdits: UserEdit[];
    exportTimestamp: Date;
  };
}


