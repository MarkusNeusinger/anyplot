import { afterEach, describe, expect, it, vi } from 'vitest';

import { Footer } from 'src/layouts/Footer';
import { render, screen, styleAt, userEvent } from 'src/test-utils';

describe('Footer', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders footer links', () => {
    render(<Footer />);

    expect(screen.getByText('github')).toBeInTheDocument();
    expect(screen.getByText('report')).toBeInTheDocument();
    expect(screen.getByText('mcp')).toBeInTheDocument();
    expect(screen.getByText('about')).toBeInTheDocument();
    expect(screen.getByText('legal')).toBeInTheDocument();
  });

  it('renders markus neusinger link', () => {
    render(<Footer />);

    expect(screen.getByText('markus neusinger')).toBeInTheDocument();
  });

  // Keyboard and screen-reader order follow the DOM, so the DOM carries the order the eye reads,
  // and no CSS `order` reshuffles it at any width.
  it('reads in the order it shows, the name last', () => {
    const { container } = render(<Footer />);

    const footer = container.querySelector('footer')!;
    expect(Array.from(footer.querySelectorAll('a')).map(a => a.textContent)).toEqual([
      'github',
      'report',
      'mcp',
      'about',
      'legal',
      'markus neusinger',
    ]);
    for (const el of Array.from(footer.querySelectorAll('*'))) {
      for (const width of [320, 399, 400, 600, 899, 900, 1440]) {
        expect(styleAt(el, width).order).toBe('');
      }
    }
  });

  it('shows the name at every width, on a line of its own below md', () => {
    render(<Footer />);

    const link = screen.getByRole('link', { name: 'markus neusinger' });
    expect(link).toHaveAttribute('href', 'https://www.linkedin.com/in/markus-neusinger/');
    const footer = link.closest('footer')!;
    for (const width of [320, 390, 600, 900, 1440]) {
      for (let el: Element | null = link; el && el !== footer; el = el.parentElement) {
        expect(styleAt(el, width).display).not.toBe('none');
      }
    }
    // Below md the separator before the name goes and the name fills a line, so no row ends on a
    // "·" and the row of links stays clear of the floating buttons (useFooterLift lifts them only
    // below 600px; with MonoLisa at 600px the row ends at x=478, the button starts at x=536).
    const line = link.parentElement!;
    const separatorBeforeName = line.previousElementSibling!;
    expect(separatorBeforeName).toHaveTextContent('·');
    for (const width of [320, 390, 600, 899]) {
      expect(styleAt(line, width).flexBasis).toBe('100%');
      expect(styleAt(separatorBeforeName, width).display).toBe('none');
    }
    expect(styleAt(line, 900).flexBasis).toBe('auto');
    expect(styleAt(separatorBeforeName, 900).display).toBe('inline');
  });

  // The five links need 356px in one row with MonoLisa at 14px, so below 400px the site's own
  // pages take a row of their own instead of the row breaking before "legal" after a "·".
  it('gives the site pages a row of their own below 400px', () => {
    render(<Footer />);

    const group = screen.getByRole('link', { name: 'mcp' }).parentElement!;
    expect(group).toContainElement(screen.getByRole('link', { name: 'legal' }));
    const separatorBeforeGroup = group.previousElementSibling!;
    expect(separatorBeforeGroup).toHaveTextContent('·');
    for (const width of [320, 390, 399]) {
      expect(styleAt(group, width).display).toBe('flex');
      expect(styleAt(group, width).flexBasis).toBe('100%');
      expect(styleAt(separatorBeforeGroup, width).display).toBe('none');
    }
    for (const width of [400, 600, 1440]) {
      expect(styleAt(group, width).display).toBe('contents');
      expect(styleAt(separatorBeforeGroup, width).display).not.toBe('none');
    }
  });

  it('sends no event for a link: the tracker script counts the outbound ones itself', async () => {
    const plausible = vi.fn();
    vi.stubGlobal('plausible', plausible);
    const user = userEvent.setup();
    render(<Footer />);

    await user.click(screen.getByText('mcp'));
    await user.click(screen.getByText('about'));
    await user.click(screen.getByText('legal'));

    expect(plausible).not.toHaveBeenCalled();
  });

  it('renders github link to repo home', () => {
    render(<Footer />);

    const githubLink = screen.getByText('github').closest('a');
    expect(githubLink).toHaveAttribute('href', 'https://github.com/MarkusNeusinger/anyplot');
    expect(githubLink).toHaveAttribute('target', '_blank');
    expect(githubLink).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('renders report link to issue chooser', () => {
    render(<Footer />);

    const reportLink = screen.getByText('report').closest('a');
    expect(reportLink).toHaveAttribute(
      'href',
      'https://github.com/MarkusNeusinger/anyplot/issues/new/choose'
    );
    expect(reportLink).toHaveAttribute('target', '_blank');
  });

  it('renders mcp as internal router link to /mcp', () => {
    render(<Footer />);

    const mcpLink = screen.getByText('mcp').closest('a');
    expect(mcpLink).toHaveAttribute('href', '/mcp');
    expect(mcpLink).not.toHaveAttribute('target');
  });

  it('renders about as internal router link to /about', () => {
    render(<Footer />);

    const aboutLink = screen.getByText('about').closest('a');
    expect(aboutLink).toHaveAttribute('href', '/about');
  });

  it('renders legal as internal router link to /legal', () => {
    render(<Footer />);

    const legalLink = screen.getByText('legal').closest('a');
    expect(legalLink).toHaveAttribute('href', '/legal');
  });
});
