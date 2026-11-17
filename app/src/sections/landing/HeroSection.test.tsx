import { beforeEach, describe, expect, it, vi } from 'vitest';

import { render, screen, userEvent } from 'src/test-utils';

const trackEvent = vi.fn();

vi.mock('src/hooks', async () => {
  const actual = await vi.importActual<typeof import('src/hooks')>('src/hooks');
  return {
    ...actual,
    useAnalytics: () => ({ trackEvent, trackPageview: vi.fn() }),
  };
});

vi.mock('src/sections/landing/PlotOfTheDayTerminal', () => ({
  PlotOfTheDayTerminal: () => <div data-testid="potd-terminal" />,
}));

vi.mock('src/sections/landing/TypewriterText', () => ({
  TypewriterText: () => <div data-testid="typewriter" />,
}));

const lane = vi.hoisted(() => ({ open: false as boolean | null }));
vi.mock('src/hooks/useAgentLaneOpen', () => ({ useAgentLaneOpen: () => lane.open }));

import { AGENT_LANE_LABEL, AGENT_LANE_LINE, HeroSection } from 'src/sections/landing/HeroSection';

/** Every style emotion wrote into the document so far. */
const styles = () =>
  [...document.querySelectorAll('style')].map(style => style.textContent ?? '').join('\n');

/** The class emotion generated for an element's `sx`. */
function emotionClass(element: Element): string {
  const name = Array.from(element.classList).find(c => /^css-[\w-]+$/.test(c));
  if (!name) throw new Error('the element carries no emotion class');
  return name;
}

describe('HeroSection', () => {
  beforeEach(() => {
    trackEvent.mockClear();
    lane.open = false;
  });

  it('announces .use_my_data() only while the public lane is open, leading to the catalogue', async () => {
    const user = userEvent.setup();
    const { rerender } = render(<HeroSection potd={null} />);
    expect(screen.queryByRole('link', { name: AGENT_LANE_LABEL })).not.toBeInTheDocument();

    lane.open = true;
    rerender(<HeroSection potd={null} />);
    const link = screen.getByRole('link', { name: AGENT_LANE_LABEL });
    expect(link).toHaveTextContent(`# ${AGENT_LANE_LINE} →`);
    expect(link).toHaveTextContent('# new: pick any plot, then .use_my_data() →');
    expect(link).not.toHaveTextContent(/experimental/i);
    expect(link).toHaveAttribute('href', '/plots');

    await user.click(link);
    expect(trackEvent).toHaveBeenCalledWith('nav_click', {
      source: 'hero_use_my_data',
      target: '/plots',
    });
  });

  it('keeps the line hidden while the lane probe is pending', () => {
    lane.open = null;
    render(<HeroSection potd={null} />);
    expect(screen.queryByRole('link', { name: AGENT_LANE_LABEL })).not.toBeInTheDocument();
  });

  it('names the builder in the eyebrow, a link to the about page that Tab reaches first', async () => {
    const user = userEvent.setup();
    const { container } = render(<HeroSection potd={null} />);

    const builder = screen.getByRole('link', { name: 'Markus Neusinger' });
    expect(builder).toHaveAttribute('href', '/about');
    // Only the name is the link; `by` is plain text, and the separator is gone.
    expect(builder).toHaveTextContent(/^Markus Neusinger$/);
    expect(builder.parentElement).toHaveTextContent(/^by Markus Neusinger$/);
    // One copy of the link at every width, so the keyboard meets it once.
    expect(
      Array.from(container.querySelectorAll('a')).filter(a => a.getAttribute('href') === '/about')
    ).toHaveLength(1);
    // The first link of the hero: the eyebrow sits above the headline.
    await user.tab();
    expect(builder).toHaveFocus();
  });

  it('shows the phrase above the name only below md, where the masthead hides it', () => {
    render(<HeroSection potd={null} />);

    const phrase = screen.getByText('the open plot catalogue');
    const byline = screen.getByRole('link', { name: 'Markus Neusinger' }).parentElement;
    if (!byline) throw new Error('the byline line is missing');
    // Two lines set in the markup: the phrase, then the byline, each a block of its own.
    expect(phrase.nextElementSibling).toBe(byline);
    // jsdom applies no media query, so read the CSS emotion wrote for each line's class.
    const css = styles();
    const phraseClass = emotionClass(phrase);
    expect(css).toMatch(new RegExp(`\\.${phraseClass}\\{[^}]*display:block;`));
    // MUI's md breakpoint is 900 px.
    expect(css).toMatch(
      new RegExp(`@media \\(min-width: ?900px\\)\\{\\.${phraseClass}\\{display:none;\\}\\}`)
    );
    const bylineClass = emotionClass(byline);
    expect(css).toMatch(new RegExp(`\\.${bylineClass}\\{[^}]*display:block;`));
    expect(css).not.toMatch(new RegExp(`\\.${bylineClass}\\{[^}]*display:none;`));
  });

  it('reports a click on the name as nav_click from hero_about', async () => {
    const user = userEvent.setup();
    render(<HeroSection potd={null} />);

    await user.click(screen.getByRole('link', { name: 'Markus Neusinger' }));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', {
      source: 'hero_about',
      target: '/about',
    });
  });

  it('says in the intro who approves the specs and sets the rules', () => {
    render(<HeroSection potd={null} />);

    expect(screen.getByText(/^every plot begins as a library-agnostic spec\./)).toHaveTextContent(
      /^every plot begins as a library-agnostic spec\. ai drafts implementations across every supported library, validates them against quality criteria, and keeps them current\. I approve new specs and set the rules\. you discover, copy, and adapt — plug in your data\. that.s it\.$/
    );
  });

  it('tracks the primary browse CTA, mcp link and github link', async () => {
    const user = userEvent.setup();
    render(<HeroSection potd={null} />);

    await user.click(screen.getByLabelText('Browse plots'));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', {
      source: 'hero_cta_browse',
      target: '/plots',
    });

    await user.click(screen.getByLabelText('Connect via MCP'));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', { source: 'hero_mcp', target: '/mcp' });

    await user.click(screen.getByLabelText('Clone on GitHub'));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', {
      source: 'hero_github',
      target: 'github',
    });
  });
});
