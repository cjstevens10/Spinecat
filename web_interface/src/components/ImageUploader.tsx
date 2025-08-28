import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { toast } from 'react-hot-toast';
import { motion } from 'framer-motion';
import { Upload, Image, AlertCircle } from 'lucide-react';
import { validateImage } from '../utils/imageUtils';

interface ImageUploaderProps {
  onImageUpload: (file: File) => Promise<void>;
}

const ImageUploader: React.FC<ImageUploaderProps> = ({ onImageUpload }) => {
  const [isProcessing, setIsProcessing] = useState(false);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    
    // Validate image
    const validation = await validateImage(file);
    
    if (!validation.isValid) {
      toast.error(validation.errors.join(', '));
      return;
    }

    try {
      setIsProcessing(true);
      await onImageUpload(file);
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Failed to upload image');
    } finally {
      setIsProcessing(false);
    }
  }, [onImageUpload]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'image/jpeg': ['.jpg', '.jpeg']
    },
    maxFiles: 1,
    disabled: isProcessing
  });

  return (
    <div className="max-w-2xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="text-center mb-12"
      >
        <h2 className="text-4xl font-bold text-white mb-4">
          Upload Book Spine Image
        </h2>
        <p className="text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
          Upload a high-quality image of book spines to automatically detect and identify books
        </p>
      </motion.div>

      {/* Upload Area */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3, delay: 0.1 }}
        className="relative"
      >
        <div
          {...getRootProps()}
          className={`
            relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200
            ${isDragActive 
              ? 'border-blue-400 bg-blue-500/10' 
              : 'border-slate-600 hover:border-slate-500 hover:bg-slate-800/30'
            }
            ${isDragReject ? 'border-red-400 bg-red-500/10' : ''}
            ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          <input {...getInputProps()} />
          
          {/* Upload Icon */}
          <div className="mb-6">
            <motion.div
              animate={{ 
                scale: isDragActive ? 1.1 : 1,
                rotate: isDragActive ? 5 : 0
              }}
              transition={{ duration: 0.2 }}
              className="w-20 h-20 bg-slate-700/50 rounded-full flex items-center justify-center mx-auto"
            >
              {isDragReject ? (
                <AlertCircle className="w-10 h-10 text-red-400" />
              ) : (
                <Upload className="w-10 h-10 text-slate-300" />
              )}
            </motion.div>
          </div>

          {/* Upload Text */}
          <div className="space-y-2">
            <h3 className="text-xl font-semibold text-white">
              {isDragReject ? 'Invalid file type' : 'Drop your image here'}
            </h3>
            <p className="text-slate-400">
              {isDragReject 
                ? 'Please upload a JPEG image file' 
                : 'or click to browse files'
              }
            </p>
            <p className="text-sm text-slate-500 mt-4">
              Supports: JPG, JPEG • Max: 10MB • High quality recommended
            </p>
          </div>

          {/* Processing State */}
          {isProcessing && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm rounded-2xl flex items-center justify-center"
            >
              <div className="text-center">
                <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
                <p className="text-white font-medium">Processing...</p>
              </div>
            </motion.div>
          )}
        </div>

        {/* Drag Reject Message */}
        {isDragReject && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 p-3 bg-red-500/20 border border-red-400/30 rounded-lg"
          >
            <p className="text-red-300 text-sm">
              Please upload a valid JPEG image file
            </p>
          </motion.div>
        )}
      </motion.div>

      {/* Instructions */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3, delay: 0.2 }}
        className="mt-8 text-center"
      >
        <div className="inline-flex items-center space-x-2 text-slate-400 text-sm">
          <Image className="w-4 h-4" />
          <span>For best results, ensure good lighting and clear text</span>
        </div>
      </motion.div>
    </div>
  );
};

export default ImageUploader;
