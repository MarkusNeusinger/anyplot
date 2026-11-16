import { fireEvent, render as rtlRender } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { ThemeProvider } from '@mui/material/styles';

import { LegalPage } from 'src/pages/LegalPage';
import { UNVERIFIED_HINT } from 'src/sections/stats/sharedLinks';
import { render, screen, within } from 'src/test-utils';
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
  it('names who is responsible, why the processing is allowed and the whole set of rights', () => {
    render(<LegalPage />);

    expect(screen.getByText('who is responsible')).toBeInTheDocument();
    expect(screen.getByText('Markus Neusinger (see above).')).toBeInTheDocument();
    // Each basis named in words with what it covers; consent given at the send and withdrawable.
    expect(screen.getByText('why this is allowed')).toBeInTheDocument();
    expect(screen.getByText(/a legitimate interest in protecting the site/)).toHaveTextContent(
      "a legitimate interest in protecting the site, counting its readers, and the assistant's telemetry and limits; your request: making the plot you ask the data assistant for; and your consent to a feedback case, given when you send it and withdrawable at any time by asking."
    );
    // Every right, the objection with the condition that makes it one, the address to write to
    // and that a feedback case can go early: the whole paragraph, so no clause can fall off its end.
    const rights = screen.getByText(/you can ask what is stored about you/);
    expect(rights).toHaveTextContent(
      /^you can ask what is stored about you and have it corrected, erased or restricted, object to the processing for a reason specific to your situation, and complain to a data protection authority\. a few lines to admin@anyplot\.ai are enough, also to have a feedback case deleted early\.$/
    );
    expect(within(rights).getByRole('link', { name: 'admin@anyplot.ai' })).toHaveAttribute(
      'href',
      'mailto:admin@anyplot.ai'
    );
    // Plain words, without the wording or the article numbers of legal texts, and without naming
    // the laws themselves.
    const privacy = document.getElementById('privacy') as HTMLElement;
    for (const term of [
      /Art\.\s*\d/,
      /legal bases/,
      /controller/,
      /supervisory/,
      /particular situation/,
      /on grounds relating/,
      /GDPR/,
      /data protection law/,
    ]) {
      expect(privacy.textContent, String(term)).not.toMatch(term);
    }
  });

  it('gives each kind of data its own period and place, in its own row', () => {
    render(<LegalPage />);

    // Each row closes with one line on how long its data is kept and where it runs, so a reader
    // never meets the data in one place and its period much further down. The whole line is
    // pinned per row: the 30 days belong to the server logs only, the feedback entries and the
    // case rows have no timer at all, and the feedback IP hash is cleared only when the next
    // feedback arrives (api/routers/feedback.py `_clear_expired_ip_hashes`), not after a flat
    // "ten minutes". The machine-read lines and the share counters share a row, so their line
    // ties each period to its own store: up to 180 days in Logging and BigQuery, no time limit in
    // SQL. Cloudflare's place stands once, on its own row. `feedback` labels two rows, the
    // site's and the data assistant's.
    const keptLines: [string, number, string][] = [
      ['analytics', 0, 'where: Plausible Analytics (EU, proxied)'],
      [
        'server logs',
        0,
        'kept: 30 days · where: Google Cloud (Logging) in the Netherlands (europe-west4)',
      ],
      [
        'machine readers, shared links',
        0,
        'machine reads: up to 180 days (Logging, BigQuery) · shares: no time limit (SQL) · where: Google Cloud in the Netherlands (europe-west4)',
      ],
      ['cloudflare', 0, 'where: global, EU data centers for EU visitors'],
      [
        'feedback',
        0,
        'entries: until you ask to delete them · IP hash: cleared by the next feedback after ten minutes; its salt dies with the server instance · where: Google Cloud (SQL) in the Netherlands (europe-west4)',
      ],
      [
        'logs',
        0,
        'telemetry: up to 180 days · where: Google Cloud (Logging, BigQuery) in the Netherlands (europe-west4)',
      ],
      [
        'feedback',
        1,
        'case files: 180 days · case rows: until you ask to delete them · where: Google Cloud (Storage, SQL) in the Netherlands (europe-west4)',
      ],
    ];
    const keptLineOf = (label: string, nth: number) =>
      (
        screen.getAllByRole('rowheader', { name: label })[nth].closest('tr') as HTMLElement
      ).querySelector('[data-kept-line]')?.textContent;
    // A no-break space ties each separator to the pair before it, so no wrap starts a line with
    // the dot.
    const tiedSeparator = `${String.fromCharCode(0xa0)}· `;
    for (const [label, nth, line] of keptLines) {
      expect(keptLineOf(label, nth), label).toBe(line.split(' · ').join(tiedSeparator));
    }
    // No other row carries such a line, so no period is borrowed by a row it does not belong
    // to; github states neither a period nor a place.
    expect(document.querySelectorAll('[data-kept-line]')).toHaveLength(keptLines.length);
    expect(keptLineOf('github', 0)).toBeUndefined();
    // The separate period and place tables are gone, their figures moved into the rows.
    expect(screen.queryByText('how long it stays')).not.toBeInTheDocument();
    expect(screen.queryByText('where it runs')).not.toBeInTheDocument();
    // The hosting place that holds for the whole site stays, word for word, as the sentence
    // before the transfers: it also places what no row does, such as the servers that hold a
    // session in memory. The transfers sentence itself stays word for word.
    expect(screen.getByText(/transfers outside Switzerland and the EU/)).toHaveTextContent(
      'hosting: Google Cloud (Run, SQL, Storage, Logging, BigQuery) in the Netherlands (europe-west4). Google Cloud and Cloudflare process data under their data processing terms, including their safeguards for transfers outside Switzerland and the EU.'
    );
    // Cloudflare's three roles (cdn, DDoS, the check) stand in its own row, not in the hosting
    // sentence, and its place stands once.
    expect(screen.getByRole('row', { name: /^cloudflare\s/ })).toHaveTextContent(
      /as the cdn, Cloudflare uses your IP address to rate-limit, filter bots and absorb DDoS attacks\./
    );
    expect(document.getElementById('privacy')?.textContent).not.toMatch(/cdn \/ ddos/);
    expect(screen.getAllByText(/EU data centers for EU visitors/)).toHaveLength(1);
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
    expect(
      screen.getByText(/no accounts, and no name or email unless you type one/)
    ).toBeInTheDocument();
    // Everything the feedback record actually holds, each field by its name, so a later trim
    // cannot quietly drop one, least of all the two identifiers a reader would care about most.
    expect(screen.getAllByRole('row', { name: /^feedback\s/ })[0]).toHaveTextContent(
      /message, reaction, optional contact, page, your window size, user-agent and a random id that ties your own submissions together, read only by the operator\./
    );
    // The feedback's IP hash is salted; when it goes stands on the feedback row's second line.
    expect(screen.getByText(/a salted IP hash limits spam/)).toBeInTheDocument();
    // Plausible's real property is cookieless and identifier-free; that its script is only
    // served from our domain stands on the row's second line as "proxied".
    expect(
      screen.getByText(/no cookies, no cross-site id, no IP address kept/)
    ).toBeInTheDocument();
    // The browser's storage is named, not hidden behind "no cookies".
    expect(screen.getByText(/your plot\s+votes, a release number/)).toBeInTheDocument();
    // Cloudflare's two uses stay apart: the cdn's use of your IP address, and the check that runs
    // only on the three actions. Turnstile, per Cloudflare's privacy addendum: what it reads, its
    // storage item, no cookie, and that Cloudflare uses the signals for itself, to improve the
    // check.
    const cloudflare = screen.getByRole('row', { name: /^cloudflare\s/ });
    expect(cloudflare).toHaveTextContent(
      /when you send feedback, rate a plot or open the data assistant, its Turnstile checks that a browser, not a script, is asking/
    );
    expect(cloudflare).toHaveTextContent(/user-agent and TLS fingerprint/);
    expect(cloudflare).toHaveTextContent(/keeps an item in your browser.s storage, with no cookie/);
    expect(cloudflare).toHaveTextContent(/anyplot learns only whether the check passed/);
    expect(cloudflare).toHaveTextContent(/on its own behalf, to improve the check/);
    expect(screen.getByText(/and Cloudflare Turnstile.s own\s+item/)).toBeInTheDocument();
    // The machine-read lines and the share counters share a row, and each tile on /stats links
    // its own anchor in it. #machine-readers wraps the whole cell; #shared-links is a block that
    // starts with its own name and runs to the end. So each anchor holds its own text, the
    // negative both kinds share and both periods. Each kind keeps its own negative, worded for
    // what its store can and cannot hold: the lines say nothing about anyone's browsing, the
    // counters nothing about who shared. Every request is a line, verified or not, so the row
    // claims no "verified only".
    const machineReaders = document.getElementById('machine-readers') as HTMLElement;
    const sharedLinks = document.getElementById('shared-links') as HTMLElement;
    expect(machineReaders).toContainElement(sharedLinks);
    expect(machineReaders).toHaveTextContent(
      /^crawlers, ai assistants and mcp clients: one content-free line per request, with vendor and purpose, whether Cloudflare verified it, the page or file and the status, and nothing about anyone.s browsing\.\s*shared links:/
    );
    // What a share is (the tile's header says the legal page explains it), what a counter holds,
    // each thing it never holds.
    expect(sharedLinks).toHaveTextContent(
      /^shared links: link previews that messengers and social networks fetch, counted per day, platform and page, and whether Cloudflare verified the fetcher, with no time of day and nothing about who shared\. neither holds an IP address or a user-agent\./
    );
    for (const anchor of [machineReaders, sharedLinks]) {
      expect(anchor).toHaveTextContent(/machine reads: up to 180 days \(Logging, BigQuery\)/);
      expect(anchor).toHaveTextContent(/shares: no time limit \(SQL\)/);
    }
    // The page does not say why an unverified share is no verdict on it; the tile's hint on the
    // word "unverified" does, so it has to keep saying it.
    expect(UNVERIFIED_HINT).toMatch(
      /no verdict on a share: WhatsApp and Signal fetch the preview from the sender.s own phone/
    );
  });

  // The data assistant's section, each claim pinned with the qualifier that
  // makes it true: experimental, without warranty and pausable, training
  // excluded under Google Cloud's terms, the ids pseudonymous (not anonymous),
  // and the data file unticked by default.
  it('describes the experimental data assistant without overclaiming', () => {
    render(<LegalPage />);

    expect(screen.getByRole('row', { name: /^status\s/ })).toHaveTextContent(
      /experimental, without warranty: results can be wrong and nobody checks them by hand\. the operator may pause it at any time\./
    );
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
      screen.getByText(/lives in server memory only and is cleared after an hour idle/)
    ).toBeInTheDocument();
    // The renderer's answer cache has no idle timer of its own.
    expect(screen.getByText(/keeps its last 16 results in memory/)).toBeInTheDocument();
    expect(
      screen.getByText(/no content: never your text, data, column or file names\./)
    ).toBeInTheDocument();
    // Every kind of field by its name: event types, plot type and library record what a visitor
    // did and chose, so no category of "technical details" covers them. The language only as a
    // code, with rare ones folded into "other".
    expect(screen.getByRole('row', { name: /^logs\s/ })).toHaveTextContent(
      /telemetry holds event types, formats, sizes, plot type, library, language code \(rare ones as "other"\), attempts, defect ids, statuses, latencies and token counts\./
    );
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
    const caseRow = screen.getAllByRole('row', { name: /^feedback\s/ })[1];
    expect(caseRow).toHaveTextContent(
      /only when you send feedback: a private bucket keeps the conversation, a profile of your data with its first 5 rows, the plot.s code and images, and the whole data file only if you tick "# include data\.csv" \(it starts unticked, which leaves out that file only\), and a triage row keeps your reaction, message, a hash of your tab id and the run.s details\./
    );
    // "No cookies" holds for visitors; admins get Cloudflare Access's login cookie.
    expect(screen.getByText(/no cookies for visitors/)).toBeInTheDocument();
    expect(
      screen.getByText(/Cloudflare Access, which sets its own login cookie/)
    ).toBeInTheDocument();
    // Scope: the assistant's processing touches only the people who use it; the chat links here.
    // The heading says it, so no sentence repeats it under it.
    const heading = screen.getByText('only if you use the data assistant (experimental)');
    expect(heading).toHaveAttribute('id', 'assistant');
    // Where the assistant's model runs stands in its own row, under the heading that limits it
    // to those who use the assistant.
    expect(
      screen.getByRole('row', {
        name: /^the model\s*what you paste and write goes to Claude by Anthropic, served through Google Cloud Vertex AI in the EU/,
      })
    ).toBeInTheDocument();
    // The code is yours, with the Highcharts exception, and the transfers.
    expect(
      screen.getByText(
        'yours to use, as is. Highcharts needs a licence from Highsoft for commercial use.'
      )
    ).toBeInTheDocument();
    expect(screen.getByText(/transfers outside Switzerland and the EU/)).toBeInTheDocument();
    // Nothing sent trains a model.
    expect(screen.getByText('no ai training')).toBeInTheDocument();
    expect(screen.getByText(/on what you send/)).toBeInTheDocument();
    // The server logs' purpose stands beside the data they hold.
    expect(screen.getByRole('row', { name: /^server logs\s/ })).toHaveTextContent(
      /IP address, URL and user-agent of each request, for security and debugging\./
    );
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
