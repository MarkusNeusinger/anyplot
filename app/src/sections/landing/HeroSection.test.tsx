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

import {
  AGENT_ENTRY_LABEL,
  AGENT_ENTRY_NAME,
  AGENT_ENTRY_TEXT,
  HeroSection,
} from 'src/sections/landing/HeroSection';

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

  it('names the agent in plain words only while the public lane is open, leading to /agent', async () => {
    const user = userEvent.setup();
    const { rerender } = render(<HeroSection potd={null} />);
    expect(screen.queryByRole('link', { name: AGENT_ENTRY_LABEL })).not.toBeInTheDocument();
    expect(screen.queryByText(AGENT_ENTRY_TEXT)).not.toBeInTheDocument();

    lane.open = true;
    rerender(<HeroSection potd={null} />);
    const link = screen.getByRole('link', { name: AGENT_ENTRY_LABEL });
    // The idiom and the plain words, both inside the one link.
    expect(link).toHaveTextContent(`${AGENT_ENTRY_NAME} →`);
    expect(link).toHaveTextContent(AGENT_ENTRY_TEXT);
    // The accessible name keeps the words on screen (WCAG 2.5.3).
    expect(AGENT_ENTRY_LABEL.toLowerCase()).toContain(AGENT_ENTRY_TEXT);
    // A decision of the launch: the chat's notice says "experimental", the hero does not.
    expect(link).not.toHaveTextContent(/experimental/i);
    expect(link).toHaveAttribute('href', '/agent');

    await user.click(link);
    expect(trackEvent).toHaveBeenCalledWith('nav_click', {
      source: 'hero_use_my_data',
      target: '/agent',
    });
  });

  it("keeps the entry's box while the lane probe is pending: invisible, unreachable, untracked", async () => {
    const user = userEvent.setup();
    lane.open = null;
    const { rerender } = render(<HeroSection potd={null} />);
    // The box holds the same two lines as the link, so the link takes its place without a move.
    const box = screen.getByTestId('hero-agent-entry');
    expect(box).toHaveTextContent(`${AGENT_ENTRY_NAME} →`);
    expect(box).toHaveTextContent(AGENT_ENTRY_TEXT);
    expect(box).toHaveStyle({ visibility: 'hidden' });
    expect(box).toHaveAttribute('aria-hidden', 'true');
    // No link: nothing to follow, focus or name.
    expect(box.tagName).toBe('SPAN');
    expect(box).not.toHaveAttribute('href');
    expect(box).not.toHaveAttribute('tabindex');
    expect(screen.queryByRole('link', { name: AGENT_ENTRY_LABEL })).not.toBeInTheDocument();
    expect(screen.queryByText(AGENT_ENTRY_TEXT)?.closest('a')).toBeNull();
    // Tabbing through the hero never stops on it.
    const stops: (Element | null)[] = [];
    for (let i = 0; i < 6; i += 1) {
      await user.tab();
      stops.push(document.activeElement);
    }
    expect(stops.some(el => el !== null && box.contains(el))).toBe(false);
    await user.click(box);
    expect(trackEvent).not.toHaveBeenCalled();

    // The lane answers open: the link stands in the box's place.
    lane.open = true;
    rerender(<HeroSection potd={null} />);
    const link = screen.getByRole('link', { name: AGENT_ENTRY_LABEL });
    expect(link).toHaveAttribute('data-testid', 'hero-agent-entry');
    expect(link).toHaveStyle({ visibility: 'visible' });
    expect(link).not.toHaveAttribute('aria-hidden');
  });

  it('removes the box when the lane answers closed', () => {
    lane.open = null;
    const { rerender } = render(<HeroSection potd={null} />);
    expect(screen.getByTestId('hero-agent-entry')).toBeInTheDocument();

    lane.open = false;
    rerender(<HeroSection potd={null} />);
    expect(screen.queryByTestId('hero-agent-entry')).not.toBeInTheDocument();
    expect(screen.queryByText(AGENT_ENTRY_TEXT)).not.toBeInTheDocument();
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

  it('keeps the name on one line, underlined on hover only, padded on phones and ringed around the name', () => {
    render(<HeroSection potd={null} />);

    const link = emotionClass(screen.getByRole('link', { name: 'Markus Neusinger' }));
    const css = styles();
    // The name never splits across lines.
    expect(css).toMatch(new RegExp(`\\.${link}\\{[^}]*white-space:nowrap;`));
    // No underline at rest: the border is there but transparent, so hover moves nothing.
    expect(css).toMatch(
      new RegExp(`\\.${link}>span\\{[^}]*border-bottom:[^;]*dotted transparent;`)
    );
    expect(css).not.toMatch(new RegExp(`\\.${link}\\{[^}]*text-decoration:underline`));
    // Hover shows it, in the colour the name takes then.
    expect(css).toMatch(
      new RegExp(`\\.${link}:hover>span\\{[^}]*border-bottom-color:currentColor;`)
    );
    // Below sm (600 px) padding grows the touch target and an equal negative margin keeps the
    // text in place; from sm up both are reset.
    const phone = new RegExp(`@media \\(min-width: ?0px\\)\\{\\.${link}\\{([^}]*)\\}\\}`).exec(css);
    if (!phone) throw new Error('the link has no padding below sm');
    const padding = /(?:^|;)padding:([^;]+);/.exec(phone[1])?.[1];
    expect(padding).toMatch(/^[1-9][\d.]*px$/);
    expect(phone[1]).toContain(`margin:-${padding};`);
    expect(css).toMatch(
      new RegExp(
        `@media \\(min-width: ?600px\\)\\{\\.${link}\\{padding:0(?:px)?;margin:0(?:px)?;\\}\\}`
      )
    );
    // The keyboard gets the hero's own ring, drawn on the name rather than the padded box.
    expect(css).toMatch(new RegExp(`\\.${link}:focus-visible\\{outline:none;\\}`));
    const cta = emotionClass(screen.getByLabelText('Browse plots'));
    const heroRing = new RegExp(`\\.${cta}:focus-visible\\{([^}]*)\\}`).exec(css)?.[1];
    if (!heroRing) throw new Error('the browse link has no focus ring');
    const nameRing = new RegExp(`\\.${link}:focus-visible>span\\{([^}]*)\\}`).exec(css)?.[1];
    if (!nameRing) throw new Error('the name has no focus ring');
    for (const declaration of heroRing.split(';').filter(Boolean)) {
      expect(nameRing).toContain(`${declaration};`);
    }
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

    const mcp = screen.getByRole('link', { name: 'Connect via MCP' });
    expect(mcp).toHaveAttribute('href', '/mcp');
    await user.click(mcp);
    expect(trackEvent).toHaveBeenCalledWith('nav_click', { source: 'hero_mcp', target: '/mcp' });

    await user.click(screen.getByLabelText('Clone on GitHub'));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', {
      source: 'hero_github',
      target: 'github',
    });
  });
});
