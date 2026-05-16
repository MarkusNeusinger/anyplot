import { describe, it, expect, vi } from 'vitest';
import { render, screen, userEvent } from '../test-utils';
import { Footer } from './Footer';

describe('Footer', () => {
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

  it('calls onTrackEvent when clicking github link', async () => {
    const onTrackEvent = vi.fn();
    const user = userEvent.setup();

    render(<Footer onTrackEvent={onTrackEvent} />);

    await user.click(screen.getByText('github'));
    expect(onTrackEvent).toHaveBeenCalledWith('external_link', expect.objectContaining({ destination: 'github' }));
  });

  it('calls onTrackEvent when clicking report link', async () => {
    const onTrackEvent = vi.fn();
    const user = userEvent.setup();

    render(<Footer onTrackEvent={onTrackEvent} />);

    await user.click(screen.getByText('report'));
    expect(onTrackEvent).toHaveBeenCalledWith('external_link', expect.objectContaining({ destination: 'github_issue_chooser' }));
  });

  it('renders without onTrackEvent', () => {
    render(<Footer />);
    expect(screen.getByText('github')).toBeInTheDocument();
  });

  it('calls onTrackEvent when clicking linkedin link', async () => {
    const onTrackEvent = vi.fn();
    const user = userEvent.setup();

    render(<Footer onTrackEvent={onTrackEvent} />);

    await user.click(screen.getByText('markus neusinger'));
    expect(onTrackEvent).toHaveBeenCalledWith('external_link', expect.objectContaining({ destination: 'linkedin' }));
  });

  it('calls onTrackEvent when clicking about link', async () => {
    const onTrackEvent = vi.fn();
    const user = userEvent.setup();

    render(<Footer onTrackEvent={onTrackEvent} />);

    await user.click(screen.getByText('about'));
    expect(onTrackEvent).toHaveBeenCalledWith('internal_link', expect.objectContaining({ destination: 'about' }));
  });

  it('calls onTrackEvent when clicking legal link', async () => {
    const onTrackEvent = vi.fn();
    const user = userEvent.setup();

    render(<Footer onTrackEvent={onTrackEvent} />);

    await user.click(screen.getByText('legal'));
    expect(onTrackEvent).toHaveBeenCalledWith('internal_link', expect.objectContaining({ destination: 'legal' }));
  });

  it('passes selectedSpec and selectedLibrary to tracking', async () => {
    const onTrackEvent = vi.fn();
    const user = userEvent.setup();

    render(<Footer onTrackEvent={onTrackEvent} selectedSpec="scatter-basic" selectedLibrary="matplotlib" />);

    await user.click(screen.getByText('github'));
    expect(onTrackEvent).toHaveBeenCalledWith('external_link', {
      destination: 'github',
      spec: 'scatter-basic',
      library: 'matplotlib',
    });
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
    expect(reportLink).toHaveAttribute('href', 'https://github.com/MarkusNeusinger/anyplot/issues/new/choose');
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
