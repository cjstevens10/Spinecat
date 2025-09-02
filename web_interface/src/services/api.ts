import { ProcessingResult, OpenLibraryBook } from '../types';

export class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = 'http://127.0.0.1:8002';
  }

  // Public getter for base URL
  public getBaseUrl(): string {
    return this.baseUrl;
  }

  /**
   * Test API connection
   */
  async testConnection(): Promise<{ status: string; filename: string; size: number }> {
    try {
      console.log('API: Testing connection...');
      const response = await fetch(`${this.baseUrl}/api/test`, {
        method: 'POST',
        body: new FormData()
      });
      
      console.log('API: Test response:', response.status, response.statusText);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      console.log('API: Test result:', result);
      return result;
    } catch (error) {
      console.error('API: Connection test failed:', error);
      throw error;
    }
  }

  /**
   * Start image processing - returns task_id
   */
  async startProcess(file: File): Promise<{ task_id: string }> {
    try {
      console.log('API: Starting processImage...');
      console.log('API: baseUrl:', this.baseUrl);
      console.log('API: file:', file.name, file.size, file.type);
      
      const formData = new FormData();
      formData.append('file', file);
      
      console.log('API: Making fetch request to:', `${this.baseUrl}/api/process-image`);
      
      const response = await fetch(`${this.baseUrl}/api/process-image`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      console.log('API: Process started successfully:', result);
      return result;
    } catch (error) {
      console.error('API: Failed to start process:', error);
      throw error;
    }
  }

  /**
   * Get progress for a specific task
   */
  async getProgress(taskId: string): Promise<{ status: string; progress: number; message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/progress/${taskId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to get progress:', error);
      throw error;
    }
  }

  /**
   * Get result for a completed task
   */
  async getResult(taskId: string): Promise<ProcessingResult> {
    try {
      const response = await fetch(`${this.baseUrl}/api/result/${taskId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (data.status !== 'completed') {
        throw new Error(`Task not completed: ${data.status}`);
      }
      return data;
    } catch (error) {
      console.error('Failed to get result:', error);
      throw error;
    }
  }

  /**
   * Search for books
   */
  async searchBooks(query: string, limit: number = 5): Promise<OpenLibraryBook[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/search-books?query=${encodeURIComponent(query)}&limit=${limit}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      // Handle the structured response from backend
      if (data.success && Array.isArray(data.results)) {
        return data.results;
      } else if (Array.isArray(data)) {
        // Fallback: if backend returns array directly
        return data;
      } else {
        console.warn('Unexpected search response format:', data);
        return [];
      }
    } catch (error) {
      console.error('Failed to search books:', error);
      return [];
    }
  }
}

export const apiService = new ApiService();
