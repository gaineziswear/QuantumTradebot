import React from 'react';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  className 
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8'
  };

  return (
    <Loader2 
      className={cn(
        'animate-spin text-gray-600', 
        sizeClasses[size], 
        className
      )} 
    />
  );
};

interface LoadingCardProps {
  title?: string;
  message?: string;
  className?: string;
}

export const LoadingCard: React.FC<LoadingCardProps> = ({ 
  title = 'Loading...', 
  message = 'Please wait while we fetch your data.',
  className 
}) => (
  <div className={cn(
    'flex flex-col items-center justify-center p-8 bg-white rounded-2xl border-0 shadow-lg',
    className
  )}>
    <LoadingSpinner size="lg" className="mb-4" />
    <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
    <p className="text-gray-600 text-center text-sm">{message}</p>
  </div>
);

interface LoadingOverlayProps {
  isVisible: boolean;
  title?: string;
  className?: string;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ 
  isVisible, 
  title = 'Processing...',
  className 
}) => {
  if (!isVisible) return null;

  return (
    <div className={cn(
      'absolute inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-50 rounded-2xl',
      className
    )}>
      <div className="text-center">
        <LoadingSpinner size="lg" className="mb-3" />
        <p className="text-gray-700 font-medium">{title}</p>
      </div>
    </div>
  );
};

interface SkeletonProps {
  className?: string;
  lines?: number;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className, lines = 1 }) => {
  return (
    <div className="space-y-2">
      {Array.from({ length: lines }).map((_, index) => (
        <div
          key={index}
          className={cn(
            'h-4 bg-gray-200 rounded animate-pulse',
            index === lines - 1 && lines > 1 ? 'w-3/4' : 'w-full',
            className
          )}
        />
      ))}
    </div>
  );
};

interface DataLoadingStateProps {
  isLoading: boolean;
  isError: boolean;
  error?: string;
  isEmpty?: boolean;
  emptyMessage?: string;
  children: React.ReactNode;
}

export const DataLoadingState: React.FC<DataLoadingStateProps> = ({
  isLoading,
  isError,
  error,
  isEmpty,
  emptyMessage = 'No data available',
  children
}) => {
  if (isLoading) {
    return <LoadingCard title="Loading Data" message="Fetching latest information..." />;
  }

  if (isError) {
    return (
      <div className="text-center p-8 bg-red-50 rounded-2xl border border-red-200">
        <div className="text-red-600 mb-2">⚠️ Error Loading Data</div>
        <p className="text-red-700 text-sm">{error || 'Something went wrong'}</p>
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className="text-center p-8 bg-gray-50 rounded-2xl">
        <div className="text-gray-400 mb-2">📊</div>
        <p className="text-gray-600">{emptyMessage}</p>
      </div>
    );
  }

  return <>{children}</>;
};
