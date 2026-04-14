import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../test-utils';
import { LegalPage } from './LegalPage';

vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('../hooks', () => ({
  useAnalytics: () => ({
    trackPageview: vi.fn(),
    trackEvent: vi.fn(),
  }),
}));

describe('LegalPage', () => {
  it('renders all section headings', () => {
    render(<LegalPage />);

    const headings = screen.getAllByRole('heading');
    const headingTexts = headings.map((h) => h.textContent);

    expect(headingTexts).toContain('Legal Notice');
    expect(headingTexts).toContain('Privacy Policy');
    expect(headingTexts).toContain('Transparency');
  });

  it('renders anchor navigation links to all sections', () => {
    render(<LegalPage />);

    const allLinks = screen.getAllByRole('link');
    const anchorLinks = allLinks.filter(
      (link) => link.getAttribute('href')?.startsWith('#')
    );

    expect(anchorLinks).toHaveLength(3);
    const hrefs = anchorLinks.map((a) => a.getAttribute('href'));
    expect(hrefs).toContain('#legal-notice');
    expect(hrefs).toContain('#privacy');
    expect(hrefs).toContain('#transparency');
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

  it('renders breadcrumb navigation', () => {
    render(<LegalPage />);

    expect(screen.getByRole('navigation', { name: 'breadcrumb' })).toBeInTheDocument();
  });

  it('renders footer with github link', () => {
    render(<LegalPage />);

    expect(screen.getByText('github')).toBeInTheDocument();
  });
});
