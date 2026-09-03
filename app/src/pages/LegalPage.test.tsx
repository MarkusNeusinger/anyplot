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

  // The privacy section's load-bearing claims, each pinned where it is true.
  // A shortening pass is exactly what drops a qualifier — "30 days" silently
  // spreading over a store that has no timer, or the objection right losing
  // the condition that makes it one.
  it('names the legal basis, the jurisdiction and the whole set of rights', () => {
    render(<LegalPage />);

    expect(screen.getByText(/legitimate interest in protecting the site/)).toBeInTheDocument();
    expect(screen.getByText(/swiss data protection law applies/)).toBeInTheDocument();
    expect(
      screen.getByText(/object to the processing on grounds relating to your particular situation/)
    ).toBeInTheDocument();
    expect(screen.getByText(/complain to a supervisory authority/)).toBeInTheDocument();
  });

  it('gives each store its own retention, and no store a borrowed one', () => {
    render(<LegalPage />);

    // Cloud Logging has the 30 days; the feedback table has no timer at all.
    expect(screen.getByText(/retained for 30 days/)).toBeInTheDocument();
    expect(screen.getByText(/nothing deletes them on a timer/)).toBeInTheDocument();
  });

  it('does not claim more privacy than the code delivers', () => {
    render(<LegalPage />);

    // The feedback widget asks for "Name or email (optional)", so the old
    // blanket "no personal data" was false.
    expect(screen.getByText(/no personal data unless you type it/)).toBeInTheDocument();
    // Plausible's real property is cookieless and identifier-free, not that
    // the script is ours — it is Plausible's, only served from our domain.
    expect(screen.getByText(/the script is theirs/)).toBeInTheDocument();
    expect(screen.getByText(/Cloudflare stands in front of the site/)).toBeInTheDocument();
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
    expect(citadelLink).toHaveAttribute('href', 'https://github.com/MarkusNeusinger/cite-citadel');
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
