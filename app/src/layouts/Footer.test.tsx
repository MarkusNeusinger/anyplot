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
    // On phones it closes the footer, on its own line, so no row ends on a separator.
    const line = link.parentElement!;
    expect(styleAt(line, 390).flexBasis).toBe('100%');
    expect(styleAt(line, 390).order).toBe('1');
    expect(styleAt(line, 600).flexBasis).toBe('auto');
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
