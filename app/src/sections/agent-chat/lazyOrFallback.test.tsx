import { Suspense } from 'react';

import { describe, expect, it } from 'vitest';

import { lazyOrFallback } from 'src/sections/agent-chat/lazyOrFallback';
import { render, screen } from 'src/test-utils';

const Loaded = ({ label }: { label: string }) => <p>loaded {label}</p>;
const Fallback = ({ label }: { label: string }) => <p role="alert">no chunk for {label}</p>;

describe('lazyOrFallback', () => {
  it('renders the chunk once it loads', async () => {
    const View = lazyOrFallback(() => Promise.resolve({ default: Loaded }), Fallback);
    render(
      <Suspense fallback="loading">
        <View label="grid" />
      </Suspense>
    );
    expect(await screen.findByText('loaded grid')).toBeInTheDocument();
  });

  it('renders the fallback with the same props when the chunk does not load', async () => {
    const View = lazyOrFallback<{ label: string }>(
      () => Promise.reject(new TypeError('Failed to fetch dynamically imported module')),
      Fallback
    );
    render(
      <Suspense fallback="loading">
        <View label="grid" />
      </Suspense>
    );
    expect(await screen.findByRole('alert')).toHaveTextContent('no chunk for grid');
  });
});
