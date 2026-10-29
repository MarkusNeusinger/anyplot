with open('app/src/sections/map/MapForceGraph.tsx', 'r') as f:
    content = f.read()

content = content.replace("fgRef: RefObject<any>;", "fgRef: RefObject<{ refresh?: () => void; centerAt?: (x: number, y: number, z: number) => void; zoom?: ((z: number, ms: number) => void) & (() => number); d3Force: (force: string, args?: unknown) => { distance?: (d: number) => void; strength?: (s: number) => void } | undefined; d3ReheatSimulation?: () => void; __forcesWired?: boolean; }>;")
with open('app/src/sections/map/MapForceGraph.tsx', 'w') as f:
    f.write(content)
