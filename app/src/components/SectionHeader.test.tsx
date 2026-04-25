import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, userEvent } from '../test-utils';

const trackEvent = vi.fn();

vi.mock('../hooks', async () => {
  const actual = await vi.importActual<typeof import('../hooks')>('../hooks');
  return {
    ...actual,
    useAnalytics: () => ({ trackEvent, trackPageview: vi.fn() }),
  };
});

import { SectionHeader } from './SectionHeader';

describe('SectionHeader', () => {
  beforeEach(() => {
    trackEvent.mockClear();
  });

  it('renders the title and prompt', () => {
    render(<SectionHeader prompt="❯" title="libraries" />);
    expect(screen.getByText('❯')).toBeInTheDocument();
    expect(screen.getByText('libraries')).toBeInTheDocument();
  });

  it('tracks nav_click when the action link is clicked', async () => {
    const user = userEvent.setup();
    render(<SectionHeader prompt="❯" title="specs" linkText="specs.all()" linkTo="/specs" />);

    await user.click(screen.getByText('specs.all()'));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', { source: 'section_header', target: '/specs' });
  });
});
