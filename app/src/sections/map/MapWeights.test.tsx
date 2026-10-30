import { useState } from 'react';

import { afterEach, describe, expect, it, vi } from 'vitest';

import { DEFAULT_CATEGORY_WEIGHT, TAG_CATEGORIES } from 'src/pages/MapPage.helpers';
import { fireEvent, render, screen } from 'src/test-utils';

import { MapWeights } from './MapWeights';

describe('MapWeights', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('starts collapsed and opens on toggle click to show all category sliders and threshold', () => {
    render(
      <MapWeights
        weights={{ ...DEFAULT_CATEGORY_WEIGHT }}
        setWeights={vi.fn()}
        minSim={0.15}
        setMinSim={vi.fn()}
        resetWeights={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: 'weights ▸' })).toBeInTheDocument();
    expect(screen.queryAllByRole('slider')).toHaveLength(0);
    expect(screen.queryByRole('button', { name: 'reset' })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'weights ▸' }));

    expect(screen.getByRole('button', { name: 'weights ▾' })).toBeInTheDocument();
    expect(screen.getAllByRole('slider')).toHaveLength(TAG_CATEGORIES.length + 1);
    for (const cat of TAG_CATEGORIES) {
      expect(screen.getByText(cat)).toBeInTheDocument();
    }
    expect(screen.getByText('threshold')).toBeInTheDocument();
    expect(screen.getByText('2.0')).toBeInTheDocument();
    expect(screen.getByText('0.15')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'weights ▾' }));
    expect(screen.queryAllByRole('slider')).toHaveLength(0);
  });

  it('calls setWeights, setMinSim, and resetWeights when controls are used', () => {
    const setWeightsSpy = vi.fn();
    const setMinSimSpy = vi.fn();
    const resetWeightsSpy = vi.fn();

    function Harness() {
      const [weights, setWeights] = useState<Record<string, number>>({
        ...DEFAULT_CATEGORY_WEIGHT,
      });
      const [minSim, setMinSim] = useState(0.15);
      return (
        <MapWeights
          weights={weights}
          setWeights={updater => {
            setWeightsSpy(updater);
            setWeights(updater);
          }}
          minSim={minSim}
          setMinSim={val => {
            setMinSimSpy(val);
            setMinSim(val);
          }}
          resetWeights={resetWeightsSpy}
        />
      );
    }

    render(<Harness />);
    fireEvent.click(screen.getByRole('button', { name: 'weights ▸' }));

    const sliders = screen.getAllByRole('slider');
    // First slider corresponds to plot_type (first entry in TAG_CATEGORIES)
    fireEvent.change(sliders[0], { target: { value: '3.5' } });
    expect(setWeightsSpy).toHaveBeenCalled();
    expect(screen.getByText('3.5')).toBeInTheDocument();

    // Last slider corresponds to the edge threshold
    fireEvent.change(sliders[sliders.length - 1], { target: { value: '0.25' } });
    expect(setMinSimSpy).toHaveBeenCalledWith(0.25);
    expect(screen.getByText('0.25')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'reset' }));
    expect(resetWeightsSpy).toHaveBeenCalledTimes(1);
  });
});
