with open('app/src/sections/map/MapForceGraph.tsx', 'r') as f:
    content = f.read()
content = content.replace("import ForceGraph2D, { type ForceGraphMethods } from 'react-force-graph-2d';", "import ForceGraph2D from 'react-force-graph-2d';")

content = content.replace("ref={fgRef}", "// @ts-expect-error type library mismatch\n      ref={fgRef}")
# For strength:
content = content.replace("fg.d3Force('charge')?.strength(forceConfig.chargeStrength);", "// @ts-expect-error D3 force types are missing\n        fg.d3Force('charge')?.strength(forceConfig.chargeStrength);")

with open('app/src/sections/map/MapForceGraph.tsx', 'w') as f:
    f.write(content)
