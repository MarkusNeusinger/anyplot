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
    expect(screen.getByText('about')).toBeInTheDocument();
    expect(screen.getByText('legal')).toBeInTheDocument();
  });

  it('renders markus neusinger link', () => {
    render(<Footer />);

    expect(screen.getByText('markus neusinger')).toBeInTheDocument();
  });

  it('shows the name at every width, on a line of its own on phones', () => {
    render(<Footer />);

    const link = screen.getByRole('link', { name: 'markus neusinger' });
    expect(link).toHaveAttribute('href', 'https://www.linkedin.com/in/markus-neusinger/');
    const footer = link.closest('footer')!;
    for (const width of [320, 390, 600, 900, 1440]) {
      for (let el: Element | null = link; el && el !== footer; el = el.parentElement) {
        expect(styleAt(el, width).display).not.toBe('none');
      }
    }
    // Below md it closes the footer, on its own line, so no row ends on a separator.
    const line = link.parentElement!;
    for (const width of [320, 390, 600, 899]) {
      expect(styleAt(line, width).flexBasis).toBe('100%');
      expect(styleAt(line, width).order).toBe('1');
    }
    expect(styleAt(line, 900).flexBasis).toBe('auto');
    expect(styleAt(line, 900).order).toBe('0');
  });

  // The floating buttons in the bottom-right corner lift above the footer only below 600px
  // (useFooterLift). jsdom lays nothing out, so this pins the layout that keeps the row of links
  // short from 600 to 899px: the name and its separator leave the row, and only the four short
  // links share it. With MonoLisa at 600px that row ends at x=450, left of the button at x=536.
  it('keeps the name out of the row of links up to md, so the row stays clear of the buttons', () => {
    const { container } = render(<Footer />);

    const footer = container.querySelector('footer')!;
    const name = screen.getByRole('link', { name: 'markus neusinger' }).parentElement!;
    const separatorBeforeName = name.previousElementSibling!;
    expect(separatorBeforeName).toHaveTextContent('·');
    for (const width of [600, 700, 899]) {
      expect(styleAt(separatorBeforeName, width).display).toBe('none');
      expect(styleAt(name, width).flexBasis).toBe('100%');
    }
    expect(styleAt(separatorBeforeName, 900).display).toBe('inline');
    expect(footer.querySelectorAll('a')).toHaveLength(5);
  });

  it('sends no event for a link: the tracker script counts the outbound ones itself', async () => {
    const plausible = vi.fn();
    vi.stubGlobal('plausible', plausible);
    const user = userEvent.setup();
    render(<Footer />);

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
