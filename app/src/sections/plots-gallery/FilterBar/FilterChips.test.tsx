import { fireEvent } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  FilterChips,
  type FilterChipsProps,
} from 'src/sections/plots-gallery/FilterBar/FilterChips';
import { render, screen } from 'src/test-utils';

const callbacks = {
  onChipClick: vi.fn(),
  onChipMenuClose: vi.fn(),
  onRemoveValue: vi.fn(),
  onRemoveActiveGroup: vi.fn(),
  onAddValueToActiveGroup: vi.fn(),
  onRemoveGroup: vi.fn(),
};

function renderChips(overrides: Partial<FilterChipsProps> = {}) {
  return render(
    <FilterChips
      activeFilters={[{ category: 'lib', values: ['matplotlib'] }]}
      randomAnimation={null}
      orCounts={[]}
      currentTotal={100}
      chipMenuAnchor={null}
      activeGroupIndex={null}
      {...callbacks}
      {...overrides}
    />
  );
}

describe('FilterChips', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders one chip per group with category:values label', () => {
    renderChips({
      activeFilters: [
        { category: 'lib', values: ['matplotlib', 'seaborn'] },
        { category: 'plot', values: ['scatter'] },
      ],
    });
    expect(screen.getByText('lib:matplotlib,seaborn')).toBeInTheDocument();
    expect(screen.getByText('plot:scatter')).toBeInTheDocument();
  });

  it('shows the old label during the out phase of the random animation', () => {
    renderChips({
      randomAnimation: { index: 0, phase: 'out', oldLabel: 'lib:plotly' },
    });
    expect(screen.getByText('lib:plotly')).toBeInTheDocument();
    expect(screen.queryByText('lib:matplotlib')).not.toBeInTheDocument();
  });

  it('shows the new label during the in phase of the random animation', () => {
    renderChips({
      randomAnimation: { index: 0, phase: 'in', oldLabel: 'lib:plotly' },
    });
    expect(screen.getByText('lib:matplotlib')).toBeInTheDocument();
  });

  it('calls onChipClick with the group index when a chip is clicked', () => {
    renderChips();
    fireEvent.click(screen.getByText('lib:matplotlib'));
    expect(callbacks.onChipClick).toHaveBeenCalledWith(expect.anything(), 0);
  });

  it('calls onRemoveGroup when the chip delete icon is clicked', () => {
    renderChips();
    const deleteIcon = document.querySelector('.MuiChip-deleteIcon');
    expect(deleteIcon).toBeTruthy();
    fireEvent.click(deleteIcon as Element);
    expect(callbacks.onRemoveGroup).toHaveBeenCalledWith(0);
  });

  describe('chip action menu', () => {
    const menuProps: Partial<FilterChipsProps> = {
      activeFilters: [{ category: 'lib', values: ['matplotlib', 'seaborn'] }],
      orCounts: [{ plotly: 20 }],
      currentTotal: 100,
      chipMenuAnchor: document.createElement('div'),
      activeGroupIndex: 0,
    };

    beforeEach(() => {
      document.body.appendChild(menuProps.chipMenuAnchor as HTMLElement);
    });

    it('offers OR additions with preview counts', () => {
      renderChips(menuProps);
      expect(screen.getByText('add (or)')).toBeInTheDocument();
      expect(screen.getByText('plotly')).toBeInTheDocument();
      expect(screen.getByText('(120)')).toBeInTheDocument(); // currentTotal + orCount

      fireEvent.click(screen.getByText('plotly'));
      expect(callbacks.onAddValueToActiveGroup).toHaveBeenCalledWith('plotly');
    });

    it('offers removing individual values', () => {
      renderChips(menuProps);
      fireEvent.click(screen.getByText('matplotlib'));
      expect(callbacks.onRemoveValue).toHaveBeenCalledWith('matplotlib');
    });

    it('offers remove all only for multi-value groups', () => {
      renderChips(menuProps);
      fireEvent.click(screen.getByText('remove all'));
      expect(callbacks.onRemoveActiveGroup).toHaveBeenCalled();
    });

    it('hides remove all for single-value groups', () => {
      renderChips({
        ...menuProps,
        activeFilters: [{ category: 'lib', values: ['matplotlib'] }],
        orCounts: [{}],
      });
      expect(screen.queryByText('remove all')).not.toBeInTheDocument();
    });
  });
});
