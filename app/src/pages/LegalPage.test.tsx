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
    // Each basis named in words with what it covers, one point each; consent given at the send
    // and withdrawable. Anchored, so no point and no qualifier can fall off.
    expect(screen.getByText('why this is allowed')).toBeInTheDocument();
    expect(screen.getByText(/a legitimate interest in protecting the site/)).toHaveTextContent(
      /^• a legitimate interest in protecting the site, counting its readers, and the assistant's telemetry and limits\s*• your request: making the plot you ask the data assistant for\s*• your consent to a feedback case: you give it when you send it and can withdraw it at any time by asking$/
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

  it('says what I do not do right after who is responsible, then what the browser keeps', () => {
    render(<LegalPage />);

    // The block stands directly under "who is responsible", before the first row of what is
    // processed.
    const who = screen.getByText('who is responsible');
    const notDone = screen.getByText('what I do not do');
    expect(who.nextElementSibling?.nextElementSibling).toBe(notDone);
    // Three short points and nothing else in them.
    const points = notDone.nextElementSibling as HTMLElement;
    expect(points).toHaveTextContent(
      /^• no cookies for visitors\s*• no accounts, and no name or email unless you type one\s*• no ai training on what you send$/
    );
    // What the browser keeps and the one login cookie stand in a paragraph of their own below the
    // points, every item of the storage list included.
    const storage = points.nextElementSibling as HTMLElement;
    expect(storage).toHaveTextContent(
      /^the browser's storage keeps UI settings, your plot votes, a release number, the random ids named here and Cloudflare Turnstile's own item\. I sign in through Cloudflare Access, which sets its own login cookie\.$/
    );
    expect(storage.nextElementSibling).toBe(screen.getByText('what is processed'));
    expect(document.getElementById('privacy')?.textContent).not.toMatch(/admins sign in/);
  });

  it('points from the disclaimer to the about page for how the examples are made', () => {
    render(<LegalPage />);

    const disclaimer = screen.getByText('disclaimer').nextElementSibling as HTMLElement;
    expect(disclaimer).toHaveTextContent(
      /^a personal portfolio project\. the plot examples are generated and maintained by ai workflows and meant as a starting point for your own data\. how that works, and my part in it: see about\. the code is provided "as is" under the MIT License; review it before production use\.$/
    );
    expect(within(disclaimer).getByRole('link', { name: 'about' })).toHaveAttribute(
      'href',
      '/about'
    );
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
    // Then who reads it: the admin page's "copy prompt for Claude Code" button hands the message,
    // the page and the reaction to the coding assistant (src/utils/claudePrompt.ts), so the row
    // names that recipient, and #privacy must not claim a sole reader ("read only by").
    expect(screen.getAllByRole('row', { name: /^feedback\s/ })[0]).toHaveTextContent(
      /message, reaction, optional contact, page, your window size, user-agent and a random id that ties your own submissions together\. I read them, and when I work on one, its message, page and reaction can go to the ai assistant I code with \(Claude by Anthropic\)\. a salted IP hash limits spam\./
    );
    expect(document.getElementById('privacy')?.textContent).not.toMatch(/read only by/);
    // The feedback's IP hash is salted; when it goes stands on the feedback row's second line.
    expect(screen.getByText(/a salted IP hash limits spam/)).toBeInTheDocument();
    // Plausible's real property is cookieless and identifier-free; that its script is only
    // served from this domain stands on the row's second line as "proxied".
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
      /its Turnstile runs when you send feedback, rate a plot or open the data assistant, and checks that a browser, not a script, is asking\. for that it reads your IP address, user-agent and TLS fingerprint and keeps an item in your browser.s storage, with no cookie\. anyplot learns only whether the check passed\./
    );
    expect(cloudflare).toHaveTextContent(/user-agent and TLS fingerprint/);
    expect(cloudflare).toHaveTextContent(/keeps an item in your browser.s storage, with no cookie/);
    expect(cloudflare).toHaveTextContent(/anyplot learns only whether the check passed/);
    expect(cloudflare).toHaveTextContent(/on its own behalf, to improve the check/);
    expect(screen.getByText(/and Cloudflare Turnstile.s own\s+item/)).toBeInTheDocument();
    // The machine-read lines and the share counters share a row, and each tile on /stats links
    // its own anchor in it. #machine-readers wraps the whole cell; #shared-links is a block that
    // starts with its own name and runs to the end. So each anchor holds its own text, the
    // negative both kinds share, both periods and the place. Every request is a line, verified or
    // not, so the row claims no "verified only". What a line or a counter holds beyond that holds
    // nothing about a person and lives in docs/reference/machine-readers.md and
    // docs/reference/plausible.md.
    const machineReaders = document.getElementById('machine-readers') as HTMLElement;
    const sharedLinks = document.getElementById('shared-links') as HTMLElement;
    expect(machineReaders).toContainElement(sharedLinks);
    expect(machineReaders).toHaveTextContent(
      /^crawlers, ai assistants and mcp clients: one line per request\.\s*shared links:/
    );
    // What a share is (the tile's header says the legal page explains it) and what neither store
    // ever holds.
    expect(sharedLinks).toHaveTextContent(
      /^shared links: counts of the link previews that messengers and social networks fetch\. neither holds an IP address or a user-agent\./
    );
    for (const anchor of [machineReaders, sharedLinks]) {
      expect(anchor).toHaveTextContent(/neither holds an IP address or a user-agent\./);
      expect(anchor).toHaveTextContent(/machine reads: up to 180 days \(Logging, BigQuery\)/);
      expect(anchor).toHaveTextContent(/shares: no time limit \(SQL\)/);
      expect(anchor).toHaveTextContent(/where: Google Cloud in the Netherlands \(europe-west4\)/);
    }
    // The shares' "no time of day" is not stretched over the machine-read lines, which carry a
    // timestamp: it went with the other fields.
    expect(machineReaders).not.toHaveTextContent(/time of day/);
    // The page does not say why an unverified share is no verdict on it; the tile's hint on the
    // word "unverified" does, so it has to keep saying it.
    expect(UNVERIFIED_HINT).toMatch(
      /no verdict on a share: WhatsApp and Signal fetch the preview from the sender.s own phone/
    );
  });

  // The data assistant's section, each claim pinned with the qualifier that
  // makes it true: experimental (the heading), its terms of use on the
  // assistant's own page, training excluded under Google Cloud's terms, the ids
  // pseudonymous (not anonymous), and the data file unticked by default.
  it('describes the experimental data assistant without overclaiming', () => {
    render(<LegalPage />);

    // The chat's notice links "how the assistant works" here, so the row says what it does; its
    // terms of use (status, limits, the code's licence) stand on its own page, which the row names
    // and links.
    const whatItIs = screen.getByRole('row', { name: /^what it is\s/ });
    expect(whatItIs).toHaveTextContent(
      /^what it is\s*it adapts a catalogue plot to your data\. status, limits and your code: see the data assistant.s page\.$/
    );
    expect(
      within(whatItIs).getByRole('link', { name: "the data assistant's page" })
    ).toHaveAttribute('href', '/agent');
    // The terms that moved are gone from the privacy section, and so are their two rows. What
    // touches personal data stays: what the limits count on, the tab id and your IP address (the
    // ids row), what not to paste (the model row) and the limits as a reason in the bases sentence.
    const privacySection = document.getElementById('privacy') as HTMLElement;
    for (const moved of [
      /without warranty/,
      /results can be wrong/,
      /nobody checks them by hand/,
      /may pause it at any time/,
      /use it only with data you may share/,
      /unlawful content/,
      /automated requests/,
      /daily limits apply/,
      /a misuse can pause you/,
      /yours to use/,
      /Highcharts/,
      /Highsoft/,
    ]) {
      expect(privacySection.textContent, String(moved)).not.toMatch(moved);
    }
    expect(screen.queryByRole('rowheader', { name: 'limits' })).not.toBeInTheDocument();
    expect(screen.queryByRole('rowheader', { name: 'your code' })).not.toBeInTheDocument();
    // The per-tab limits and the pause after misuse count on the salted tab id, the per-network
    // limits on the salted address: both uses of an identifier, so the ids row names them while
    // the sentences that state the limits stand on the assistant's page.
    expect(screen.getByRole('row', { name: /^ids\s/ })).toHaveTextContent(
      /^ids\s*a random tab id stands in for you\. the per-tab limits and a pause after misuse go by that id, the per-network limits by your IP address\. both ids are salted with a value/
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
    // Nothing is kept without feedback: the condition opens the row, and "then" carries it into
    // both the bucket and the triage row. The box starts unticked, and leaving it so drops
    // data.csv only, while the profile sample stays. The cases are read in a session with the
    // coding assistant (.claude/skills/triage-agent-cases), so the row names that recipient and
    // what it reads.
    const caseRow = screen.getAllByRole('row', { name: /^feedback\s/ })[1];
    expect(caseRow).toHaveTextContent(
      /^feedback\s*only when you send feedback\. a private bucket then keeps the conversation, a profile of your data with its first 5 rows, and the plot.s code and images\. it keeps the whole data file only if you tick "# include data\.csv"; the box starts unticked, which leaves out that file only\. a triage row then keeps your reaction, message, a hash of your tab id and the run.s details\. I read the cases together with the ai assistant I code with \(Claude by Anthropic\): your reaction and message, the conversation, the data sample or file, the plot and its code\./
    );
    // "No cookies" holds for visitors; the one admin gets Cloudflare Access's login cookie.
    expect(screen.getByText(/no cookies for visitors/)).toBeInTheDocument();
    expect(
      screen.getByText(/I sign in through Cloudflare Access, which sets its own login cookie\./)
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
    // The transfers.
    expect(screen.getByText(/transfers outside Switzerland and the EU/)).toBeInTheDocument();
    // Nothing sent trains a model. One person runs the site, so the list speaks in the first
    // person singular.
    expect(screen.getByText('what I do not do')).toBeInTheDocument();
    expect(screen.queryByText(/what we do not do/)).not.toBeInTheDocument();
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

  // The chat links #assistant, the two tiles on /stats link #machine-readers and #shared-links.
  it.each(['assistant', 'machine-readers', 'shared-links'])(
    'opens a fresh load of /legal#%s at its place',
    anchor => {
      // The route is lazy, so the browser's own jump to the fragment finds nothing; the page
      // scrolls itself.
      const original = Element.prototype.scrollIntoView;
      const scrollIntoView = vi.fn();
      Element.prototype.scrollIntoView = scrollIntoView;
      try {
        rtlRender(
          <ThemeProvider theme={theme}>
            <MemoryRouter initialEntries={[`/legal#${anchor}`]}>
              <LegalPage />
            </MemoryRouter>
          </ThemeProvider>
        );
        expect(scrollIntoView).toHaveBeenCalledTimes(1);
        expect(scrollIntoView.mock.contexts[0]).toHaveAttribute('id', anchor);
      } finally {
        Element.prototype.scrollIntoView = original;
      }
    }
  );

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
