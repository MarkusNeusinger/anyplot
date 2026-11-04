import { describe, expect, it, vi } from 'vitest';

import { LibrariesSection } from 'src/sections/landing/LibrariesSection';
import { render, screen } from 'src/test-utils';

vi.mock('src/hooks', () => ({
  useAnalytics: () => ({ trackPageview: vi.fn(), trackEvent: vi.fn() }),
}));

describe('LibrariesSection', () => {
  it('points libraries.all() at the libraries page', () => {
    render(<LibrariesSection libraries={[]} onLibraryClick={vi.fn()} />);

    expect(screen.getByRole('link', { name: 'libraries.all()' })).toHaveAttribute(
      'href',
      '/libraries'
    );
  });
});
