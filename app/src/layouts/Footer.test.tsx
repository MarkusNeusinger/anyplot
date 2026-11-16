import { afterEach, describe, expect, it, vi } from 'vitest';

import { Footer } from 'src/layouts/Footer';
import { render, screen, styleAt, userEvent } from 'src/test-utils';

const ENTRIES = ['github', 'mcp', 'markus neusinger', 'about', 'legal'];

// The test environment's handle on its document: the analytics hook sends only on anyplot.ai.
declare const jsdom: { reconfigure: (options: { url: string }) => void };

describe('Footer', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    jsdom.reconfigure({ url: 'http://localhost:3000/' });
  });

  // Keyboard and screen-reader order follow the DOM, so the DOM carries the order the eye reads,
  // and no CSS `order` reshuffles it at any width.
  it('reads github, mcp, the name, about, legal, in the order it shows', () => {
    const { container } = render(<Footer />);

    const footer = container.querySelector('footer')!;
    expect(Array.from(footer.querySelectorAll('a')).map(a => a.textContent)).toEqual(ENTRIES);
    for (const el of Array.from(footer.querySelectorAll('*'))) {
      for (const width of [320, 390, 600, 719, 720, 900, 1440]) {
        expect(styleAt(el, width).order).toBe('');
      }
    }
  });

  // Issues are filed from GitHub itself or from a spec page's suggestion link.
  it('has no report entry', () => {
    const { container } = render(<Footer />);

    const footer = container.querySelector('footer')!;
    expect(footer.textContent).not.toMatch(/report/i);
    for (const a of Array.from(footer.querySelectorAll('a'))) {
      expect(a.getAttribute('href')).not.toContain('/issues/new');
    }
  });

  // Below 720px the single row would run under the scroll-to-top button, which nothing lifts from
  // 600px up, so the name takes the middle line of three and its two separators go: no line
  // starts or ends on a "·".
  it('puts the name on a line of its own below 720px and keeps one row from 720px', () => {
    render(<Footer />);

    const link = screen.getByRole('link', { name: 'markus neusinger' });
    const footer = link.closest('footer')!;
    const line = link.parentElement!;
    const before = line.previousElementSibling!;
    const after = line.nextElementSibling!;
    expect(before).toHaveTextContent('·');
    expect(after).toHaveTextContent('·');
    const otherSeparators = Array.from(footer.children).filter(
      el => el.textContent === '·' && el !== before && el !== after
    );
    expect(otherSeparators).toHaveLength(2);

    for (const width of [320, 390, 600, 719]) {
      expect(styleAt(line, width).flexBasis).toBe('100%');
      expect(styleAt(before, width).display).toBe('none');
      expect(styleAt(after, width).display).toBe('none');
    }
    for (const width of [720, 900, 1440]) {
      expect(styleAt(line, width).flexBasis).toBe('auto');
      expect(styleAt(before, width).display).toBe('inline');
      expect(styleAt(after, width).display).toBe('inline');
    }
    for (const width of [320, 390, 600, 719, 720, 900, 1440]) {
      for (const el of [...otherSeparators, ...Array.from(footer.querySelectorAll('a'))]) {
        for (let node: Element | null = el; node && node !== footer; node = node.parentElement) {
          expect(styleAt(node, width).display).not.toBe('none');
        }
      }
    }
  });

  it('sends no event for any entry: the tracker script counts the outbound ones itself', async () => {
    jsdom.reconfigure({ url: 'https://anyplot.ai/' });
    const plausible = vi.fn();
    vi.stubGlobal('plausible', plausible);
    const user = userEvent.setup();
    render(<Footer />);

    for (const name of ENTRIES) {
      await user.click(screen.getByRole('link', { name }));
    }

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

  it('links the name to LinkedIn in a new tab', () => {
    render(<Footer />);

    const nameLink = screen.getByRole('link', { name: 'markus neusinger' });
    expect(nameLink).toHaveAttribute('href', 'https://www.linkedin.com/in/markus-neusinger/');
    expect(nameLink).toHaveAttribute('target', '_blank');
    expect(nameLink).toHaveAttribute('rel', 'noopener noreferrer');
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
