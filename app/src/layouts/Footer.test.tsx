import { afterEach, describe, expect, it, vi } from 'vitest';

import { Footer } from 'src/layouts/Footer';
import { render, screen, userEvent } from 'src/test-utils';

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
