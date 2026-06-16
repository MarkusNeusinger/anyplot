import { describe, expect, it, vi } from 'vitest';

import { NotFoundPage } from 'src/pages/NotFoundPage';
import { render, screen } from 'src/test-utils';

// Mock react-helmet-async to avoid provider requirement
vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

describe('NotFoundPage', () => {
  it('renders page.miss() heading', () => {
    render(<NotFoundPage />);
    expect(screen.getByRole('heading', { level: 1, name: /page not found/i })).toBeInTheDocument();
  });

  it('renders 404 sub-message', () => {
    render(<NotFoundPage />);
    expect(screen.getByText(/404 — no route matched/i)).toBeInTheDocument();
  });

  it('renders link back to home', () => {
    render(<NotFoundPage />);
    const link = screen.getByRole('link', { name: /go home/i });
    expect(link).toHaveAttribute('href', '/');
  });
});
