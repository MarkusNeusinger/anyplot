import { describe, it, expect } from 'vitest';
import { render, screen } from '../test-utils';
import { NotFoundPage } from './NotFoundPage';

// Mock react-helmet-async to avoid provider requirement
vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

describe('NotFoundPage', () => {
  it('renders 404 heading', () => {
    render(<NotFoundPage />);
    expect(screen.getByText('404')).toBeInTheDocument();
  });

  it('renders page not found message', () => {
    render(<NotFoundPage />);
    expect(screen.getByText('page not found')).toBeInTheDocument();
  });

  it('renders link back to home', () => {
    render(<NotFoundPage />);
    const link = screen.getByText('back to pyplots.ai');
    expect(link.closest('a')).toHaveAttribute('href', '/');
  });
});
