import { fireEvent, render as rtlRender } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { ThemeProvider } from '@mui/material/styles';

import { LegalPage } from 'src/pages/LegalPage';
import { render, screen } from 'src/test-utils';
import { theme } from 'src/theme';

const trackEvent = vi.fn();
vi.mock('src/hooks', () => ({
  useAnalytics: () => ({
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
    // the server logs only, and the feedback rows have no timer at all. The IP
    // hash is cleared only when the next feedback arrives (api/routers/feedback.py
    // `_clear_expired_ip_hashes`), so the row says so instead of a flat "ten minutes".
    const retention: [string, string][] = [
      ['server logs', '30 days'],
      [
        'feedback IP hash',
        'cleared by the next feedback after ten minutes; its salt dies with the server instance',
      ],
      ['assistant telemetry', 'up to 180 days'],
      ['machine readers', 'up to 180 days'],
      ['shared links', 'no time limit: counts per day, platform and page'],
      ['feedback case files', '180 days'],
      ['feedback entries, case rows', 'until you ask to delete them'],
    ];
    for (const [store, kept] of retention) {
      expect(
        screen.getByRole('row', { name: new RegExp(`^${store}\\s*${kept}$`) })
      ).toBeInTheDocument();
    }
    // The label is the row's header, so a screen reader announces it before the figure.
    expect(screen.getByRole('rowheader', { name: 'feedback IP hash' })).toBeInTheDocument();
    // Google Cloud, its logs and BigQuery included, runs in the EU region.
    expect(
      screen.getByText(
        /Google Cloud \(Run, SQL, Storage, Logging, BigQuery\) in the Netherlands \(europe-west4\)/
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
    // The feedback's IP hash is salted; when it goes sits in the retention table.
    expect(screen.getByText(/a salted hash of your IP address limits spam/)).toBeInTheDocument();
    // Plausible's real property is cookieless and identifier-free, not that
    // the script is ours — it is Plausible's, only served from our domain.
    expect(screen.getByText(/its script is served through this domain/)).toBeInTheDocument();
    expect(screen.getByText(/Cloudflare uses your IP address/)).toBeInTheDocument();
    // The browser's storage is named, not hidden behind "no cookies".
    expect(screen.getByText(/your plot\s+votes, a release number/)).toBeInTheDocument();
    // Turnstile, per Cloudflare's privacy addendum: what it reads, its storage item, no cookie,
    // and Cloudflare's own controller role for improving the check.
    expect(screen.getByRole('row', { name: /^bot check\s/ })).toHaveTextContent(
      /Cloudflare Turnstile checks that a browser, not a script, is asking/
    );
    expect(screen.getByText(/user-agent and TLS fingerprint/)).toBeInTheDocument();
    expect(screen.getByText(/with no cookie/)).toBeInTheDocument();
    expect(screen.getByText(/as its own controller, to improve the check/)).toBeInTheDocument();
    expect(screen.getByText(/and Cloudflare Turnstile.s own\s+item/)).toBeInTheDocument();
    // The machine-read line, with the two things it never holds, under the anchor that
    // /legal#machine-readers lands on. Every request is a line, verified or not, so the row
    // claims no "verified only".
    const machineReaders = document.getElementById('machine-readers');
    expect(machineReaders).toHaveTextContent(/one content-free\s+line/);
    expect(machineReaders).toHaveTextContent(/whether Cloudflare verified it/);
    expect(machineReaders).toHaveTextContent(/no IP address, no user-agent/);
    // The share counter, under the anchor /legal#shared-links lands on (the tile on /stats links
    // it): what a row holds, each thing it never holds, and that it has no time limit.
    const sharedLinks = document.getElementById('shared-links');
    expect(sharedLinks).toHaveTextContent(/fetches a page.s preview image/);
    expect(sharedLinks).toHaveTextContent(/the day, the platform and the page/);
    expect(sharedLinks).toHaveTextContent(/no IP address, no\s+user-agent, no time of day/);
    expect(sharedLinks).toHaveTextContent(/nothing about who shared/);
    expect(sharedLinks).toHaveTextContent(/kept\s+without a time limit/);
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
    // Eight grouped rows, each label a row header.
    for (const group of [
      'site',
      'api',
      'catalogue pipeline',
      'data assistant',
      'google cloud',
      'edge & analytics',
      'reviews',
      'editor, typography',
    ]) {
      expect(screen.getAllByRole('rowheader', { name: group }).length).toBeGreaterThan(0);
    }
    expect(
      screen.getByRole('row', {
        name: /^data assistant\s*Google ADK, Claude Haiku 5\.5 via Vertex AI \(EU\)/,
      })
    ).toBeInTheDocument();
    expect(
      screen.getByText(/15\s+plotting libraries in Python, R, Julia and JavaScript/)
    ).toBeInTheDocument();
    // Only the services the repository pins to europe-west4 carry the region.
    expect(
      screen.getByText(
        /Cloud Build and Artifact Registry in the\s+Netherlands \(europe-west4\), plus Secret Manager and Cloud Monitoring/
      )
    ).toBeInTheDocument();
  });

  it('opens a fresh load of /legal#assistant at the assistant section', () => {
    // The route is lazy, so the browser's own jump to the fragment finds nothing; the page scrolls itself.
    const original = Element.prototype.scrollIntoView;
    const scrollIntoView = vi.fn();
    Element.prototype.scrollIntoView = scrollIntoView;
    try {
      rtlRender(
        <ThemeProvider theme={theme}>
          <MemoryRouter initialEntries={['/legal#assistant']}>
            <LegalPage />
          </MemoryRouter>
        </ThemeProvider>
      );
      expect(scrollIntoView).toHaveBeenCalledTimes(1);
      expect(scrollIntoView.mock.contexts[0]).toHaveAttribute('id', 'assistant');
    } finally {
      Element.prototype.scrollIntoView = original;
    }
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

  it('renders the running costs of one named month, with what they leave out', () => {
    render(<LegalPage />);

    expect(screen.getByText('monthly running costs (October 2026)')).toBeInTheDocument();
    const costs: [string, string][] = [
      ['hosting: Cloud Run \\(site, api, data assistant, renderer\\)', '~\\$10'],
      ['database: Cloud SQL', '~\\$25'],
      ['data assistant model: Claude Haiku via Vertex AI', '~\\$15'],
      ['storage, logs and builds', '~\\$1'],
      ['domain \\(\\.ai\\)', '~\\$8'],
      ['total', '~\\$60/month'],
    ];
    for (const [item, cost] of costs) {
      expect(
        screen.getByRole('row', { name: new RegExp(`^${item}\\s*${cost}$`) })
      ).toBeInTheDocument();
    }
    // Paid after discounts, so the note says which ones, and that the model cost moves with use.
    expect(
      screen.getByText(/after three-year commitments and promotional credits/)
    ).toBeInTheDocument();
    expect(screen.getByText(/the assistant.s model cost\s+grows with use/)).toBeInTheDocument();
    expect(
      screen.getByText(/development tools and subscriptions are not included/)
    ).toBeInTheDocument();
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

  it('sends no event for an outbound link: the tracker script counts those itself', () => {
    const plausible = vi.fn();
    vi.stubGlobal('plausible', plausible);
    try {
      render(<LegalPage />);

      for (const name of [
        'kurrentschrift.ink',
        'cite-citadel',
        'markus-neusinger',
        '@MarkusNeusinger',
        'MarkusNeusinger',
      ]) {
        const link = screen.getByRole('link', { name });
        expect(link).toHaveAttribute('href', expect.stringMatching(/^https:\/\//));
        fireEvent.click(link);
      }

      expect(plausible).not.toHaveBeenCalled();
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
