/**
 * A spec's sources (`specification.yaml`, core/spec_sources.py): the section on the spec
 * page and the structured data, built the way the crawler pages in api/routers/seo.py build
 * them.
 */

import type { SourceEntry, SpecSources } from 'src/types';

/** Whether the spec names a work to show; `data` alone is none. */
export function hasSourceEntries(sources: SpecSources | null | undefined): sources is SpecSources {
  return Boolean(sources && (sources.inspired_by?.length || sources.references?.length));
}

/**
 * Whether a source's address may become a link. The API passes only blocks that
 * core/spec_sources.py accepts, http and https addresses alone; the page checks again, so a
 * `javascript:` or other address never reaches an href whatever the response holds. Like the
 * check in core: no whitespace, an http or https scheme, a host. The pattern keeps `https:///x`
 * out, which the URL parser would read as the host `x` while Python's `urlsplit` sees none.
 */
export function isWebAddress(url: string): boolean {
  if (/\s/.test(url) || !/^https?:\/\/[^/?#]/i.test(url)) return false;
  try {
    const { protocol, hostname } = new URL(url);
    return (protocol === 'http:' || protocol === 'https:') && hostname !== '';
  } catch {
    return false;
  }
}

/**
 * The resolver address of a DOI. The DOI goes in as it stands: core/spec_sources.py admits
 * only characters that need no escaping in a URL path, and the crawler pages build the same
 * address.
 */
export function doiUrl(doi: string): string {
  return `https://doi.org/${doi}`;
}

function sourceNode(entry: SourceEntry): Record<string, unknown> {
  const identifiers = (
    [
      ['DOI', entry.doi],
      ['ISBN', entry.isbn],
    ] as const
  )
    .filter(([, value]) => value)
    .map(([kind, value]) => ({ '@type': 'PropertyValue', propertyID: kind, value }));
  return {
    '@type': 'CreativeWork',
    name: entry.title,
    url: entry.url,
    ...(identifiers.length ? { identifier: identifiers } : {}),
  };
}

/**
 * The page node's JSON-LD properties for the sources: `isBasedOn` for a work that gave the
 * idea, `citation` for the literature the values follow. Empty without entries. They belong
 * on the page's node, never on SoftwareSourceCode: the code is based on the spec alone,
 * because the catalogue takes ideas from other works and never their code.
 */
export function sourcesJsonLd(sources: SpecSources | null | undefined): Record<string, unknown> {
  if (!sources) return {};
  return {
    ...(sources.inspired_by?.length ? { isBasedOn: sources.inspired_by.map(sourceNode) } : {}),
    ...(sources.references?.length ? { citation: sources.references.map(sourceNode) } : {}),
  };
}
