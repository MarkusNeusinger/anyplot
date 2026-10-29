import { describe, expect, it } from 'vitest';

import type { MapLink } from 'src/pages/MapPage.helpers';
import { colors } from 'src/theme';

import { linkEndId, strokeFor } from './MapPage.utils';

describe('linkEndId', () => {
  it('returns string if end is string', () => {
    expect(linkEndId('node-1')).toBe('node-1');
  });

  it('returns id if end is an object with id', () => {
    expect(linkEndId({ id: 'node-2' } as unknown as MapLink['source'])).toBe('node-2');
  });

  it('returns undefined if end is an object without id', () => {
    expect(linkEndId({} as unknown as MapLink['source'])).toBeUndefined();
  });
});

describe('strokeFor', () => {
  it('returns hover color (or primary) when hovered', () => {
    expect(strokeFor(false, true, '#ff0000')).toBe('#ff0000');
    expect(strokeFor(false, true, null)).toBe(colors.primary);
  });

  it('returns node color when not hovered but color is provided', () => {
    expect(strokeFor(false, false, '#00ff00')).toBe('#00ff00');
  });

  it('returns neutral hairline for dark mode when no color provided', () => {
    expect(strokeFor(true, false, null)).toBe('rgba(240,239,232,0.18)');
  });

  it('returns neutral hairline for light mode when no color provided', () => {
    expect(strokeFor(false, false, null)).toBe('rgba(26,26,23,0.18)');
  });
});
