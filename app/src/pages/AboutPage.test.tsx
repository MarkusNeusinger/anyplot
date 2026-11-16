import { render as rtlRender } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { ThemeProvider } from '@mui/material/styles';

import { AboutPage } from 'src/pages/AboutPage';
import { fireEvent, render, screen } from 'src/test-utils';
import { theme } from 'src/theme';

vi.mock('src/hooks', () => ({
  useAnalytics: () => ({ trackEvent: vi.fn() }),
}));

const REPO = 'https://github.com/MarkusNeusinger/anyplot';

describe('AboutPage', () => {
  it('opens with the lede, then who built it and how', () => {
    render(<AboutPage />);

    const headings = screen.getAllByRole('heading').map(h => h.textContent);
    expect(headings.slice(0, 3)).toEqual(['about', 'who built it', 'how it is built']);
    // The palette makes its own point; the old "library-agnostic" section repeated it.
    expect(headings).not.toContain('library-agnostic');
    expect(headings).toContain('transparency');
  });

  it('names the builder with his photo and the links to his profiles', () => {
    render(<AboutPage />);

    const builder = document.getElementById('builder')!;
    expect(builder).toHaveTextContent('Markus Neusinger');
    // As the README's "How I build anyplot" says it, and the year test_readme_claims.py pins.
    expect(builder).toHaveTextContent(
      /a physicist working in data and ai: since 2013 he has built data pipelines/
    );
    expect(builder).toHaveTextContent(/he built anyplot in Visp, a small town in the Swiss Alps/);
    expect(builder.querySelector('img')).toHaveAttribute(
      'src',
      'https://storage.googleapis.com/anyplot-static/images/markusneusinger.webp'
    );
    expect(screen.getByRole('link', { name: 'markus-neusinger' })).toHaveAttribute(
      'href',
      'https://www.linkedin.com/in/markus-neusinger/'
    );
    expect(screen.getByRole('link', { name: 'MarkusNeusinger' })).toHaveAttribute(
      'href',
      'https://github.com/MarkusNeusinger'
    );
    // Introduced once: the origin section no longer describes him anonymously.
    expect(screen.queryByText(/by a physicist and data analyst/)).not.toBeInTheDocument();
  });

  it('says models write the code and links the README sections and the workflow page', () => {
    render(<AboutPage />);

    expect(
      screen.getByText(/models write anyplot.s code — the site, the api, and the agents/)
    ).toBeInTheDocument();
    for (const [name, href] of [
      ['how I build anyplot', `${REPO}/blob/main/README.md#how-i-build-anyplot`],
      ['engineering highlights', `${REPO}/blob/main/README.md#engineering-highlights`],
      ['how anyplot is built with ai agents', `${REPO}/blob/main/docs/concepts/ai-workflow.md`],
    ]) {
      const link = screen.getByRole('link', { name });
      expect(link).toHaveAttribute('href', href);
      expect(link).toHaveAttribute('target', '_blank');
    }
  });

  // impl-review.yml lowers the bar 10 points per repair down to 50, and daily-regen.yml runs on a
  // nightly cron; no workflow runs when a library ships a release.
  it('states the review bar and the nightly regeneration as the workflows run them', () => {
    render(<AboutPage />);

    expect(
      screen.getByText(/the bar drops 10 points per\s+repair, to 50 at the last review/)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/every night a job\s+regenerates the oldest implementations/)
    ).toBeInTheDocument();
    expect(screen.queryByText(/ships a\s+new release/)).not.toBeInTheDocument();
  });

  it('keeps the library-agnostic point under the palette', () => {
    render(<AboutPage />);

    expect(screen.getByText(/a "gentoo penguin" is always blue/)).toBeInTheDocument();
    // The stack and costs now sit on this page: no pointer to the legal page for them.
    expect(screen.queryByText(/curious about the stack/)).not.toBeInTheDocument();
  });

  it('links the palette page through the router', () => {
    render(<AboutPage />);

    const link = screen.getByRole('link', { name: 'palette page' });
    expect(link).toHaveAttribute('href', '/palette');
    // A plain href renders the same anchor; only the router cancels the click's full page load.
    expect(fireEvent.click(link)).toBe(false);
  });

  it('links the stats, plots and mcp pages from the review, chat and mcp sections', () => {
    render(<AboutPage />);

    // The stats page twice: the review's score distribution and the mcp section's machine readers.
    for (const [name, href, links] of [
      ['stats page', '/stats', 2],
      ['pick any plot', '/plots', 1],
      ['mcp page', '/mcp', 1],
    ] as const) {
      const found = screen.getAllByRole('link', { name });
      expect(found).toHaveLength(links);
      for (const link of found) {
        expect(link).toHaveAttribute('href', href);
        expect(fireEvent.click(link)).toBe(false);
      }
    }
  });

  it('names the machine readers on the stats page in the mcp section', () => {
    render(<AboutPage />);

    expect(
      screen.getByText(/how many assistants and crawlers read the catalogue and how many came/)
    ).toBeInTheDocument();
  });

  it('sends a plot request to the issue form, with no label or title prefilled', () => {
    render(<AboutPage />);

    expect(screen.getByRole('link', { name: /request_plot\(\)/ })).toHaveAttribute(
      'href',
      'https://github.com/MarkusNeusinger/anyplot/issues/new?template=request-new-plot.yml'
    );
  });

  it('renders the technology stack', () => {
    render(<AboutPage />);

    const transparency = document.getElementById('transparency');
    expect(transparency).not.toBeNull();
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

  // The repository vendors JetBrains Mono (agents/anyplot/render/fonts/) under
  // the SIL OFL 1.1, so the MIT claim needs its qualifier and the font its own
  // line — dropping either makes the page claim a licence the fonts do not have.
  it('names JetBrains Mono and its own licence beside the MIT code', () => {
    render(<AboutPage />);

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
    render(<AboutPage />);

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
    render(<AboutPage />);

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
      render(<AboutPage />);

      for (const name of [
        'kurrentschrift.ink',
        'cite-citadel',
        'markus-neusinger',
        'MarkusNeusinger',
        'how I build anyplot',
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

  it('opens a fresh load of /about#transparency at the stack and costs', () => {
    // The route is lazy, so the browser's own jump to the fragment finds nothing; the page scrolls itself.
    const original = Element.prototype.scrollIntoView;
    const scrollIntoView = vi.fn();
    Element.prototype.scrollIntoView = scrollIntoView;
    try {
      rtlRender(
        <ThemeProvider theme={theme}>
          <MemoryRouter initialEntries={['/about#transparency']}>
            <AboutPage />
          </MemoryRouter>
        </ThemeProvider>
      );
      expect(scrollIntoView).toHaveBeenCalledTimes(1);
      expect(scrollIntoView.mock.contexts[0]).toHaveAttribute('id', 'transparency');
    } finally {
      Element.prototype.scrollIntoView = original;
    }
  });
});
