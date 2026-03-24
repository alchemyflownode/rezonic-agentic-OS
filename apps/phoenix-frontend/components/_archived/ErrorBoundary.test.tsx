/**
 * Example test file
 * Shows how to write tests for REZ HIVE components and utilities
 * 
 * Run tests:
 *   npm test                  # Run once
 *   npm run test:watch        # Run in watch mode
 *   npm run test:coverage     # Generate coverage report
 */

import { render, screen } from '@testing-library/react';
import { ErrorBoundary } from '@/components/ErrorBoundary';

describe('ErrorBoundary', () => {
  // Suppress console.error for error boundary tests
  beforeEach(() => {
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders children when there is no error', () => {
    render(
      <ErrorBoundary>
        <div>Test Content</div>
      </ErrorBoundary>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('renders fallback UI when there is an error', () => {
    const ThrowError = () => {
      throw new Error('Test error');
    };

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
  });

  it('displays try again button', () => {
    const ThrowError = () => {
      throw new Error('Test error');
    };

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    const tryAgainButton = screen.getByRole('button', { name: /Try Again/i });
    expect(tryAgainButton).toBeInTheDocument();
  });
});

/**
 * Testing Best Practices
 * 
 * 1. UNIT TESTS - Test individual functions/components
 *    describe('function name', () => {
 *      it('should do X when Y', () => {
 *        expect(result).toBe(expected);
 *      });
 *    });
 * 
 * 2. INTEGRATION TESTS - Test component interactions
 *    it('should update state when button is clicked', () => {
 *      render(<Component />);
 *      fireEvent.click(screen.getByRole('button'));
 *      expect(screen.getByText('Updated')).toBeInTheDocument();
 *    });
 * 
 * 3.MOCKING - Mock external dependencies
 *    jest.mock('@/lib/logger');
 *    jest.spyOn(module, 'function').mockReturnValue(value);
 * 
 * 4. ASYNC TESTS - Handle promises
 *    it('should fetch data', async () => {
 *      render(<Component />);
 *      await screen.findByText('Loaded');
 *    });
 * 
 * 5. COVERAGE - Aim for high coverage
 *    npm run test:coverage
 *    Current target: 40% statement coverage
 * 
 * 6. COMMON ASSERTIONS
 *    expect(value).toBe(expected);                // Strict equality
 *    expect(value).toEqual(object);               // Deep equality
 *    expect(element).toBeInTheDocument();         // DOM checks
 *    expect(element).toHaveClass('className');    // CSS classes
 *    expect(fn).toHaveBeenCalled();               // Function calls
 *    expect(fn).toHaveBeenCalledWith(arg);        // Function arguments
 */
