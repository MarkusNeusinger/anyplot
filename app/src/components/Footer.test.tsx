import { describe, it, expect, vi } from 'vitest';
import { render, screen, userEvent } from '../test-utils';
import { Footer } from './Footer';

describe('Footer', () => {
  it('renders footer links', () => {
    render(<Footer />);

    expect(screen.getByText('github')).toBeInTheDocument();
    expect(screen.getByText('stats')).toBeInTheDocument();
    expect(screen.getByText('legal')).toBeInTheDocument();
    expect(screen.getByText('mcp')).toBeInTheDocument();
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

  it('calls onTrackEvent when clicking stats link', async () => {
    const onTrackEvent = vi.fn();
    const user = userEvent.setup();

    render(<Footer onTrackEvent={onTrackEvent} />);

    await user.click(screen.getByText('stats'));
    expect(onTrackEvent).toHaveBeenCalledWith('internal_link', expect.objectContaining({ destination: 'stats' }));
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

  it('calls onTrackEvent when clicking mcp link', async () => {
    const onTrackEvent = vi.fn();
    const user = userEvent.setup();

    render(<Footer onTrackEvent={onTrackEvent} />);

    await user.click(screen.getByText('mcp'));
    expect(onTrackEvent).toHaveBeenCalledWith('internal_link', expect.objectContaining({ destination: 'mcp' }));
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

  it('renders github link with correct href', () => {
    render(<Footer />);

    const githubLink = screen.getByText('github').closest('a');
    expect(githubLink).toHaveAttribute('href', 'https://github.com/MarkusNeusinger/anyplot');
    expect(githubLink).toHaveAttribute('target', '_blank');
    expect(githubLink).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('renders mcp as internal router link to /mcp', () => {
    render(<Footer />);

    const mcpLink = screen.getByText('mcp').closest('a');
    expect(mcpLink).toHaveAttribute('href', '/mcp');
  });

  it('renders legal as internal router link to /legal', () => {
    render(<Footer />);

    const legalLink = screen.getByText('legal').closest('a');
    expect(legalLink).toHaveAttribute('href', '/legal');
  });
});
