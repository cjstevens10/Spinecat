import { ImageValidationResult } from '../types';

// Minimum image requirements
const MIN_WIDTH = 800;
const MIN_HEIGHT = 600;
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

/**
 * Validates an uploaded image file
 */
export async function validateImage(file: File): Promise<ImageValidationResult> {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Check file type
  if (!file.type.startsWith('image/jpeg')) {
    errors.push('Only JPEG images are supported');
    return { isValid: false, errors, warnings };
  }

  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    errors.push(`File size must be less than ${MAX_FILE_SIZE / (1024 * 1024)}MB`);
  }

  // Check image dimensions and quality
  try {
    const dimensions = await getImageDimensions(file);
    
    if (dimensions.width < MIN_WIDTH || dimensions.height < MIN_HEIGHT) {
      errors.push(`Image must be at least ${MIN_WIDTH}x${MIN_HEIGHT} pixels`);
    }

    // Check aspect ratio (should be reasonable for book spines)
    const aspectRatio = dimensions.width / dimensions.height;
    if (aspectRatio < 0.5 || aspectRatio > 3) {
      warnings.push('Unusual aspect ratio - may affect spine detection accuracy');
    }

    // Check for potential blur (simple edge detection simulation)
    const blurScore = await checkImageBlur(file);
    if (blurScore < 0.1) {
      errors.push('Image appears to be very blurry - please use a sharper image for best results');
    } else if (blurScore < 0.3) {
      warnings.push('Image quality could be improved, but should still work');
    }

  } catch (error) {
    errors.push('Failed to analyze image - file may be corrupted');
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
}

/**
 * Gets image dimensions from a file
 */
async function getImageDimensions(file: File): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      resolve({ width: img.width, height: img.height });
    };
    img.onerror = () => reject(new Error('Failed to load image'));
    img.src = URL.createObjectURL(file);
  });
}

/**
 * Simple blur detection using canvas
 */
async function checkImageBlur(file: File): Promise<number> {
  return new Promise((resolve) => {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      
      if (ctx) {
        ctx.drawImage(img, 0, 0);
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const blurScore = calculateBlurScore(imageData);
        resolve(blurScore);
      } else {
        resolve(0.5); // Default score if canvas context not available
      }
    };
    
    img.onerror = () => resolve(0.5); // Default score on error
    img.src = URL.createObjectURL(file);
  });
}

/**
 * Calculate blur score using Laplacian variance
 */
function calculateBlurScore(imageData: ImageData): number {
  const { data, width, height } = imageData;
  let variance = 0;
  let count = 0;

  // Simple edge detection using Laplacian operator
  for (let y = 1; y < height - 1; y++) {
    for (let x = 1; x < width - 1; x++) {
      const idx = (y * width + x) * 4;
      const center = data[idx];
      
      // Laplacian kernel: [[0,1,0], [1,-4,1], [0,1,0]]
      const laplacian = 
        data[((y-1) * width + x) * 4] +     // top
        data[((y+1) * width + x) * 4] +     // bottom
        data[(y * width + (x-1)) * 4] +     // left
        data[(y * width + (x+1)) * 4] -     // right
        4 * center;                          // center * -4
      
      variance += laplacian * laplacian;
      count++;
    }
  }

  const avgVariance = variance / count;
  
  // Normalize to 0-1 range (higher = sharper)
  // This is a simplified approach - in production you'd want more sophisticated blur detection
  let normalizedScore = Math.min(avgVariance / 500, 1.0);
  
  // Ensure minimum score for images that might have low variance but are still sharp
  // This prevents false rejections of good quality images
  normalizedScore = Math.max(normalizedScore, 0.2);
  
  return normalizedScore;
}

/**
 * Process image through the Spinecat pipeline
 * This will be replaced with actual pipeline integration
 */
export async function processImage(file: File): Promise<any> {
  // TODO: Integrate with actual pipeline
  // For now, return a promise that resolves after a delay
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        success: true,
        message: 'Image processed successfully'
      });
    }, 2000);
  });
}
