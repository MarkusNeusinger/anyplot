import { describe, expect, it } from 'vitest';

import { langFromPath, paths, RESERVED_TOP_LEVEL, specPath } from 'src/routes/paths';

describe('specPath', () => {
  it('builds the cross-language hub path', () => {
    expect(specPath('scatter-basic')).toBe('/scatter-basic');
  });

  it('builds the language overview path', () => {
    expect(specPath('scatter-basic', 'python')).toBe('/scatter-basic/python');
  });

  it('builds the implementation detail path', () => {
    expect(specPath('scatter-basic', 'python', 'matplotlib')).toBe(
      '/scatter-basic/python/matplotlib'
    );
  });

  it('ignores library without language', () => {
    expect(specPath('scatter-basic', undefined, 'matplotlib')).toBe('/scatter-basic');
  });
});

describe('langFromPath', () => {
  it('returns the language segment of a spec path', () => {
    expect(langFromPath('/scatter-basic/python')).toBe('python');
  });

  it('returns undefined for single-segment paths', () => {
    expect(langFromPath('/scatter-basic')).toBeUndefined();
  });

  it('returns undefined when the first segment is a reserved route', () => {
    expect(langFromPath('/plots/python')).toBeUndefined();
  });
});

describe('paths registry', () => {
  it('exposes every static route', () => {
    expect(paths.home).toBe('/');
    expect(paths.plots).toBe('/plots');
    expect(paths.specs).toBe('/specs');
    expect(paths.libraries).toBe('/libraries');
    expect(paths.map).toBe('/map');
    expect(paths.palette).toBe('/palette');
    expect(paths.about).toBe('/about');
    expect(paths.legal).toBe('/legal');
    expect(paths.mcp).toBe('/mcp');
    expect(paths.stats).toBe('/stats');
    expect(paths.debug).toBe('/debug');
  });

  it('every static route is a reserved top-level slug', () => {
    const staticRoutes = [
      paths.plots,
      paths.specs,
      paths.libraries,
      paths.map,
      paths.palette,
      paths.about,
      paths.legal,
      paths.mcp,
      paths.stats,
      paths.debug,
    ];
    for (const route of staticRoutes) {
      expect(RESERVED_TOP_LEVEL.has(route.slice(1))).toBe(true);
    }
  });

  it('builds encoded plots filter URLs', () => {
    expect(paths.plotsFiltered('lib', 'ggplot2')).toBe('/plots?lib=ggplot2');
    expect(paths.plotsFiltered('plot', 'scatter plot')).toBe('/plots?plot=scatter%20plot');
  });

  it('exposes specPath as paths.spec', () => {
    expect(paths.spec('heatmap-basic', 'r', 'ggplot2')).toBe('/heatmap-basic/r/ggplot2');
  });
});
