import { describe, it, expect } from 'vitest';
import { specPath, langFromPath, specIdFromPath } from './paths';

describe('specPath', () => {
  it('builds hub, language, and detail paths', () => {
    expect(specPath('scatter')).toBe('/scatter');
    expect(specPath('scatter', 'python')).toBe('/scatter/python');
    expect(specPath('scatter', 'python', 'altair')).toBe('/scatter/python/altair');
  });
});

describe('langFromPath', () => {
  it('returns the language segment for a detail path', () => {
    expect(langFromPath('/scatter/python/altair')).toBe('python');
  });

  it('returns undefined when there is no language segment or the root is reserved', () => {
    expect(langFromPath('/scatter')).toBeUndefined();
    expect(langFromPath('/')).toBeUndefined();
    expect(langFromPath('/stats/python')).toBeUndefined();
  });
});

describe('specIdFromPath', () => {
  it('returns the first segment for a spec route', () => {
    expect(specIdFromPath('/scatter')).toBe('scatter');
    expect(specIdFromPath('/scatter/python/altair')).toBe('scatter');
  });

  it('returns undefined for the root path', () => {
    expect(specIdFromPath('/')).toBeUndefined();
    expect(specIdFromPath('')).toBeUndefined();
  });

  it('returns undefined when the first segment is a reserved top-level route', () => {
    expect(specIdFromPath('/stats')).toBeUndefined();
    expect(specIdFromPath('/about/team')).toBeUndefined();
    expect(specIdFromPath('/map')).toBeUndefined();
  });
});
