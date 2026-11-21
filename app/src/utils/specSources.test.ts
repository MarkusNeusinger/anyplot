import { describe, expect, it } from 'vitest';

import { doiUrl, hasSourceEntries, isWebAddress, sourcesJsonLd } from 'src/utils/specSources';

describe('hasSourceEntries', () => {
  it('is true only for a spec that names a work', () => {
    expect(hasSourceEntries(null)).toBe(false);
    expect(hasSourceEntries(undefined)).toBe(false);
    expect(hasSourceEntries({ data: 'invented', inspired_by: [], references: [] })).toBe(false);
    expect(
      hasSourceEntries({ inspired_by: [], references: [{ title: 'A', url: 'https://a.example' }] })
    ).toBe(true);
  });
});

describe('isWebAddress', () => {
  it('admits only http and https addresses with a host', () => {
    expect(isWebAddress('https://example.org/a')).toBe(true);
    expect(isWebAddress('HTTP://example.org')).toBe(true);
    for (const other of [
      'javascript:alert(1)',
      ' https://example.org',
      'https://',
      'https:///x',
      '//example.org',
      'data:text/html,x',
      'ftp://example.org',
    ]) {
      expect(isWebAddress(other)).toBe(false);
    }
  });
});

describe('doiUrl', () => {
  it('points at the DOI resolver', () => {
    expect(doiUrl('10.1000/xyz123')).toBe('https://doi.org/10.1000/xyz123');
  });
});

describe('sourcesJsonLd', () => {
  it('builds the properties api/routers/seo.py writes', () => {
    expect(
      sourcesJsonLd({
        inspired_by: [{ title: 'A project', url: 'https://example.org/p', doi: null }],
        references: [
          {
            title: 'A book',
            url: 'https://example.org/b',
            doi: '10.1000/xyz123',
            isbn: '978-3-16-148410-0',
          },
        ],
      })
    ).toEqual({
      isBasedOn: [{ '@type': 'CreativeWork', name: 'A project', url: 'https://example.org/p' }],
      citation: [
        {
          '@type': 'CreativeWork',
          name: 'A book',
          url: 'https://example.org/b',
          identifier: [
            { '@type': 'PropertyValue', propertyID: 'DOI', value: '10.1000/xyz123' },
            { '@type': 'PropertyValue', propertyID: 'ISBN', value: '978-3-16-148410-0' },
          ],
        },
      ],
    });
  });

  it('is empty without entries', () => {
    expect(sourcesJsonLd(null)).toEqual({});
    expect(sourcesJsonLd({ data: 'real', inspired_by: [], references: [] })).toEqual({});
  });
});
