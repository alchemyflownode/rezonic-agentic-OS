/**
 * Error Boundary Component
 * Catches React component errors and displays fallback UI
 * Prevents entire app from crashing
 */

'use client';

import React, { ReactNode, ReactElement } from 'react';
import { AlertTriangle } from 'lucide-react';
import { logger } from '@/lib/logger';

interface Props {
  children: ReactNode;
  fallback?: ReactElement;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: undefined,
      errorInfo: undefined,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error to observability service
    logger.error('ErrorBoundary', error, {
      componentStack: errorInfo.componentStack,
      error: error.toString(),
    });

    // Update state with error details
    this.setState({
      error,
      errorInfo,
    });

    // In production, send to error tracking service (Sentry, etc)
    if (process.env.NODE_ENV === 'production' && 'fetch' in window) {
      this.reportErrorToService(error, errorInfo);
    }
  }

  private reportErrorToService = async (error: Error, errorInfo: React.ErrorInfo) => {
    try {
      await fetch('/api/errors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: error.toString(),
          stack: error.stack,
          componentStack: errorInfo.componentStack,
          timestamp: new Date().toISOString(),
        }),
      });
    } catch (e) {
      // Silently fail to avoid recursive errors
      console.error('Failed to report error:', e);
    }
  };

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: undefined,
      errorInfo: undefined,
    });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen bg-[#030405] text-white flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-black/50 border border-red-500/30 rounded-2xl p-8 backdrop-blur-sm" role="alert" aria-live="assertive">
            {/* Icon + Title */}
            <div className="flex items-center gap-3 mb-4">
              <div className="p-3 bg-red-500/10 rounded-lg">
                <AlertTriangle className="w-6 h-6 text-red-400" aria-hidden="true" />
              </div>
              <h1 className="text-xl font-semibold text-white">Something went wrong</h1>
            </div>

            {/* Error Details */}
            <p className="text-sm text-white/80 mb-4">
              An unexpected error occurred. The error has been logged and our team will look into it.
            </p>

            {/* Dev Error Info */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="bg-black/50 border border-red-500/20 rounded-lg p-3 mb-4">
                <summary className="cursor-pointer font-medium text-red-300 hover:text-red-200">
                  Error Details (click to expand)
                </summary>
                <div className="mt-3 max-h-40 overflow-y-auto">
                  <p className="text-xs font-mono text-red-300 whitespace-pre-wrap break-words">
                    {this.state.error.toString()}
                  </p>
                  {this.state.errorInfo?.componentStack && (
                    <p className="text-xs font-mono text-white/70 mt-2 whitespace-pre-wrap break-words">
                      {this.state.errorInfo.componentStack}
                    </p>
                  )}
                </div>
              </details>
            )}

            {/* Actions */}
            <div className="flex gap-2">
              <button
                type="button"
                onClick={this.handleReset}
                aria-label="Retry loading the application"
                className="flex-1 px-4 py-2 bg-cyan-500/10 border border-cyan-500/30 rounded-lg text-cyan-400 hover:bg-cyan-500 hover:text-black transition-all font-medium text-sm focus:outline-2 focus:outline-offset-2 focus:outline-cyan-400"
              >
                Try Again
              </button>
              <button
                type="button"
                onClick={() => (window.location.href = '/')}
                aria-label="Return to home page"
                className="flex-1 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white/80 hover:bg-white/10 hover:text-white transition-all font-medium text-sm focus:outline-2 focus:outline-offset-2 focus:outline-amber-400"
              >
                Go Home
              </button>
            </div>

            {/* Support Info */}
            <p className="text-xs text-white/70 text-center mt-4">
              Error ID: {this.state.error?.stack?.substring(0, 8) || 'unknown'}
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Segment Error Boundary - wraps specific sections
 * Use to prevent one failing component from crashing rest of page
 */
export function SegmentErrorBoundary({
  children,
  name = 'Component',
}: {
  children: ReactNode;
  name?: string;
}) {
  return (
    <ErrorBoundary
      fallback={
        <div className="p-4 bg-red-500/5 border border-red-500/20 rounded-lg" role="alert">
          <p className="text-red-500 text-sm font-medium">
            ⚠️ {name} encountered an error and could not be displayed.
          </p>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
}
