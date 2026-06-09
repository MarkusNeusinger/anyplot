import { beforeEach, describe, expect, it, vi } from 'vitest';

import { render, screen, userEvent } from 'src/test-utils';

const trackEvent = vi.fn();

vi.mock('src/hooks', async () => {
  const actual = await vi.importActual<typeof import('src/hooks')>('src/hooks');
  return {
    ...actual,
    useAnalytics: () => ({ trackEvent, trackPageview: vi.fn() }),
  };
});

import { SectionHeader } from 'src/components/SectionHeader';

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
    expect(trackEvent).toHaveBeenCalledWith('nav_click', {
      source: 'section_header',
      target: '/specs',
    });
  });

  it('renders an external link and tracks external_link with the hostname', async () => {
    const user = userEvent.setup();
    render(
      <SectionHeader
        prompt="❯"
        title="visitors"
        linkText="plausible.view()"
        linkHref="https://plausible.io/anyplot.ai"
      />
    );

    const link = screen.getByText('plausible.view()');
    expect(link).toHaveAttribute('href', 'https://plausible.io/anyplot.ai');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');

    await user.click(link);
    expect(trackEvent).toHaveBeenCalledWith('external_link', {
      source: 'section_header',
      destination: 'plausible.io',
    });
  });
});
