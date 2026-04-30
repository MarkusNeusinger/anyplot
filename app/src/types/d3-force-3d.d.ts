/**
 * Minimal ambient declarations for d3-force-3d (no @types package published).
 * We only use forceCollide; the rest of the simulation lives inside force-graph.
 */
declare module 'd3-force-3d' {
  export interface Force<N> {
    initialize: (nodes: N[]) => void;
    radius: (r: number | ((node: N, i: number, nodes: N[]) => number)) => Force<N>;
    iterations: (n: number) => Force<N>;
    strength: (s: number | ((node: N) => number)) => Force<N>;
    distance: (d: number | ((link: unknown) => number)) => Force<N>;
  }

  export function forceCollide<N>(
    radius?: number | ((node: N, i: number, nodes: N[]) => number)
  ): Force<N>;

  export function forceX<N>(
    x?: number | ((node: N, i: number, nodes: N[]) => number)
  ): Force<N>;

  export function forceY<N>(
    y?: number | ((node: N, i: number, nodes: N[]) => number)
  ): Force<N>;
}
