import { fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { LegalPage } from 'src/pages/LegalPage';
import { render, screen } from 'src/test-utils';

vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const trackEvent = vi.fn();
vi.mock('src/hooks', () => ({
  useAnalytics: () => ({
    trackPageview: vi.fn(),
    trackEvent: (...args: unknown[]) => trackEvent(...args),
  }),
}));

describe('LegalPage', () => {
  it('renders all section headings', () => {
    render(<LegalPage />);

    const headings = screen.getAllByRole('heading');
    const headingTexts = headings.map(h => h.textContent);

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

  it('renders other projects links without noreferrer', () => {
    render(<LegalPage />);

    const kurrentLink = screen.getByRole('link', { name: 'kurrentschrift.ink' });
    expect(kurrentLink).toHaveAttribute('href', 'https://kurrentschrift.ink');
    expect(kurrentLink).toHaveAttribute('target', '_blank');
    expect(kurrentLink).toHaveAttribute('rel', 'noopener');

    const citadelLink = screen.getByRole('link', { name: 'cite-citadel' });
    expect(citadelLink).toHaveAttribute('href', 'https://markusneusinger.github.io/cite-citadel/');
    expect(citadelLink).toHaveAttribute('target', '_blank');
    expect(citadelLink).toHaveAttribute('rel', 'noopener');
  });

  it('tracks external link clicks for other projects', () => {
    trackEvent.mockClear();
    render(<LegalPage />);

    fireEvent.click(screen.getByRole('link', { name: 'kurrentschrift.ink' }));
    fireEvent.click(screen.getByRole('link', { name: 'cite-citadel' }));

    expect(trackEvent).toHaveBeenCalledWith('external_link', { destination: 'kurrentschrift' });
    expect(trackEvent).toHaveBeenCalledWith('external_link', { destination: 'cite_citadel' });
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
