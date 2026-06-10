import { describe, expect, it, vi } from 'vitest';

import { FilterSizeToggle } from 'src/sections/plots-gallery/FilterBar/FilterSizeToggle';
import { render, screen, userEvent } from 'src/test-utils';

describe('FilterSizeToggle', () => {
  it('renders the grid size toggle for the current size', () => {
    render(
      <FilterSizeToggle imageSize="normal" onImageSizeChange={vi.fn()} onTrackEvent={vi.fn()} />
    );
    expect(screen.getByRole('button', { name: 'Switch to compact view' })).toBeInTheDocument();
  });

  it('passes size changes and analytics through to the handlers', async () => {
    const onImageSizeChange = vi.fn();
    const onTrackEvent = vi.fn();
    render(
      <FilterSizeToggle
        imageSize="normal"
        onImageSizeChange={onImageSizeChange}
        onTrackEvent={onTrackEvent}
      />
    );

    await userEvent.click(screen.getByRole('button', { name: 'Switch to compact view' }));

    expect(onImageSizeChange).toHaveBeenCalledWith('compact');
    expect(onTrackEvent).toHaveBeenCalledWith('grid_resize', { size: 'compact' });
  });
});
