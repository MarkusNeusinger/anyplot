import { describe, it, expect } from 'vitest';
import { createTooltipId, parseTooltipId, isTooltipOpen } from './tooltip';

describe('createTooltipId', () => {
  it('creates spec tooltip ID', () => {
    expect(createTooltipId('spec', 'scatter-basic', 'matplotlib')).toBe('spec-scatter-basic-matplotlib');
  });

  it('creates lib tooltip ID', () => {
    expect(createTooltipId('lib', 'heatmap', 'seaborn')).toBe('lib-heatmap-seaborn');
  });
});

describe('parseTooltipId', () => {
  it('parses valid spec tooltip ID', () => {
    expect(parseTooltipId('spec-scatter-basic-matplotlib')).toEqual({
      type: 'spec',
      specId: 'scatter-basic',
      library: 'matplotlib',
    });
  });

  it('parses valid lib tooltip ID', () => {
    expect(parseTooltipId('lib-heatmap-seaborn')).toEqual({
      type: 'lib',
      specId: 'heatmap',
      library: 'seaborn',
    });
  });

  it('handles multi-hyphen spec IDs', () => {
    expect(parseTooltipId('spec-scatter-color-mapped-plotly')).toEqual({
      type: 'spec',
      specId: 'scatter-color-mapped',
      library: 'plotly',
    });
  });

  it('returns null for too few parts', () => {
    expect(parseTooltipId('spec-only')).toBeNull();
  });

  it('returns null for invalid type', () => {
    expect(parseTooltipId('invalid-scatter-matplotlib')).toBeNull();
  });

  it('returns null for empty string', () => {
    expect(parseTooltipId('')).toBeNull();
  });
});

describe('isTooltipOpen', () => {
  it('returns true when tooltip matches', () => {
    expect(isTooltipOpen('spec-scatter-basic-matplotlib', 'spec', 'scatter-basic', 'matplotlib')).toBe(true);
  });

  it('returns false when tooltip does not match', () => {
    expect(isTooltipOpen('spec-scatter-basic-matplotlib', 'spec', 'heatmap', 'seaborn')).toBe(false);
  });

  it('returns false when openTooltip is null', () => {
    expect(isTooltipOpen(null, 'spec', 'scatter-basic', 'matplotlib')).toBe(false);
  });
});
