import { afterEach, describe, expect, it, vi } from 'vitest';

import { Footer } from 'src/layouts/Footer';
import { render, screen, styleAt, userEvent } from 'src/test-utils';

const ENTRIES = ['github', 'mcp', 'markus neusinger', 'about', 'legal'];

const ONE_ROW = ['github · mcp · markus neusinger · about · legal'];
const TWO_ROWS = ['github · mcp · about · legal', 'markus neusinger'];
const PAIRS = ['github · mcp', 'about · legal', 'markus neusinger'];

// The test environment's handle on its document: the analytics hook sends only on anyplot.ai.
declare const jsdom: { reconfigure: (options: { url: string }) => void };

function renderFooter() {
  const { container } = render(<Footer />);
  return container.querySelector('footer')!;
}

// The declarations at a width and a default font size. The footer has no container query and no
// pseudo-element to read, so those two arguments of the helper stay unset.
const styleFor = (el: Element, width: number, fontSize: number) =>
  styleAt(el, width, undefined, undefined, fontSize);

// Whether an element shows at a width and default font size: no ancestor up to the footer is
// display: none.
function shown(el: Element, footer: Element, width: number, fontSize: number) {
  for (let node: Element | null = el; node; node = node.parentElement) {
    if (styleFor(node, width, fontSize).display === 'none') return false;
    if (node === footer) return true;
  }
  return true;
}

// The footer's lines as the eye reads them: the shown children in DOM order, where a child with
// a 100% flex basis takes a line of its own and the others share one. The bounds in Footer.tsx
// keep a shared line narrower than the footer, so it never wraps by itself.
function lines(footer: Element, width: number, fontSize = 16) {
  const words = (el: Element): string[] =>
    el.children.length === 0
      ? [el.textContent!.trim()]
      : Array.from(el.children)
          .filter(child => shown(child, footer, width, fontSize))
          .flatMap(words);
  const out: string[][] = [];
  let current: string[] | null = null;
  for (const child of Array.from(footer.children)) {
    if (!shown(child, footer, width, fontSize)) continue;
    if (styleFor(child, width, fontSize).flexBasis === '100%') {
      out.push(words(child));
      current = null;
    } else {
      if (!current) out.push((current = []));
      current.push(...words(child));
    }
  }
  return out.map(line => line.join(' '));
}

// The links a keyboard and a screen reader reach, in DOM order.
function reachable(footer: Element, width: number, fontSize = 16) {
  return Array.from(footer.querySelectorAll('a'))
    .filter(a => shown(a, footer, width, fontSize))
    .map(a => a.textContent);
}

describe('Footer', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    jsdom.reconfigure({ url: 'http://localhost:3000/' });
  });

  // Keyboard and screen-reader order follow the DOM, so the DOM carries the order the eye reads
  // in every layout, and no CSS `order` or reversed direction reshuffles it at any width.
  it('reads the entries in the order they show, in each layout', () => {
    const footer = renderFooter();

    for (const [width, fontSize, layout] of [
      [320, 20, PAIRS],
      [390, 24, PAIRS],
      [320, 16, TWO_ROWS],
      [390, 16, TWO_ROWS],
      [719, 16, TWO_ROWS],
      [899, 20, TWO_ROWS],
      [720, 16, ONE_ROW],
      [1440, 16, ONE_ROW],
    ] as const) {
      expect(lines(footer, width, fontSize)).toEqual(layout);
      expect(reachable(footer, width, fontSize)).toEqual(layout.flatMap(line => line.split(' · ')));
    }
    for (const el of [footer, ...Array.from(footer.querySelectorAll('*'))]) {
      for (const width of [320, 390, 600, 719, 720, 900, 1440]) {
        const style = styleAt(el, width);
        expect(style.order).toBe('');
        expect(style.flexDirection).not.toMatch(/reverse/);
        expect(style.flexWrap).not.toBe('wrap-reverse');
      }
    }
  });

  // One copy stands in the middle of the single row, the other on the line below the links; the
  // one that does not belong to the layout must leave the tab order and the accessibility tree,
  // which display: none does and visibility or opacity tricks do not.
  it('shows one copy of the name in each layout and hides the other with display: none', () => {
    const footer = renderFooter();

    const [inRow, onOwnLine] = screen
      .getAllByText('markus neusinger')
      .map(link => link.parentElement!);
    expect(inRow.previousElementSibling).toHaveTextContent('·');
    expect(inRow.nextElementSibling).toHaveTextContent('·');
    expect(onOwnLine).toBe(footer.lastElementChild);

    for (const [width, fontSize] of [
      [320, 16],
      [390, 16],
      [600, 16],
      [719, 16],
      [320, 24],
      [899, 20],
      [1079, 24],
    ]) {
      expect(styleFor(inRow, width, fontSize).display).toBe('none');
      expect(styleFor(onOwnLine, width, fontSize).display).not.toBe('none');
    }
    for (const [width, fontSize] of [
      [720, 16],
      [900, 20],
      [1080, 24],
      [1440, 16],
    ]) {
      expect(styleFor(inRow, width, fontSize).display).toBe('inline');
      expect(styleFor(onOwnLine, width, fontSize).display).toBe('none');
    }
  });

  // At the 16px default font size, the single row would run under the scroll-to-top button below
  // 720px, and nothing lifts that button from 600px up. The row's text grows with the browser's
  // default font size and the corner buttons do not, so a larger default needs a wider screen
  // before the row fits beside them; a smaller one never brings the row in below 720px, where its
  // px gaps would still reach the button.
  it('takes one row from 720px and 45em, and two rows below', () => {
    const footer = renderFooter();

    expect(lines(footer, 719)).toEqual(TWO_ROWS);
    expect(lines(footer, 720)).toEqual(ONE_ROW);
    for (const width of [720, 780, 899]) expect(lines(footer, width, 20)).toEqual(TWO_ROWS);
    for (const width of [900, 1440]) expect(lines(footer, width, 20)).toEqual(ONE_ROW);
    expect(lines(footer, 1079, 24)).toEqual(TWO_ROWS);
    expect(lines(footer, 1080, 24)).toEqual(ONE_ROW);
    for (const width of [600, 719]) expect(lines(footer, width, 13)).toEqual(TWO_ROWS);
    expect(lines(footer, 720, 13)).toEqual(ONE_ROW);
  });

  // The four links' line is 270px wide at the default and fits a 320px phone; its text grows
  // with a larger default and its gaps do not, so from 304px and 19em the links share a line,
  // and below that they break as their pairs with no separator left at a line's end.
  it('keeps the four links on one line from 304px and 19em, and in pairs below', () => {
    const footer = renderFooter();

    expect(lines(footer, 303)).toEqual(PAIRS);
    for (const width of [304, 320]) expect(lines(footer, width)).toEqual(TWO_ROWS);
    for (const width of [320, 375, 379]) expect(lines(footer, width, 20)).toEqual(PAIRS);
    for (const width of [380, 390]) expect(lines(footer, width, 20)).toEqual(TWO_ROWS);
    for (const width of [320, 414, 455]) expect(lines(footer, width, 24)).toEqual(PAIRS);
    for (const width of [456, 480]) expect(lines(footer, width, 24)).toEqual(TWO_ROWS);
    expect(lines(footer, 303, 13)).toEqual(PAIRS);
    expect(lines(footer, 304, 13)).toEqual(TWO_ROWS);
  });

  // Issues are filed from GitHub itself or from a spec page's suggestion link.
  it('has no report entry', () => {
    const footer = renderFooter();

    expect(footer.textContent).not.toMatch(/report/i);
    for (const a of Array.from(footer.querySelectorAll('a'))) {
      expect(a.getAttribute('href')).not.toContain('/issues/new');
    }
  });

  it('sends no event for any entry: the tracker script counts the outbound ones itself', async () => {
    jsdom.reconfigure({ url: 'https://anyplot.ai/' });
    const plausible = vi.fn();
    vi.stubGlobal('plausible', plausible);
    const user = userEvent.setup();
    const footer = renderFooter();

    for (const a of Array.from(footer.querySelectorAll('a'))) {
      await user.click(a);
    }

    expect(footer.querySelectorAll('a')).toHaveLength(ENTRIES.length + 1);
    expect(plausible).not.toHaveBeenCalled();
  });

  it('links github to the repository in a new tab', () => {
    render(<Footer />);

    const githubLink = screen.getByRole('link', { name: 'github' });
    expect(githubLink).toHaveAttribute('href', 'https://github.com/MarkusNeusinger/anyplot');
    expect(githubLink).toHaveAttribute('target', '_blank');
    expect(githubLink).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('links mcp to /mcp inside the site', () => {
    render(<Footer />);

    const mcpLink = screen.getByRole('link', { name: 'mcp' });
    expect(mcpLink).toHaveAttribute('href', '/mcp');
    expect(mcpLink).not.toHaveAttribute('target');
  });

  it('links both copies of the name to LinkedIn in a new tab', () => {
    render(<Footer />);

    const nameLinks = screen.getAllByText('markus neusinger');
    expect(nameLinks).toHaveLength(2);
    for (const nameLink of nameLinks) {
      expect(nameLink.tagName).toBe('A');
      expect(nameLink).toHaveAttribute('href', 'https://www.linkedin.com/in/markus-neusinger/');
      expect(nameLink).toHaveAttribute('target', '_blank');
      expect(nameLink).toHaveAttribute('rel', 'noopener noreferrer');
    }
  });

  it('links about to /about inside the site', () => {
    render(<Footer />);

    const aboutLink = screen.getByRole('link', { name: 'about' });
    expect(aboutLink).toHaveAttribute('href', '/about');
    expect(aboutLink).not.toHaveAttribute('target');
  });

  it('links legal to /legal inside the site', () => {
    render(<Footer />);

    const legalLink = screen.getByRole('link', { name: 'legal' });
    expect(legalLink).toHaveAttribute('href', '/legal');
    expect(legalLink).not.toHaveAttribute('target');
  });
});
