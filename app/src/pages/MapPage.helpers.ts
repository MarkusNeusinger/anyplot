/**
 * Pure helpers for the /map page: tag flattening, IDF weighting,
 * weighted Jaccard similarity, and sparse KNN edge construction.
 *
 * Kept side-effect-free so the math is exhaustively unit-testable
 * in MapPage.helpers.test.ts. The page component imports these and
 * feeds the result into react-force-graph-2d.
 */

import { selectPreviewUrl } from '../utils/themedPreview';


/** Backend response shape from GET /api/specs/map. Mirrors api/schemas.py::SpecMapItem. */
export interface SpecMapItem {
  id: string;
  title: string;
  preview_url_light: string | null;
  preview_url_dark: string | null;
  quality_score: number | null;
  tags: Record<string, string[]> | null;
  impl_tags: Record<string, string[]> | null;
}

/** Node shape passed to ForceGraph2D. `img` populated lazily as thumbnails resolve. */
export interface MapNode {
  id: string;
  title: string;
  tags: string[];
  thumbUrl: string | null;
  img?: HTMLImageElement;
}

/** Link shape passed to ForceGraph2D. `weight` = weighted-Jaccard sim ∈ (0, 1]. */
export interface MapLink {
  source: string;
  target: string;
  weight: number;
}

/**
 * Flatten a spec's nested tag dicts to a single `category:value` string set.
 * Prefixing prevents collisions like `numeric` appearing in both `data_type`
 * and `dataprep` and gives the IDF/Jaccard math distinct tokens to weigh.
 */
export function flattenTags(spec: SpecMapItem, includeImpl = true): string[] {
  const out: string[] = [];
  const push = (dict: Record<string, string[]> | null | undefined) => {
    if (!dict) return;
    for (const [category, values] of Object.entries(dict)) {
      if (!Array.isArray(values)) continue;
      for (const v of values) {
        if (typeof v === 'string' && v.length > 0) out.push(`${category}:${v}`);
      }
    }
  };
  push(spec.tags);
  if (includeImpl) push(spec.impl_tags);
  return Array.from(new Set(out));
}

/**
 * Inverse-document-frequency weights: w_t = log(N / df_t).
 * Down-weights ubiquitous tags (`data_type:numeric` is in nearly every spec)
 * and amplifies rare ones. Returns weight ≥ 0; tags absent from the corpus
 * default to 0 when looked up.
 */
export function computeIDF(specs: SpecMapItem[]): Map<string, number> {
  const N = specs.length || 1;
  const df = new Map<string, number>();
  for (const spec of specs) {
    for (const tag of flattenTags(spec)) {
      df.set(tag, (df.get(tag) ?? 0) + 1);
    }
  }
  const idf = new Map<string, number>();
  for (const [tag, count] of df) {
    idf.set(tag, Math.log(N / count));
  }
  return idf;
}

/**
 * Weighted Jaccard similarity over two tag sets.
 *   sim = Σ w_t for t∈a∩b / Σ w_t for t∈a∪b
 * Returns 0 when both sets are empty (no signal) or denominator collapses.
 */
export function weightedJaccard(a: string[], b: string[], idf: Map<string, number>): number {
  if (a.length === 0 || b.length === 0) return 0;
  const setA = new Set(a);
  const setB = new Set(b);
  let num = 0;
  let denom = 0;
  const seen = new Set<string>();
  for (const t of setA) {
    seen.add(t);
    const w = idf.get(t) ?? 0;
    denom += w;
    if (setB.has(t)) num += w;
  }
  for (const t of setB) {
    if (seen.has(t)) continue;
    denom += idf.get(t) ?? 0;
  }
  return denom > 0 ? num / denom : 0;
}

/**
 * Build a sparse KNN link list: each spec keeps its top-K most similar
 * neighbors above `minSim`. Output is deduplicated (no A→B + B→A pair) and
 * symmetric — the link with the higher weight wins on tie.
 *
 * With ~327 specs × K=5 the result is ~1.6k edges: dense enough for
 * cohesive clustering, sparse enough to avoid hairball rendering.
 */
export function buildKNNLinks(
  specs: SpecMapItem[],
  idf: Map<string, number>,
  k = 5,
  minSim = 0.05
): MapLink[] {
  const tagsByIdx = specs.map(s => flattenTags(s));
  const linkSet = new Map<string, MapLink>();
  for (let i = 0; i < specs.length; i++) {
    const sims: { j: number; sim: number }[] = [];
    for (let j = 0; j < specs.length; j++) {
      if (i === j) continue;
      const sim = weightedJaccard(tagsByIdx[i], tagsByIdx[j], idf);
      // sim > 0 drops zero-weight links (no shared tags or all-zero IDF) — pure visual noise.
      if (sim > 0 && sim >= minSim) sims.push({ j, sim });
    }
    sims.sort((x, y) => y.sim - x.sim);
    for (const { j, sim } of sims.slice(0, k)) {
      const a = specs[i].id;
      const b = specs[j].id;
      const key = a < b ? `${a}|${b}` : `${b}|${a}`;
      const existing = linkSet.get(key);
      if (!existing || sim > existing.weight) {
        linkSet.set(key, { source: a < b ? a : b, target: a < b ? b : a, weight: sim });
      }
    }
  }
  return Array.from(linkSet.values());
}

/** Pick the best thumbnail URL for the current theme. Wraps selectPreviewUrl. */
export function selectMapThumbUrl(spec: SpecMapItem, isDark: boolean): string | null {
  return selectPreviewUrl(spec, isDark);
}

/**
 * Eager-preload every node's thumbnail. Resolves once all images either
 * loaded or errored — failures are swallowed (image stays undefined and
 * the node renders as a plain dot in nodeCanvasObject's fallback path).
 *
 * `onLoad` fires per-image so the page can call fgRef.refresh() to re-paint
 * without re-running the simulation. This is what produces the "thumbnails
 * pop in organically" UX rather than a blocking wait.
 */
export async function preloadImages(
  items: { id: string; thumbUrl: string | null }[],
  onLoad?: (id: string, img: HTMLImageElement) => void
): Promise<Map<string, HTMLImageElement>> {
  const out = new Map<string, HTMLImageElement>();
  await Promise.all(
    items.map(({ id, thumbUrl }) => {
      if (!thumbUrl) return Promise.resolve();
      return new Promise<void>(resolve => {
        // document.createElement is preferred over `new Image()` here only because
        // some lint configs don't surface browser globals on plain .ts files.
        const img = document.createElement('img');
        // Intentionally NOT setting img.crossOrigin: the GCS bucket has no CORS
        // headers, and adding crossOrigin='anonymous' triggers a preflight that
        // fails. We only ever drawImage() these onto the canvas (the canvas
        // becomes "tainted", which is fine — we never read it back).
        img.onload = () => {
          out.set(id, img);
          onLoad?.(id, img);
          resolve();
        };
        img.onerror = () => resolve();
        img.src = thumbUrl;
      });
    })
  );
  return out;
}
