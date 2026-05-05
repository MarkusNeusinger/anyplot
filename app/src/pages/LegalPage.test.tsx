import { describe, it, expect, vi } from 'vitest';
import { fireEvent } from '@testing-library/react';
import { render, screen } from '../test-utils';
import { LegalPage } from './LegalPage';

vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const trackEvent = vi.fn();
vi.mock('../hooks', () => ({
  useAnalytics: () => ({
    trackPageview: vi.fn(),
    trackEvent: (...args: unknown[]) => trackEvent(...args),
  }),
}));

describe('LegalPage', () => {
  it('renders all section headings', () => {
    render(<LegalPage />);

    const headings = screen.getAllByRole('heading');
    const headingTexts = headings.map((h) => h.textContent);

    expect(headingTexts).toContain('legal notice');
    expect(headingTexts).toContain('privacy policy');
    expect(headingTexts).toContain('transparency');
  });

  it('renders operator information', () => {
    render(<LegalPage />);

    const nameMatches = screen.getAllByText(/Markus Neusinger/);
    expect(nameMatches.length).toBeGreaterThan(0);
    expect(screen.getByText(/Visp, Switzerland/)).toBeInTheDocument();
  });

  it('renders contact email link', () => {
    render(<LegalPage />);

    const emailLinks = screen.getAllByRole('link', { name: 'admin@anyplot.ai' });
    expect(emailLinks[0]).toHaveAttribute('href', 'mailto:admin@anyplot.ai');
  });

  it('renders Plausible as analytics provider', () => {
    render(<LegalPage />);

    const plausibleLinks = screen.getAllByText(/Plausible/);
    expect(plausibleLinks.length).toBeGreaterThan(0);
  });

  it('renders the technology stack', () => {
    render(<LegalPage />);

    expect(screen.getByRole('link', { name: 'React' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /FastAPI/ })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /PostgreSQL/ })).toBeInTheDocument();
  });

  it('renders hosting costs', () => {
    render(<LegalPage />);

    expect(screen.getByText('~$34/month')).toBeInTheDocument();
  });

  it('tracks external link clicks for linkedin, x and github', () => {
    trackEvent.mockClear();
    render(<LegalPage />);

    fireEvent.click(screen.getByRole('link', { name: 'markus-neusinger' }));
    fireEvent.click(screen.getByRole('link', { name: '@MarkusNeusinger' }));
    fireEvent.click(screen.getByRole('link', { name: 'MarkusNeusinger' }));

    expect(trackEvent).toHaveBeenCalledWith('external_link', { destination: 'linkedin' });
    expect(trackEvent).toHaveBeenCalledWith('external_link', { destination: 'x' });
    expect(trackEvent).toHaveBeenCalledWith('external_link', { destination: 'github_personal' });
  });

});
