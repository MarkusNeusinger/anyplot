import re

with open('app/src/sections/map/MapForceGraph.tsx', 'r') as f:
    content = f.read()

# Fix the broken import
content = content.replace(
"""import { colorFor, NODE_SIZE } from 'src/hooks/useForceGraphSimulation';
// from 'src/hooks/useForceGraphSimulation';""",
"import { colorFor, NODE_SIZE, type MapGraphData, type MapForceConfig } from 'src/hooks/useForceGraphSimulation';"
)

content = content.replace("zoom?: (z: number, ms: number) => void;", "zoom?: ((z: number, ms: number) => void) & (() => number);")

with open('app/src/sections/map/MapForceGraph.tsx', 'w') as f:
    f.write(content)

with open('app/src/pages/MapPage.tsx', 'r') as f:
    content = f.read()

content = content.replace("zoom?: (z: number, ms: number) => void;", "zoom?: ((z: number, ms: number) => void) & (() => number);")

with open('app/src/pages/MapPage.tsx', 'w') as f:
    f.write(content)
