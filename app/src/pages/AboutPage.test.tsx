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

  // spec-create.yml merges a spec only on the repository owner's `approved` label.
  it('says in the lede that ideas arrive as issues and that I approve the specs', () => {
    render(<AboutPage />);

    expect(
      screen.getByText(
        /plot ideas come in as GitHub issues; ai drafts the spec, generates code for every library, and reviews each implementation\. I approve new specs and tune the rules when something repeatedly fails\./
      )
    ).toBeInTheDocument();
  });

  it('describes itself by its builder and the things it covers, each a section of the page', () => {
    render(<AboutPage />);

    const description =
      'About anyplot.ai: built by Markus Neusinger with AI agents he directs. How the catalogue is written and reviewed, the stack, and what it costs to run.';
    expect(description.length).toBeLessThanOrEqual(155);
    expect(document.head.querySelector('meta[name="description"]')).toHaveAttribute(
      'content',
      description
    );
    expect(document.head.querySelector('meta[property="og:description"]')).toHaveAttribute(
      'content',
      description
    );
    // who built it; how ai agents write (how it is built, pipeline) and review the catalogue;
    // the stack and the running costs under transparency.
    const headings = screen.getAllByRole('heading').map(h => h.textContent);
    for (const heading of [
      'who built it',
      'how it is built',
      'pipeline',
      'review',
      'transparency',
    ]) {
      expect(headings).toContain(heading);
    }
    const transparency = document.getElementById('transparency')!;
    expect(transparency).toContainElement(screen.getByText('technology stack'));
    expect(transparency).toContainElement(screen.getByText('monthly running costs (October 2026)'));
  });

  it('names the builder with his photo and the links to his profiles', () => {
    render(<AboutPage />);

    const builder = document.getElementById('builder')!;
    expect(builder).toHaveTextContent('Markus Neusinger');
    // In the first person, with the year the README's "How I build anyplot" gives, which
    // test_readme_claims.py pins.
    expect(builder).toHaveTextContent(
      /I.m a chart nerd\. physicist by training, data analyst by trade\. since 2013 I have built data pipelines, models and the tools around them, lately with ai agents doing the legwork\./
    );
    expect(builder).toHaveTextContent(
      /on anyplot they write the code; I decide, test and send back\./
    );
    // The month test_readme_claims.py holds to the README's "Since November 2025".
    expect(builder).toHaveTextContent(
      /I have built it alone since November 2025, in Visp, a small town in the Swiss Alps\. I wanted one place to find the right plot for my data\./
    );
    // The builder speaks for himself: no sentence of the page describes him from outside.
    expect(document.body).not.toHaveTextContent(/\bhe (has|built|leads|tests|corrects)\b/);
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
    // His own site, like the other projects: no noreferrer, so its analytics see the referrer.
    const site = screen.getByRole('link', { name: 'neusinger.com' });
    expect(site).toHaveAttribute('href', 'https://neusinger.com');
    expect(site).toHaveAttribute('target', '_blank');
    expect(site).toHaveAttribute('rel', 'noopener');
    expect(builder).toContainElement(site);
    // Introduced once: the origin section no longer describes him anonymously.
    expect(screen.queryByText(/by a physicist and data analyst/)).not.toBeInTheDocument();
  });

  // spec-create.yml merges a spec only on the owner's `approved`; outside the plot pipeline a pull
  // request merges only on his named OK (CLAUDE.md, "PR Follow-Through").
  it('says ai models write the code, what I do, and links the README sections and the workflow page', () => {
    render(<AboutPage />);

    const paragraph = screen.getByText(
      /^ai models write anyplot.s code: the site, the api, and the agents behind .use with my data.\./
    );
    for (const sentence of [
      /I decide what gets built, cut the work into tasks and give each one to Claude Code, Claude in GitHub Actions, Gemini or Copilot, depending on what it needs and what it costs\./,
      /I test what comes back and send it back until it.s right\./,
      /a new spec needs my approval, and outside the plot pipeline the agents merge nothing without my OK\./,
      /what I correct becomes a rule the agents follow\. I have built it with ai agents since November 2025\.$/,
    ]) {
      expect(paragraph).toHaveTextContent(sentence);
    }
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
  // nightly cron; no workflow runs when a library ships a release. The checks before the review
  // are the ones a workflow runs: the renders exist and the canvas gate; none checks for a blank
  // image.
  it('states the review bar and the nightly regeneration as the workflows run them', () => {
    render(<AboutPage />);

    expect(
      screen.getByText(/automated checks come first: the code\s+runs, the canvas has its size\./)
    ).toBeInTheDocument();
    expect(screen.queryByText(/blank/)).not.toBeInTheDocument();
    expect(
      screen.getByText(/the bar drops 10 points per\s+repair, to 50 at the last review/)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/every night a job\s+regenerates the oldest implementations/)
    ).toBeInTheDocument();
    expect(screen.queryByText(/ships a\s+new release/)).not.toBeInTheDocument();
  });

  // textContent, not toHaveTextContent: the matchers collapse whitespace, and the block's columns
  // are spaces.
  it('draws the pipeline as a block with its columns aligned', () => {
    render(<AboutPage />);

    expect(screen.getByText(/^\/\/ pipeline/).textContent).toBe(
      [
        '// pipeline',
        'idea    → a github issue',
        'spec    → ai drafts, I approve',
        'code    → ai writes     (per library)',
        'review  → ai scores     (24 criteria)',
        'fix     → ai repairs    (up to 4 times)',
        'rules   → I set and change them',
      ].join('\n')
    );
    // One builder: the page names no "humans" anywhere.
    expect(document.body).not.toHaveTextContent(/\bhumans?\b/i);
  });

  // The first commit is from November 2025; CHANGELOG.md's 2.0.0 relaunch as anyplot.ai is from
  // April 2026, which test_readme_claims.py pins.
  it('tells the origin with the dates the repository shows', () => {
    render(<AboutPage />);

    expect(
      screen.getByText(
        /it started in November 2025 as pyplots\.ai, a catalogue of Python plotting examples\./
      )
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /after a few months on pyplots\.ai, I decided to go bigger\. in April 2026 it became anyplot\.ai\./
      )
    ).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent(/weekend/);
    // test_readme_claims.py holds the two counts to the library registry.
    const origin = screen.getByText(/^it started in November 2025/);
    expect(origin).toHaveTextContent(
      /pyplots\.ai, a catalogue of Python plotting examples\. it grew out of everyday work: finding plot ideas, and showing colleagues a chart instead of explaining it at length\. people wanted two things/
    );
    expect(origin).toHaveTextContent(
      /it became anyplot\.ai\. today it covers fifteen libraries in four languages, and one colorblind-safe palette travels across all of them\.$/
    );
  });

  // One person builds the site, so the page speaks as "I", never as "we".
  it('speaks in the first person singular throughout', () => {
    render(<AboutPage />);

    expect(document.body).not.toHaveTextContent(/\b(we|our|ours|us)\b/i);
    // A rule, not an absolute: the palette swap of May 2026 edited the plots' code catalogue-wide.
    expect(
      screen.getByText(
        /^the pipeline runs on its own schedule, by rules I set\. every night a job regenerates/
      )
    ).toHaveTextContent(
      /I update the spec and regenerate its libraries\. I don.t fix a plot by editing its code: a patch fixes one plot, a fix to the spec or a rule reaches every plot it governs\.$/
    );
    expect(screen.queryByText(/maintains itself|humans curate|never patch/)).not.toBeInTheDocument();
    expect(screen.getByText(/my own colourblind-safe categorical palette/)).toBeInTheDocument();
    expect(screen.getByText(/ignore this entirely\. I make it the default\./)).toBeInTheDocument();
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

  // The explainer at /agent says the same: .use_my_data() sits on a plot's page.
  it('says where .use_my_data() is, as the chat explainer does', () => {
    render(<AboutPage />);

    expect(
      screen.getByText(/^experimental, open to everyone since 2 november 2026\./)
    ).toHaveTextContent(
      /pick any plot, choose \.use_my_data\(\) on its page, and paste your data\. an agent adapts/
    );
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
    // Nine grouped rows, each label a row header.
    for (const group of [
      'site',
      'api',
      'catalogue pipeline',
      'data assistant',
      'google cloud',
      'edge & analytics',
      'reviews',
      'checks',
      'editor, typography',
    ]) {
      expect(screen.getAllByRole('rowheader', { name: group }).length).toBeGreaterThan(0);
    }
    // ci-tests.yml and ci-lint.yml on every code pull request, codecov.yml's patch target,
    // codeql.yml, ci-migrations.yml; the live-site check is the merge rule in CLAUDE.md
    // (scripts/site-smoke.mjs).
    expect(
      screen.getByRole('row', {
        name: /^checks\s*tests and lint on every code pull request, an 80\s%\spatch-coverage target, CodeQL, every migration run on a throwaway PostgreSQL, a check of the live site after a merge$/,
      })
    ).toBeInTheDocument();
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
