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
    expect(onTrackEvent).toHaveBeenCalledWith('external_link', expect.objectContaining({ destination: 'stats' }));
  });

  it('renders without onTrackEvent', () => {
    render(<Footer />);
    expect(screen.getByText('github')).toBeInTheDocument();
  });
});
