with open('app/src/sections/map/MapForceGraph.tsx', 'r') as f:
    content = f.read()

content = content.replace("import ForceGraph2D from 'react-force-graph-2d';", "import ForceGraph2D, { type ForceGraphMethods } from 'react-force-graph-2d';\ntype MapForceGraphMethods = ForceGraphMethods & { __forcesWired?: boolean };")

content = content.replace("fgRef: RefObject<{ refresh?: () => void; centerAt?: (x: number, y: number, z: number) => void; zoom?: ((z: number, ms: number) => void) & (() => number); d3Force: (force: string, args?: unknown) => { distance?: (d: number) => void; strength?: (s: number) => void } | undefined; d3ReheatSimulation?: () => void; __forcesWired?: boolean; }>;", "fgRef: RefObject<MapForceGraphMethods>;")

# the `distance` and `strength` inside the callback had type issues because d3Force types might not match exactly.
# I can cast linkForce to { distance: (d: any) => void, strength: (s: any) => void } using `unknown`.
content = content.replace("const linkForce = fg.d3Force('link');", "const linkForce = fg.d3Force('link') as unknown as { distance: (d: unknown) => void; strength: (s: unknown) => void; };")

content = content.replace(
    "const centerForce = fg.d3Force('center') as { strength?: (s: number) => void } | undefined;",
    "const centerForce = fg.d3Force('center') as unknown as { strength?: (s: unknown) => void } | undefined;"
)

with open('app/src/sections/map/MapForceGraph.tsx', 'w') as f:
    f.write(content)

with open('app/src/pages/MapPage.tsx', 'r') as f:
    page_content = f.read()

page_content = page_content.replace(
    "import { specPath } from 'src/routes/paths';",
    "import { type ForceGraphMethods } from 'react-force-graph-2d';\nimport { specPath } from 'src/routes/paths';"
)

page_content = page_content.replace(
    "const fgRef = useRef<{ refresh?: () => void; centerAt?: (x: number, y: number, z: number) => void; zoom?: ((z: number, ms: number) => void) & (() => number); graph2ScreenCoords?: (x: number, y: number) => { x: number, y: number }; d3Force: (force: string, args?: unknown) => { distance?: (d: number) => void; strength?: (s: number) => void } | undefined; d3ReheatSimulation?: () => void; __forcesWired?: boolean; }>(null);",
    "const fgRef = useRef<ForceGraphMethods & { __forcesWired?: boolean }>(null);"
)

with open('app/src/pages/MapPage.tsx', 'w') as f:
    f.write(page_content)
