import { render as rtlRender } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { ThemeProvider } from '@mui/material/styles';

import { AboutPage } from 'src/pages/AboutPage';
import { fireEvent, render, screen, styleAt, within } from 'src/test-utils';
import { theme } from 'src/theme';

vi.mock('src/hooks', () => ({
  useAnalytics: () => ({ trackEvent: vi.fn() }),
  useTheme: () => ({ isDark: false }),
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
    expect(transparency).toContainElement(
      screen.getByText('monthly running costs (as of November 2026)')
    );
  });

  it('names the builder with his photo and the links to his profiles', () => {
    render(<AboutPage />);

    const builder = document.getElementById('builder')!;
    expect(builder).toHaveTextContent('Markus Neusinger');
    // In the first person, with the year the README's "How I build anyplot" gives, which
    // test_readme_claims.py pins; "senior" is the AI workflow page's "then senior data analyst".
    expect(builder).toHaveTextContent(
      /I.m a chart nerd\. physicist by training, senior data analyst by trade\. since 2013 I have built data pipelines, models and the tools around them, lately with ai agents doing the legwork\./
    );
    // The years test_readme_claims.py holds to the AI workflow page's "from 2022 to 2024".
    expect(builder).toHaveTextContent(
      /lately with ai agents doing the legwork\. I know the stack from building it by hand: from 2022 to 2024 I built and ran a platform for blockchain market data, largely without ai\. on anyplot the agents write the code; I decide, test and send back\./
    );
    // The month test_readme_claims.py holds to the README's "Since November 2025".
    expect(builder).toHaveTextContent(
      /I have built it alone and in my own time since November 2025, in Visp, a small town in the Swiss Alps\. I wanted one place to find the right plot for my data\./
    );
    // The builder speaks for himself: no sentence of the page describes him from outside.
    expect(document.body).not.toHaveTextContent(/\bhe (has|built|leads|tests|corrects)\b/);
    // The file's own size, so the browser reserves the photo's height before it loads; decorative,
    // since the name stands beside it.
    const photo = builder.querySelector('img')!;
    expect(photo).toHaveAttribute(
      'src',
      'https://storage.googleapis.com/anyplot-static/images/markusneusinger-684.webp'
    );
    // Two files of the one picture: the 360px one covers the 110px slot at any pixel density, and
    // a window too narrow for the gutter is told so, so a phone never loads the 684px file.
    expect(photo).toHaveAttribute(
      'srcset',
      'https://storage.googleapis.com/anyplot-static/images/markusneusinger-360.webp 360w, ' +
        'https://storage.googleapis.com/anyplot-static/images/markusneusinger-684.webp 684w'
    );
    expect(photo).toHaveAttribute('sizes', '(min-width: 1248px) 216px, 110px');
    expect(photo).toHaveAttribute('width', '684');
    expect(photo).toHaveAttribute('height', '1381');
    expect(photo).toHaveAttribute('alt', '');
    expect(photo).toHaveAttribute('aria-hidden', 'true');
    // Narrower than the gutter needs, it stands beside the name at 110px, as before.
    expect(styleAt(photo).width).toBe('110px');
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

  // Outside the plot pipeline a pull request merges only on the owner's named OK (CLAUDE.md,
  // "PR Follow-Through"). The spec approval stands in the lede and the diagram, the month in "who
  // built it" and the origin, each pinned there.
  it('says ai models write the code, what I do, and links the README sections and the workflow page', () => {
    render(<AboutPage />);

    const paragraph = screen.getByText(
      /^ai models write anyplot.s code: the site, the api, and the agents behind .use with my data.\./
    );
    for (const sentence of [
      /I decide what gets built, cut the work into tasks and give each one to Claude Code, Claude in GitHub Actions, Gemini or Copilot, depending on what it needs and what it costs\./,
      /I test what comes back and send it back until it.s right\. outside the plot pipeline the agents merge nothing without my OK, and what I correct becomes a rule they follow\.$/,
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

  // test_readme_claims.py holds the 24 to the criteria registry. "more than thirty" is a floor on
  // the changes to prompts/quality-criteria.md, which a shallow CI clone cannot count; #7528 added
  // AR-09 after a review passed an altair chart whose title the crop had cut off.
  it('says who sets the rubric and that it changes', () => {
    render(<AboutPage />);

    expect(screen.getByText(/^every implementation is scored before it ships\./)).toHaveTextContent(
      /to 50 at the last review\. what counts as a good plot is my call; ai helped turn it into 24 criteria and their points\. the rubric isn.t fixed: it has changed more than thirty times since November 2025, for example after a review passed a plot whose title was cut off\. the stats page shows the score distribution per library\.$/
    );
  });

  // PipelineFlow.test.tsx holds the steps' words and order; here, that the page shows the figure
  // under the pipeline's text.
  it('draws the pipeline under its text, as a figure of its steps', () => {
    render(<AboutPage />);

    const figure = screen.getByRole('figure', { name: '// pipeline' });
    expect(within(figure).getAllByRole('listitem')).toHaveLength(5);
    expect(
      screen.getByText(/^the pipeline runs on its own schedule/).compareDocumentPosition(figure)
    ).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
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
      /pyplots\.ai, a catalogue of Python plotting examples\. it grew out of everyday work: showing colleagues a chart instead of explaining it at length\. they, and later people who found it online, wanted two things from it: ideas for which plot fits their data, and to get to know libraries they hadn.t used yet, since each has its own strengths\. after a few months/
    );
    expect(origin).toHaveTextContent(
      /it became anyplot\.ai\. today it covers fifteen libraries in four languages, and one colourblind-safe palette travels across all of them\.$/
    );
    // The timeline follows the text, from the start to today.
    const timeline = screen.getByText('first github release').closest('ol')!;
    expect(origin.compareDocumentPosition(timeline)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
    expect(timeline.firstElementChild).toHaveTextContent('nov 2025 pyplots.ai');
    expect(timeline.lastElementChild).toHaveTextContent(/^today$/);
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
      /I update the spec and regenerate its libraries\. I don.t fix a plot by editing its code: a patch fixes one plot, a fix to the spec or a rule reaches every plot it governs when that plot is next regenerated\.$/
    );
    expect(
      screen.queryByText(/maintains itself|humans curate|never patch/)
    ).not.toBeInTheDocument();
    expect(screen.getByText(/my own colourblind-safe categorical palette/)).toBeInTheDocument();
    expect(screen.getByText(/ignore this entirely\. I make it the default\./)).toBeInTheDocument();
  });

  // Four rounds of variants under docs/reference/palette-variants/ (v0 to v3), which
  // test_readme_claims.py counts; scripts/_palette_common.py measures the colour distances.
  it('says how many rounds the palette took', () => {
    render(<AboutPage />);

    expect(screen.getByText(/^every plot uses/)).toHaveTextContent(
      /validated against the three main forms of colour vision deficiency\. it took four rounds: the colour-distance numbers had to agree with what I like to look at\. it sits in the same neighbourhood as Okabe-Ito/
    );
  });

  it('keeps the library-agnostic point under the palette', () => {
    render(<AboutPage />);

    expect(
      screen.getByText(
        /^the palette travels with you across libraries\. switching tools doesn.t mean re-learning your colour grammar\.$/
      )
    ).toBeInTheDocument();
    // The two sentences carry the point alone; the penguin example before them is gone.
    expect(document.body).not.toHaveTextContent(/penguin/i);
    // The eight chips stand between the palette's first paragraph and those two sentences.
    const chip = screen.getByText('#009E73').closest('ul')!;
    expect(within(chip).getAllByRole('listitem')).toHaveLength(8);
    expect(screen.getByText(/^every plot uses/).compareDocumentPosition(chip)).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING
    );
    expect(chip.compareDocumentPosition(screen.getByText(/^the palette travels with you/))).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING
    );
    // The stack and costs now sit on this page: no pointer to the legal page for them.
    expect(screen.queryByText(/curious about the stack/)).not.toBeInTheDocument();
  });

  // A screen reader announces each list with its section's heading, so no new word is needed.
  it('names the chips and the timeline by the headings of their sections', () => {
    render(<AboutPage />);

    const chips = screen.getByRole('list', { name: 'palette' });
    expect(within(chips).getAllByRole('listitem')).toHaveLength(8);
    expect(chips).toHaveTextContent(/^brand green #009E73/);
    const timeline = screen.getByRole('list', { name: 'origin' });
    expect(timeline.tagName).toBe('OL');
    expect(timeline.firstElementChild).toHaveTextContent('nov 2025 pyplots.ai');
    expect(screen.getByRole('heading', { name: 'palette' }).id).toBe(
      chips.getAttribute('aria-labelledby')
    );
    expect(screen.getByRole('heading', { name: 'origin' }).id).toBe(
      timeline.getAttribute('aria-labelledby')
    );
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
      screen.getByText(/^experimental, open to everyone since November 2026\./)
    ).toHaveTextContent(
      /pick any plot, choose \.use_my_data\(\) on its page, and paste your data\. an agent adapts/
    );
  });

  // The agent design document (docs/concepts/agent-network.md) holds each part: the roles, the
  // validator, the points that decide a repair, the notes, the owner rules with their dates.
  // test_readme_claims.py holds "one repair and two reviews" to the agents' settings.
  it('explains the agents and my rules in a second paragraph, linking the design document', () => {
    render(<AboutPage />);

    const paragraph = screen.getByText(/^one agent talks to you/);
    expect(paragraph).toHaveTextContent(
      /^one agent talks to you, an adapter writes the code changes, and a reviewer scores the render; the loop that calls them is plain code\. a validator reads the code before anything runs, and code decides from the reviewer.s points whether a repair is due: one repair and two reviews at most\. what the review still finds comes back as notes with the plot\./
    );
    expect(paragraph).toHaveTextContent(
      /what the review still finds comes back as notes with the plot\. my rules: open to everyone, no login, hosted in the EU, and I keep what you paste or write only if you send feedback\. by those rules I decided which model answers, where the code it writes runs, and what the usage logs may hold; the design document on GitHub records these decisions with their dates\.$/
    );
    const link = screen.getByRole('link', { name: 'the design document on GitHub' });
    expect(link).toHaveAttribute('href', `${REPO}/blob/main/docs/concepts/agent-network.md`);
    expect(link).toHaveAttribute('target', '_blank');
    expect(paragraph).toContainElement(link);
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
    // ci-tests.yml runs the Python tests when a pull request changes Python outside plots/ or a
    // config file it lists, and the frontend's lint and tests when it changes app/; ci-lint.yml
    // lints any Python change. A pull request that changes only other code (R, Julia, or
    // JavaScript outside app/) starts neither, so the row names Python and frontend code only.
    // codecov.yml's patch target, codeql.yml, ci-migrations.yml; the live-site check is the merge
    // rule in CLAUDE.md (scripts/site-smoke.mjs).
    expect(
      screen.getByRole('row', {
        name: /^checks\s*tests and lint on every pull request that changes Python or frontend code outside the plot catalogue, an 80\s%\spatch-coverage target, CodeQL, every migration run on a throwaway PostgreSQL, and by rule a check of the live site after a merge$/,
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

  it('renders the running costs as of a named month, with what they leave out', () => {
    render(<AboutPage />);

    expect(screen.getByText('monthly running costs (as of November 2026)')).toBeInTheDocument();
    const costs: [string, string][] = [
      ['hosting: Cloud Run \\(site, api, data assistant, renderer\\)', '~\\$14'],
      ['database: Cloud SQL', '~\\$35'],
      ['data assistant model: Claude Haiku via Vertex AI', '~\\$12'],
      ['storage, logs and builds', '~\\$6'],
      ['domain \\(\\.ai\\)', '~\\$8'],
      ['total', '~\\$75/month'],
    ];
    for (const [item, cost] of costs) {
      expect(
        screen.getByRole('row', { name: new RegExp(`^${item}\\s*${cost}$`) })
      ).toBeInTheDocument();
    }
    // The prices before credits, so the note says which prices, what pays most of it, which
    // month each figure comes from, and that the model cost moves with use.
    expect(
      screen.getByText(/^at three-year commitment prices, before credits; a monthly cloud credit/)
    ).toHaveTextContent(
      /^at three-year commitment prices, before credits; a monthly cloud credit from a Google developer subscription pays most of it\. infrastructure as billed for October 2026, the assistant.s model at November.s pace; it grows with use\. development \(test runs and reviews\) is not included\. all costs are covered privately\.$/
    );
    expect(screen.queryByText(/promotional credits/)).not.toBeInTheDocument();
  });

  // Each figure is rounded on its own, so the total is checked against the rows it sums.
  it('totals the running costs from their rows', () => {
    render(<AboutPage />);

    const table = screen.getByText('monthly running costs (as of November 2026)')
      .nextElementSibling as HTMLElement;
    const amounts = within(table)
      .getAllByRole('row')
      .map(row => {
        const [label, value] = Array.from(row.querySelectorAll('th, td'), cell => cell.textContent);
        return [label, Number(/^~\$(\d+)/.exec(value ?? '')?.[1])] as const;
      });
    const total = amounts.find(([label]) => label === 'total')![1];
    const parts = amounts.filter(([label]) => label !== 'total').map(([, amount]) => amount);
    expect(parts).toHaveLength(5);
    expect(parts.every(Number.isFinite)).toBe(true);
    expect(parts.reduce((sum, amount) => sum + amount, 0)).toBe(total);
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
