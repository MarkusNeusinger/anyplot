import { describe, it, expect, vi } from 'vitest';
import { render, screen, userEvent } from '../test-utils';
import { PlotsLink, GridSizeToggle, ToolbarActions } from './ToolbarActions';

describe('PlotsLink', () => {
  it('renders a link to /plots', () => {
    render(<PlotsLink />);

    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/plots');
  });

  it('has a "plots" tooltip', async () => {
    const user = userEvent.setup();
    render(<PlotsLink />);

    const link = screen.getByRole('link');
    await user.hover(link);

    expect(await screen.findByText('plots')).toBeInTheDocument();
  });
});

describe('GridSizeToggle', () => {
  const defaultProps = {
    imageSize: 'normal' as const,
    onImageSizeChange: vi.fn(),
    onTrackEvent: vi.fn(),
  };

  it('renders with aria-label for current state', () => {
    render(<GridSizeToggle {...defaultProps} />);

    expect(screen.getByRole('button')).toHaveAttribute(
      'aria-label',
      'Switch to compact view'
    );
  });

  it('shows "Switch to normal view" when in compact mode', () => {
    render(<GridSizeToggle {...defaultProps} imageSize="compact" />);

    expect(screen.getByRole('button')).toHaveAttribute(
      'aria-label',
      'Switch to normal view'
    );
  });

  it('toggles to compact on click and fires tracking event', async () => {
    const onImageSizeChange = vi.fn();
    const onTrackEvent = vi.fn();
    const user = userEvent.setup();

    render(
      <GridSizeToggle
        imageSize="normal"
        onImageSizeChange={onImageSizeChange}
        onTrackEvent={onTrackEvent}
      />
    );

    await user.click(screen.getByRole('button'));

    expect(onImageSizeChange).toHaveBeenCalledWith('compact');
    expect(onTrackEvent).toHaveBeenCalledWith('grid_resize', { size: 'compact' });
  });

  it('toggles to normal when already compact', async () => {
    const onImageSizeChange = vi.fn();
    const user = userEvent.setup();

    render(
      <GridSizeToggle
        {...defaultProps}
        imageSize="compact"
        onImageSizeChange={onImageSizeChange}
      />
    );

    await user.click(screen.getByRole('button'));
    expect(onImageSizeChange).toHaveBeenCalledWith('normal');
  });

  it('responds to Enter key', async () => {
    const onImageSizeChange = vi.fn();
    const user = userEvent.setup();

    render(<GridSizeToggle {...defaultProps} onImageSizeChange={onImageSizeChange} />);

    screen.getByRole('button').focus();
    await user.keyboard('{Enter}');

    expect(onImageSizeChange).toHaveBeenCalledWith('compact');
  });

  it('responds to Space key', async () => {
    const onImageSizeChange = vi.fn();
    const user = userEvent.setup();

    render(<GridSizeToggle {...defaultProps} onImageSizeChange={onImageSizeChange} />);

    screen.getByRole('button').focus();
    await user.keyboard(' ');

    expect(onImageSizeChange).toHaveBeenCalledWith('compact');
  });
});

describe('ToolbarActions', () => {
  it('renders both PlotsLink and GridSizeToggle', () => {
    render(
      <ToolbarActions
        imageSize="normal"
        onImageSizeChange={vi.fn()}
        onTrackEvent={vi.fn()}
      />
    );

    expect(screen.getByRole('link')).toHaveAttribute('href', '/plots');
    expect(screen.getByRole('button')).toBeInTheDocument();
  });
});
