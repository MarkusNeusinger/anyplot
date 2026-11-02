import { fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { LegalPage } from 'src/pages/LegalPage';
import { render, screen } from 'src/test-utils';

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

    // One table row per store, each with its own figure: the 30 days belong to
    // the server logs only, and the feedback rows have no timer at all.
    const retention: [string, string][] = [
      ['server logs', '30 days'],
      ['feedback IP hash', 'ten minutes'],
      ['assistant telemetry', 'up to 180 days'],
      ['feedback case files', '180 days'],
      ['feedback entries, case rows', 'until you ask to delete them'],
    ];
    for (const [store, kept] of retention) {
      expect(
        screen.getByRole('row', { name: new RegExp(`^${store}\\s*${kept}$`) })
      ).toBeInTheDocument();
    }
    // Google Cloud, its logs included, runs in the EU region.
    expect(
      screen.getByText(
        /Google Cloud \(Run, SQL, Storage, Logging\) in the Netherlands \(europe-west4\)/
      )
    ).toBeInTheDocument();
    // The page states the current state only: no notes on what older entries still carry.
    expect(screen.queryByText(/before the move/)).not.toBeInTheDocument();
    expect(screen.queryByText(/unsalted/)).not.toBeInTheDocument();
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
    // The feedback's IP hash is salted; its ten minutes sit in the retention table.
    expect(screen.getByText(/a salted hash of your IP address limits spam/)).toBeInTheDocument();
    // Plausible's real property is cookieless and identifier-free, not that
    // the script is ours — it is Plausible's, only served from our domain.
    expect(screen.getByText(/its script is served through this domain/)).toBeInTheDocument();
    expect(screen.getByText(/Cloudflare uses your IP address/)).toBeInTheDocument();
    // The browser's storage is named, not hidden behind "no cookies".
    expect(screen.getByText(/your plot\s+votes, a release number/)).toBeInTheDocument();
  });

  // The data assistant's section, each claim pinned with the qualifier that
  // makes it true: experimental and open to everyone but pausable, training
  // excluded under Google Cloud's terms, the ids pseudonymous (not anonymous),
  // the data file unticked by default, and each legal basis with its purpose.
  it('describes the experimental data assistant without overclaiming', () => {
    render(<LegalPage />);

    expect(
      screen.getByText(/open to everyone, experimental and without warranty/)
    ).toBeInTheDocument();
    expect(screen.getByText(/nobody checks them by hand/)).toBeInTheDocument();
    expect(screen.getByText(/the operator may pause it at any time/)).toBeInTheDocument();
    expect(
      screen.getByText(
        /served through Google Cloud Vertex AI in the EU under Google Cloud.s data processing terms/
      )
    ).toBeInTheDocument();
    expect(screen.getByText(/your prompts are not used for training/)).toBeInTheDocument();
    expect(
      screen.getByText(/don.t paste personal data you are not allowed to share/)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/with no database, and is cleared after an hour idle/)
    ).toBeInTheDocument();
    // The renderer's answer cache has no idle timer of its own.
    expect(screen.getByText(/keeps its last 16 results in memory/)).toBeInTheDocument();
    expect(screen.getByText(/never your text, data, column or file names/)).toBeInTheDocument();
    // The language is about the user: only as a code, with rare ones folded into "other".
    expect(screen.getByText(/language code \(rare ones as "other"\)/)).toBeInTheDocument();
    // A public user's id is a salted random tab id that dies with the instance; only admins get the HMAC.
    expect(
      screen.getByText(
        /salted with a value that lives only as long as the server instance, in memory, never written down/
      )
    ).toBeInTheDocument();
    expect(screen.getByText(/keyed hash \(HMAC\)/)).toBeInTheDocument();
    // The 30-day server logs could only be joined by timestamp: pseudonymous, not anonymous.
    expect(
      screen.getByText(/only timestamps could match them to the 30-day server logs/)
    ).toBeInTheDocument();
    expect(screen.getByText(/so they are pseudonymous/)).toBeInTheDocument();
    // Nothing is kept without feedback; the box starts unticked, and leaving it so drops
    // data.csv only, while the profile sample stays.
    expect(screen.getByText(/kept only when you send feedback/)).toBeInTheDocument();
    expect(
      screen.getByText(/it starts unticked, which leaves out that file only/)
    ).toBeInTheDocument();
    expect(screen.getByText(/first 5 rows/)).toBeInTheDocument();
    // Each legal basis with what it covers; consent given at the send and withdrawable.
    expect(
      screen.getByRole('row', { name: /^Art\. 6\(1\)\(f\)\s*legitimate interest/ })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('row', { name: /^Art\. 6\(1\)\(b\)\s*your request: making the plot/ })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('row', {
        name: /^Art\. 6\(1\)\(a\)\s*your consent to a feedback case, given when you send it and withdrawable at any time by asking$/,
      })
    ).toBeInTheDocument();
    // "No cookies" holds for visitors; admins get Cloudflare Access's login cookie.
    expect(screen.getByText(/no cookies for visitors/)).toBeInTheDocument();
    expect(
      screen.getByText(/Cloudflare Access, which sets its own login cookie/)
    ).toBeInTheDocument();
    // Scope: the assistant's processing touches only the people who use it; the chat links here.
    const heading = screen.getByText('only if you use the data assistant (experimental)');
    expect(heading).toHaveAttribute('id', 'assistant');
    expect(
      screen.getByText(/if you only browse the catalogue, none of it touches you/)
    ).toBeInTheDocument();
    expect(
      screen.getByRole('row', {
        name: /^data assistant\s*Claude by Anthropic via Google Cloud Vertex AI \(EU\), if you use it$/,
      })
    ).toBeInTheDocument();
    // The code's licence with the Highcharts exception, and the transfers.
    expect(screen.getByText(/yours to use, as is/)).toBeInTheDocument();
    expect(
      screen.getByText(
        /Highcharts is free for non-commercial use, and a commercial use needs a licence from Highsoft/
      )
    ).toBeInTheDocument();
    expect(screen.getByText(/transfers outside Switzerland and the EU/)).toBeInTheDocument();
    // Browsing the catalogue involves no model, and nothing sent trains one.
    expect(screen.getByText(/browsing never reaches a model/)).toBeInTheDocument();
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
