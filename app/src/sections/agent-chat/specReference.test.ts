import { describe, expect, it } from 'vitest';

import { expectedColumns, previewsByLibrary } from 'src/sections/agent-chat/specReference';

describe('expectedColumns', () => {
  it('keeps the column bullets and drops the size and example lines', () => {
    expect(
      expectedColumns([
        '`value` (numeric) - The continuous variable to visualize as density curves',
        '`group` (categorical) - The grouping variable that creates separate ridges',
        'Size: 50-500 observations per group for smooth density estimation',
        'Example: Monthly temperature readings, survey scores by age group',
        'examples: lower case and plural too',
        '  ',
      ])
    ).toEqual([
      '`value` (numeric) - The continuous variable to visualize as density curves',
      '`group` (categorical) - The grouping variable that creates separate ridges',
    ]);
  });

  it('is empty without data bullets', () => {
    expect(expectedColumns(undefined)).toEqual([]);
    expect(expectedColumns(null)).toEqual([]);
  });

  it('keeps a column whose description mentions a size', () => {
    expect(expectedColumns(['`size` (numeric) - Size: the bubble area'])).toEqual([
      '`size` (numeric) - Size: the bubble area',
    ]);
  });
});

describe('previewsByLibrary', () => {
  it('keeps each library its previews and nothing else', () => {
    expect(
      previewsByLibrary([
        {
          library_id: 'matplotlib',
          preview_url: 'p.png',
          preview_url_light: 'l.png',
          preview_url_dark: 'd.png',
        },
      ])
    ).toEqual({
      matplotlib: { preview_url: 'p.png', preview_url_light: 'l.png', preview_url_dark: 'd.png' },
    });
  });
});
