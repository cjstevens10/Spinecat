import React from 'react';
import { motion } from 'framer-motion';
import { Loader2, CheckCircle, AlertCircle, BookOpen } from 'lucide-react';

import { ProcessingState } from '../types';

interface ProcessingStatusProps {
  state: ProcessingState;
}

const ProcessingStatus: React.FC<ProcessingStatusProps> = ({ state }) => {
  const getStatusIcon = () => {
    switch (state.status) {
      case 'uploading':
        return <Loader2 className="h-8 w-8 text-blue-400 animate-spin" />;
      case 'processing':
        return <Loader2 className="h-8 w-8 text-blue-400 animate-spin" />;
      case 'completed':
        return <CheckCircle className="h-8 w-8 text-green-400" />;
      case 'error':
        return <AlertCircle className="h-8 w-8 text-red-400" />;
      default:
        return <Loader2 className="h-8 w-8 text-blue-400 animate-spin" />;
    }
  };

  const getStatusColor = () => {
    switch (state.status) {
      case 'uploading':
      case 'processing':
        return 'text-blue-400';
      case 'completed':
        return 'text-green-400';
      case 'error':
        return 'text-red-400';
      default:
        return 'text-blue-400';
    }
  };

  const getProgressColor = () => {
    switch (state.status) {
      case 'uploading':
      case 'processing':
        return 'bg-blue-500';
      case 'completed':
        return 'bg-green-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-blue-500';
    }
  };

  return (
    <div className="max-w-md mx-auto">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="card text-center"
      >
        {/* Status Icon */}
        <div className="mb-6">
          {getStatusIcon()}
        </div>

        {/* Status Message (driven directly by backend message) */}
        <h3 className={`text-xl font-semibold mb-2 ${getStatusColor()}`}>
          {state.status === 'uploading' && 'Uploading Image...'}
          {state.status === 'processing' && (
            state.message || 'Processing...'
          )}
          {state.status === 'completed' && 'Processing Complete!'}
          {state.status === 'error' && 'Processing Failed'}
        </h3>

        <p className="text-slate-300 mb-6">
          {state.message}
        </p>

        {/* Progress Bar */}
        {state.status !== 'error' && (
          <div className="mb-6">
            <div className="w-full bg-slate-600 rounded-full h-3">
              <motion.div
                className={`h-3 rounded-full ${getProgressColor()}`}
                initial={{ width: 0 }}
                animate={{ width: `${state.progress}%` }}
                transition={{ duration: 0.5, ease: "easeOut" }}
              />
            </div>
            <p className="text-sm text-slate-300 mt-2">
              {state.progress.toFixed(2)}% complete
            </p>
          </div>
        )}

        {/* Error Details */}
        {state.status === 'error' && state.error && (
          <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 text-left">
            <h4 className="font-medium text-red-300 mb-2">Error Details:</h4>
            <p className="text-sm text-red-200">{state.error}</p>
          </div>
        )}

        {/* Processing Steps */}
        {state.status === 'processing' && (
          <div className="space-y-3 text-left">
            <div className="text-xs text-slate-400 mb-3 text-center">
              Processing pipeline stages
            </div>
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${state.progress >= 20 ? 'bg-green-500' : 'bg-slate-500'}`} />
              <span className={`text-sm ${state.progress >= 20 ? 'text-green-400' : 'text-slate-400'}`}>
                Detecting book spines with YOLO
              </span>
            </div>
            
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${state.progress >= 40 ? 'bg-green-500' : 'bg-slate-500'}`} />
              <span className={`text-sm ${state.progress >= 40 ? 'text-green-400' : 'text-slate-400'}`}>
                Running OCR on detected spines
                {state.message.includes('Processing spine') && (
                  <span className="ml-2 text-xs text-blue-400">
                    (Processing...)
                  </span>
                )}
              </span>
            </div>
            
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${state.progress >= 80 ? 'bg-green-500' : 'bg-slate-500'}`} />
              <span className={`text-sm ${state.progress >= 80 ? 'text-green-400' : 'text-slate-400'}`}>
                Matching books with library database
              </span>
            </div>
            
            <div className="flex items-center space-x-3">
              <div className={`w-3 h-3 rounded-full ${state.progress >= 100 ? 'bg-green-500' : 'bg-slate-500'}`} />
              <span className={`text-sm ${state.progress >= 100 ? 'text-green-400' : 'text-slate-400'}`}>
                Finalizing results
              </span>
            </div>
          </div>
        )}

        {/* Spine Count Display */}
        {state.status === 'processing' && state.message && (
          <div className="mt-4 p-4 bg-slate-700/50 rounded-lg border border-slate-600">
            <div className="flex items-center justify-center space-x-3 text-slate-200">
              <BookOpen className="w-5 h-5 text-blue-400" />
              <span className="text-sm font-medium">
                {state.message.includes('spines') ? state.message : 'Processing detected spines...'}
              </span>
            </div>
            
            {/* Real-time progress details */}
            {state.message.includes('OCR completed for spine') && (
              <div className="mt-3 text-center">
                <div className="text-xs text-slate-400 mb-2">
                  Individual spine OCR progress
                </div>
                <div className="flex items-center justify-center space-x-2">
                  <div className="inline-flex items-center px-2 py-1 rounded text-xs bg-blue-900/50 text-blue-300 border border-blue-700">
                    {state.message.match(/spine (\d+)/)?.[1] || '0'} of 5 spines processed
                  </div>
                </div>
              </div>
            )}
            
            {state.message.includes('Found') && (
              <div className="mt-2 text-center">
                <div className="text-xs text-slate-400">
                  {state.message.includes('spines') && state.message.includes('successful matches') && (
                    <div className="space-y-1">
                      <div className="inline-flex items-center px-2 py-1 rounded text-xs bg-blue-900/50 text-blue-300 border border-blue-700">
                        {state.message.match(/Found (\d+) spines/)?.[1] || '0'} spines detected
                      </div>
                      <div className="inline-flex items-center px-2 py-1 rounded text-xs bg-green-900/50 text-green-300 border border-green-700 ml-2">
                        {state.message.match(/(\d+) successful matches/)?.[1] || '0'} successful matches
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </motion.div>
    </div>
  );
};

export default ProcessingStatus;


