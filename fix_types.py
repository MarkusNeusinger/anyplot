import re

with open('app/src/sections/map/MapForceGraph.tsx', 'r') as f:
    content = f.read()

content = content.replace(
    "import { colors } from 'src/theme';\nimport { colorFor, NODE_SIZE } from 'src/hooks/useForceGraphSimulation';",
    "import { colors } from 'src/theme';\nimport { colorFor, NODE_SIZE, type MapGraphData, type MapForceConfig } from 'src/hooks/useForceGraphSimulation';"
)

content = content.replace("graphData: unknown;", "graphData: MapGraphData;")
content = content.replace("forceConfig: unknown;", "forceConfig: MapForceConfig;")
content = content.replace("fgRef: RefObject<unknown>;", "fgRef: RefObject<{ refresh?: () => void; centerAt?: (x: number, y: number, z: number) => void; zoom?: (z: number, ms: number) => void; d3Force: (force: string, args?: unknown) => { distance?: (d: number) => void; strength?: (s: number) => void } | undefined; d3ReheatSimulation?: () => void; __forcesWired?: boolean; }>;")

content = content.replace("const linkForce = fg.d3Force('link') as unknown;", "const linkForce = fg.d3Force('link');")
content = content.replace("fg.d3Force('center')?.strength?.(forceConfig.centerGravity);", "const centerForce: any = fg.d3Force('center'); if (centerForce && centerForce.strength) centerForce.strength(forceConfig.centerGravity);")
# Need to use 'any' if I want, wait, no any.
content = content.replace("const centerForce: any = fg.d3Force('center'); if (centerForce && centerForce.strength) centerForce.strength(forceConfig.centerGravity);",
"const centerForce = fg.d3Force('center') as { strength?: (s: number) => void } | undefined;\n        centerForce?.strength?.(forceConfig.centerGravity);")

with open('app/src/sections/map/MapForceGraph.tsx', 'w') as f:
    f.write(content)

with open('app/src/pages/MapPage.tsx', 'r') as f:
    content = f.read()

content = content.replace("const fgRef = useRef<unknown>(null);", "const fgRef = useRef<{ refresh?: () => void; centerAt?: (x: number, y: number, z: number) => void; zoom?: (z: number, ms: number) => void; graph2ScreenCoords?: (x: number, y: number) => { x: number, y: number }; d3Force: (force: string, args?: unknown) => { distance?: (d: number) => void; strength?: (s: number) => void } | undefined; d3ReheatSimulation?: () => void; __forcesWired?: boolean; }>(null);")

with open('app/src/pages/MapPage.tsx', 'w') as f:
    f.write(content)
