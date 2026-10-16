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
    // blanket "no personal data" was false — and so is any restatement of it:
    // an IP address, an IP hash and the feedback session id are personal data
    // whether or not you typed them, so the bullet promises only name/email.
    expect(screen.getByText(/no name or email unless you type one/)).toBeInTheDocument();
    // Everything the feedback record actually holds, so a later trim cannot
    // quietly drop the two identifiers a reader would care about most.
    expect(screen.getByText(/your window size/)).toBeInTheDocument();
    expect(
      screen.getByText(/a random id that ties your own submissions together/)
    ).toBeInTheDocument();
    // Plausible's real property is cookieless and identifier-free, not that
    // the script is ours — it is Plausible's, only served from our domain.
    expect(screen.getByText(/the script is theirs/)).toBeInTheDocument();
    expect(screen.getByText(/Cloudflare stands in front of the site/)).toBeInTheDocument();
  });

  // The data assistant's section, each claim pinned with the qualifier that
  // makes it true: a preview only admins reach, training excluded only under
  // Vertex AI's terms, telemetry pseudonymous (not anonymous), the data file
  // ticked by default, and a case row that has no timer while its files do.
  it('describes the data assistant preview without overclaiming', () => {
    render(<LegalPage />);

    expect(
      screen.getByText(/only the operator and the\s+site.s admins can open/)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/served through Google Cloud Vertex AI in the\s+EU/)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/processed under Google Cloud.s data\s+processing terms/)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/don.t paste personal data you are not allowed to\s+share/)
    ).toBeInTheDocument();
    expect(screen.getByText(/there is no session database/)).toBeInTheDocument();
    expect(screen.getByText(/pseudonymous, not\s+anonymous/)).toBeInTheDocument();
    expect(screen.getByText(/up to 180 days/)).toBeInTheDocument();
    expect(screen.getByText(/keyed hash \(HMAC\)/)).toBeInTheDocument();
    // Unticking the box drops data.csv only; the profile sample stays.
    expect(screen.getByText(/unticking leaves out that file only/)).toBeInTheDocument();
    expect(screen.getByText(/first 5 rows as a sample/)).toBeInTheDocument();
    // The renderer's answer cache has no idle timer of its own.
    expect(screen.getByText(/keeps its last 16 results/)).toBeInTheDocument();
    expect(screen.getByText(/nothing deletes it on a timer/)).toBeInTheDocument();
    expect(screen.getByText(/Art\. 6\(1\)\(b\) GDPR/)).toBeInTheDocument();
    expect(screen.getByText(/Art\. 6\(1\)\(f\) GDPR/)).toBeInTheDocument();
    // Scope: the assistant's processing touches only the people who use it.
    expect(screen.getByText('only if you use the data assistant (preview)')).toBeInTheDocument();
    expect(screen.getByText(/if you\s+only browse the catalogue, none of it/)).toBeInTheDocument();
    expect(
      screen.getByText(/Claude models by Anthropic \(EU\) — only when you use the\s+data assistant/)
    ).toBeInTheDocument();
    // Browsing the catalogue still involves no model; only the assistant does.
    expect(screen.getByText(/never sees a visitor.s request/)).toBeInTheDocument();
  });

  it('renders the technology stack', () => {
    render(<LegalPage />);

    expect(screen.getByRole('link', { name: 'React' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /FastAPI/ })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /PostgreSQL/ })).toBeInTheDocument();
  });

  // The repository vendors JetBrains Mono (agents/anyplot/render/fonts/) under
  // the SIL OFL 1.1, so the MIT claim needs its qualifier and the font its own
  // line — dropping either makes the page claim a licence the fonts do not have.
  it('names JetBrains Mono and its own licence beside the MIT code', () => {
    render(<LegalPage />);

    expect(screen.getByRole('link', { name: 'JetBrains Mono' })).toHaveAttribute(
      'href',
      'https://github.com/JetBrains/JetBrainsMono'
    );
    expect(screen.getByRole('link', { name: 'SIL Open Font License 1.1' })).toHaveAttribute(
      'href',
      'https://openfontlicense.org'
    );
    expect(
      screen.getByText(/the attribution strip under plots created from your own data/)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/bundled third-party fonts keep their own licences/)
    ).toBeInTheDocument();
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
