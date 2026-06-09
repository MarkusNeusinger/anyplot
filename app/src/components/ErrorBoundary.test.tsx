import { ReactNode } from 'react';

import { beforeEach, describe, expect, it, vi } from 'vitest';

// Must import after test-utils to get jest-dom matchers
import { ErrorBoundary } from 'src/components/ErrorBoundary';
import { render, screen } from 'src/test-utils';

// Component that throws on render
function ThrowingComponent({ message }: { message: string }): ReactNode {
  throw new Error(message);
}

// Suppress React error boundary console.error noise in tests
beforeEach(() => {
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

describe('ErrorBoundary', () => {
  it('renders children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <div>Hello World</div>
      </ErrorBoundary>
    );
    expect(screen.getByText('Hello World')).toBeInTheDocument();
  });

  it('renders fallback UI when child throws', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent message="test error" />
      </ErrorBoundary>
    );
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText(/unexpected error occurred/i)).toBeInTheDocument();
  });

  it('renders custom fallback when provided', () => {
    render(
      <ErrorBoundary fallback={<div>Custom Error</div>}>
        <ThrowingComponent message="test error" />
      </ErrorBoundary>
    );
    expect(screen.getByText('Custom Error')).toBeInTheDocument();
    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();
  });

  it('shows recovery buttons in default fallback', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent message="test error" />
      </ErrorBoundary>
    );
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /reload page/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /go home/i })).toBeInTheDocument();
  });

  it('toggles technical details disclosure', async () => {
    const { userEvent } = await import('src/test-utils');
    const user = userEvent.setup();

    render(
      <ErrorBoundary>
        <ThrowingComponent message="boom on iOS" />
      </ErrorBoundary>
    );

    expect(screen.queryByTestId('error-details')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /show technical details/i }));

    const details = screen.getByTestId('error-details');
    expect(details).toBeInTheDocument();
    expect(details.textContent).toContain('boom on iOS');
    expect(details.textContent).toContain('User-Agent:');
    expect(details.textContent).toContain('URL:');

    await user.click(screen.getByRole('button', { name: /hide technical details/i }));
    expect(screen.queryByTestId('error-details')).not.toBeInTheDocument();
  });

  it('copies details to the clipboard', async () => {
    const { userEvent } = await import('src/test-utils');
    const user = userEvent.setup();

    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText },
    });

    render(
      <ErrorBoundary>
        <ThrowingComponent message="copy me" />
      </ErrorBoundary>
    );

    await user.click(screen.getByRole('button', { name: /copy details/i }));

    expect(writeText).toHaveBeenCalledTimes(1);
    expect(writeText.mock.calls[0][0]).toContain('copy me');
    expect(await screen.findByRole('button', { name: /copied/i })).toBeInTheDocument();
  });

  it('recovers when Try Again is clicked', async () => {
    const { userEvent } = await import('src/test-utils');
    const user = userEvent.setup();

    // Use a flag to control whether the child throws
    let shouldThrow = true;

    function MaybeThrow() {
      if (shouldThrow) throw new Error('test');
      return <div>Recovered</div>;
    }

    const { rerender } = render(
      <ErrorBoundary>
        <MaybeThrow />
      </ErrorBoundary>
    );

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();

    // Stop throwing and click retry
    shouldThrow = false;
    await user.click(screen.getByRole('button', { name: /try again/i }));

    // Re-render to provide non-throwing child
    rerender(
      <ErrorBoundary>
        <MaybeThrow />
      </ErrorBoundary>
    );

    expect(screen.getByText('Recovered')).toBeInTheDocument();
  });
});
