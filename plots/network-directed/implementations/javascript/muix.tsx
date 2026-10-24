// anyplot.ai
// network-directed: Directed Network Graph
// Library: muix 9.2.1 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-09-05

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "network-directed · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 64;
const MARGIN = { top: 28, right: 260, bottom: 32, left: 44 };
const NODE_RADIUS = 30;
const END_GAP = 6;
const PAD_X_SHARE = 0.14;
const PAD_Y_SHARE = 0.25;

// Data
const SOURCE_COL = "Importer Module";
const SOURCE_LAYER_COL = "Importer Layer";
const SOURCE_DEPTH_COL = "Importer Depth";
const TARGET_COL = "Imported Module";
const TARGET_LAYER_COL = "Imported Layer";
const TARGET_DEPTH_COL = "Imported Depth";
const WEIGHT_COL = "Import Calls";

const DATA: Array<Record<string, string | number>> = [
  {
    [SOURCE_COL]: "config",
    [SOURCE_LAYER_COL]: "Foundation",
    [SOURCE_DEPTH_COL]: 0,
    [TARGET_COL]: "utils",
    [TARGET_LAYER_COL]: "Foundation",
    [TARGET_DEPTH_COL]: 0,
    [WEIGHT_COL]: 2,
  },
  {
    [SOURCE_COL]: "logger",
    [SOURCE_LAYER_COL]: "Core Services",
    [SOURCE_DEPTH_COL]: 1,
    [TARGET_COL]: "utils",
    [TARGET_LAYER_COL]: "Foundation",
    [TARGET_DEPTH_COL]: 0,
    [WEIGHT_COL]: 3,
  },
  {
    [SOURCE_COL]: "auth",
    [SOURCE_LAYER_COL]: "Core Services",
    [SOURCE_DEPTH_COL]: 1,
    [TARGET_COL]: "utils",
    [TARGET_LAYER_COL]: "Foundation",
    [TARGET_DEPTH_COL]: 0,
    [WEIGHT_COL]: 2,
  },
  {
    [SOURCE_COL]: "auth",
    [SOURCE_LAYER_COL]: "Core Services",
    [SOURCE_DEPTH_COL]: 1,
    [TARGET_COL]: "config",
    [TARGET_LAYER_COL]: "Foundation",
    [TARGET_DEPTH_COL]: 0,
    [WEIGHT_COL]: 1,
  },
  {
    [SOURCE_COL]: "cache",
    [SOURCE_LAYER_COL]: "Core Services",
    [SOURCE_DEPTH_COL]: 1,
    [TARGET_COL]: "utils",
    [TARGET_LAYER_COL]: "Foundation",
    [TARGET_DEPTH_COL]: 0,
    [WEIGHT_COL]: 2,
  },
  {
    [SOURCE_COL]: "orders",
    [SOURCE_LAYER_COL]: "Domain Logic",
    [SOURCE_DEPTH_COL]: 2,
    [TARGET_COL]: "auth",
    [TARGET_LAYER_COL]: "Core Services",
    [TARGET_DEPTH_COL]: 1,
    [WEIGHT_COL]: 2,
  },
  {
    [SOURCE_COL]: "orders",
    [SOURCE_LAYER_COL]: "Domain Logic",
    [SOURCE_DEPTH_COL]: 2,
    [TARGET_COL]: "logger",
    [TARGET_LAYER_COL]: "Core Services",
    [TARGET_DEPTH_COL]: 1,
    [WEIGHT_COL]: 3,
  },
  {
    [SOURCE_COL]: "orders",
    [SOURCE_LAYER_COL]: "Domain Logic",
    [SOURCE_DEPTH_COL]: 2,
    [TARGET_COL]: "cache",
    [TARGET_LAYER_COL]: "Core Services",
    [TARGET_DEPTH_COL]: 1,
    [WEIGHT_COL]: 2,
  },
  {
    [SOURCE_COL]: "inventory",
    [SOURCE_LAYER_COL]: "Domain Logic",
    [SOURCE_DEPTH_COL]: 2,
    [TARGET_COL]: "cache",
    [TARGET_LAYER_COL]: "Core Services",
    [TARGET_DEPTH_COL]: 1,
    [WEIGHT_COL]: 2,
  },
  {
    [SOURCE_COL]: "inventory",
    [SOURCE_LAYER_COL]: "Domain Logic",
    [SOURCE_DEPTH_COL]: 2,
    [TARGET_COL]: "logger",
    [TARGET_LAYER_COL]: "Core Services",
    [TARGET_DEPTH_COL]: 1,
    [WEIGHT_COL]: 2,
  },
  {
    [SOURCE_COL]: "billing",
    [SOURCE_LAYER_COL]: "Domain Logic",
    [SOURCE_DEPTH_COL]: 2,
    [TARGET_COL]: "auth",
    [TARGET_LAYER_COL]: "Core Services",
    [TARGET_DEPTH_COL]: 1,
    [WEIGHT_COL]: 2,
  },
  {
    [SOURCE_COL]: "billing",
    [SOURCE_LAYER_COL]: "Domain Logic",
    [SOURCE_DEPTH_COL]: 2,
    [TARGET_COL]: "orders",
    [TARGET_LAYER_COL]: "Domain Logic",
    [TARGET_DEPTH_COL]: 2,
    [WEIGHT_COL]: 1,
  },
  {
    [SOURCE_COL]: "rest-api",
    [SOURCE_LAYER_COL]: "API Layer",
    [SOURCE_DEPTH_COL]: 3,
    [TARGET_COL]: "orders",
    [TARGET_LAYER_COL]: "Domain Logic",
    [TARGET_DEPTH_COL]: 2,
    [WEIGHT_COL]: 3,
  },
  {
    [SOURCE_COL]: "rest-api",
    [SOURCE_LAYER_COL]: "API Layer",
    [SOURCE_DEPTH_COL]: 3,
    [TARGET_COL]: "inventory",
    [TARGET_LAYER_COL]: "Domain Logic",
    [TARGET_DEPTH_COL]: 2,
    [WEIGHT_COL]: 2,
  },
  {
    [SOURCE_COL]: "rest-api",
    [SOURCE_LAYER_COL]: "API Layer",
    [SOURCE_DEPTH_COL]: 3,
    [TARGET_COL]: "billing",
    [TARGET_LAYER_COL]: "Domain Logic",
    [TARGET_DEPTH_COL]: 2,
    [WEIGHT_COL]: 2,
  },
  {
    [SOURCE_COL]: "graphql-api",
    [SOURCE_LAYER_COL]: "API Layer",
    [SOURCE_DEPTH_COL]: 3,
    [TARGET_COL]: "orders",
    [TARGET_LAYER_COL]: "Domain Logic",
    [TARGET_DEPTH_COL]: 2,
    [WEIGHT_COL]: 3,
  },
  {
    [SOURCE_COL]: "graphql-api",
    [SOURCE_LAYER_COL]: "API Layer",
    [SOURCE_DEPTH_COL]: 3,
    [TARGET_COL]: "billing",
    [TARGET_LAYER_COL]: "Domain Logic",
    [TARGET_DEPTH_COL]: 2,
    [WEIGHT_COL]: 1,
  },
  {
    [SOURCE_COL]: "web-app",
    [SOURCE_LAYER_COL]: "UI & Apps",
    [SOURCE_DEPTH_COL]: 4,
    [TARGET_COL]: "rest-api",
    [TARGET_LAYER_COL]: "API Layer",
    [TARGET_DEPTH_COL]: 3,
    [WEIGHT_COL]: 3,
  },
  {
    [SOURCE_COL]: "web-app",
    [SOURCE_LAYER_COL]: "UI & Apps",
    [SOURCE_DEPTH_COL]: 4,
    [TARGET_COL]: "graphql-api",
    [TARGET_LAYER_COL]: "API Layer",
    [TARGET_DEPTH_COL]: 3,
    [WEIGHT_COL]: 2,
  },
  {
    [SOURCE_COL]: "mobile-app",
    [SOURCE_LAYER_COL]: "UI & Apps",
    [SOURCE_DEPTH_COL]: 4,
    [TARGET_COL]: "graphql-api",
    [TARGET_LAYER_COL]: "API Layer",
    [TARGET_DEPTH_COL]: 3,
    [WEIGHT_COL]: 2,
  },
  {
    [SOURCE_COL]: "admin-panel",
    [SOURCE_LAYER_COL]: "UI & Apps",
    [SOURCE_DEPTH_COL]: 4,
    [TARGET_COL]: "rest-api",
    [TARGET_LAYER_COL]: "API Layer",
    [TARGET_DEPTH_COL]: 3,
    [WEIGHT_COL]: 2,
  },
  {
    [SOURCE_COL]: "admin-panel",
    [SOURCE_LAYER_COL]: "UI & Apps",
    [SOURCE_DEPTH_COL]: 4,
    [TARGET_COL]: "inventory",
    [TARGET_LAYER_COL]: "Domain Logic",
    [TARGET_DEPTH_COL]: 2,
    [WEIGHT_COL]: 1,
  },
  {
    [SOURCE_COL]: "config",
    [SOURCE_LAYER_COL]: "Foundation",
    [SOURCE_DEPTH_COL]: 0,
    [TARGET_COL]: "auth",
    [TARGET_LAYER_COL]: "Core Services",
    [TARGET_DEPTH_COL]: 1,
    [WEIGHT_COL]: 1,
  },
];

// Derive unique modules and architectural layers across both endpoint columns
interface ModuleNode {
  id: string;
  layer: string;
  depth: number;
  x: number;
  y: number;
}

const rawModules: Array<{ id: string; layer: string; depth: number }> = [];
const seenModules = new Set<string>();
const layerNames: string[] = [];

for (let i = 0; i < DATA.length; i++) {
  const row = DATA[i];
  const tgt = String(row[TARGET_COL]);
  const tgtLayer = String(row[TARGET_LAYER_COL]);
  const tgtDepth = Number(row[TARGET_DEPTH_COL]);
  if (!seenModules.has(tgt)) {
    seenModules.add(tgt);
    rawModules.push({ id: tgt, layer: tgtLayer, depth: tgtDepth });
  }
  if (!layerNames.includes(tgtLayer)) layerNames.push(tgtLayer);

  const src = String(row[SOURCE_COL]);
  const srcLayer = String(row[SOURCE_LAYER_COL]);
  const srcDepth = Number(row[SOURCE_DEPTH_COL]);
  if (!seenModules.has(src)) {
    seenModules.add(src);
    rawModules.push({ id: src, layer: srcLayer, depth: srcDepth });
  }
  if (!layerNames.includes(srcLayer)) layerNames.push(srcLayer);
}

// Reserve palette[4] (semantic error red) for circular back-edge; assign unused palette slots in order
const flagColor = t.palette[4];
const unusedPaletteSlots = [t.palette[0], t.palette[1], t.palette[2], t.palette[3], t.palette[5]];
const layerColors = new Map<string, string>();
for (let i = 0; i < layerNames.length; i++) {
  layerColors.set(layerNames[i], unusedPaletteSlots[i]);
}

// Group modules by depth and center vertically within each layer
const depthCounts = new Map<number, number>();
for (let i = 0; i < rawModules.length; i++) {
  const d = rawModules[i].depth;
  depthCounts.set(d, (depthCounts.get(d) ?? 0) + 1);
}

const depthSeen = new Map<number, number>();
const nodes: ModuleNode[] = [];
const nodeById = new Map<string, ModuleNode>();

for (let i = 0; i < rawModules.length; i++) {
  const m = rawModules[i];
  const seen = depthSeen.get(m.depth) ?? 0;
  depthSeen.set(m.depth, seen + 1);
  const count = depthCounts.get(m.depth) ?? 1;
  const node: ModuleNode = {
    id: m.id,
    layer: m.layer,
    depth: m.depth,
    x: m.depth,
    y: seen - (count - 1) / 2,
  };
  nodes.push(node);
  nodeById.set(node.id, node);
}

const edgeKeys = new Set<string>();
for (let i = 0; i < DATA.length; i++) {
  edgeKeys.add(`${DATA[i][SOURCE_COL]}>${DATA[i][TARGET_COL]}`);
}

// Rule-based detection of bidirectional pairs and upward dependency violations (sourceDepth < targetDepth)
const edges = DATA.map((row) => {
  const source = String(row[SOURCE_COL]);
  const target = String(row[TARGET_COL]);
  const weight = Number(row[WEIGHT_COL]);
  const srcDepth = Number(row[SOURCE_DEPTH_COL]);
  const tgtDepth = Number(row[TARGET_DEPTH_COL]);
  const bidirectional = edgeKeys.has(`${target}>${source}`);
  const flagged = srcDepth < tgtDepth;
  return { source, target, weight, bidirectional, flagged };
});

const xs = nodes.map((n) => n.x);
const ys = nodes.map((n) => n.y);
const minX = Math.min(...xs);
const maxX = Math.max(...xs);
const minY = Math.min(...ys);
const maxY = Math.max(...ys);
const xPad = (maxX - minX) * PAD_X_SHARE;
const yPad = (maxY - minY) * PAD_Y_SHARE;
const xAxisMin = minX - xPad;
const xAxisMax = maxX + xPad;
const yAxisMin = minY - yPad;
const yAxisMax = maxY + yPad;

function DirectedNetworkOverlay() {
  const { left, top, width } = useDrawingArea();
  const xScale = useXScale();
  const yScale = useYScale();

  const legendX = left + width + 36;
  const legendY = top + 12;

  return (
    <g>
      <defs>
        <marker
          id="np-arrow"
          viewBox="0 0 12 10"
          refX="11"
          refY="5"
          markerWidth="13"
          markerHeight="11"
          markerUnits="userSpaceOnUse"
          orient="auto-start-reverse"
        >
          <path d="M0,0 L12,5 L0,10 Z" fill={t.inkSoft} />
        </marker>
        <marker
          id="np-arrow-flag"
          viewBox="0 0 12 10"
          refX="11"
          refY="5"
          markerWidth="15"
          markerHeight="13"
          markerUnits="userSpaceOnUse"
          orient="auto-start-reverse"
        >
          <path d="M0,0 L12,5 L0,10 Z" fill={flagColor} />
        </marker>
      </defs>

      {/* Directed edges with arrowheads stopping at target node rim */}
      {edges.map((e, i) => {
        const s = nodeById.get(e.source);
        const d = nodeById.get(e.target);
        if (!s || !d) return null;
        const x1 = Number(xScale(s.x));
        const y1 = Number(yScale(s.y));
        const x2 = Number(xScale(d.x));
        const y2 = Number(yScale(d.y));

        let pathD = "";
        if (!e.bidirectional) {
          const dx = x2 - x1;
          const dy = y2 - y1;
          const dist = Math.hypot(dx, dy) || 1;
          const ex = x2 - (dx / dist) * (NODE_RADIUS + END_GAP);
          const ey = y2 - (dy / dist) * (NODE_RADIUS + END_GAP);
          pathD = `M ${x1} ${y1} L ${ex} ${ey}`;
        } else {
          const mx = (x1 + x2) / 2;
          const my = (y1 + y2) / 2;
          const canonFrom = e.source < e.target ? s : d;
          const canonTo = e.source < e.target ? d : s;
          const cdx = Number(xScale(canonTo.x)) - Number(xScale(canonFrom.x));
          const cdy = Number(yScale(canonTo.y)) - Number(yScale(canonFrom.y));
          const cdist = Math.hypot(cdx, cdy) || 1;
          const nx = -cdy / cdist;
          const ny = cdx / cdist;
          const sign = e.source < e.target ? 1 : -1;
          const bow = Math.max(55, cdist * 0.4) * sign;
          const cx = mx + nx * bow;
          const cy = my + ny * bow;
          const tdx = x2 - cx;
          const tdy = y2 - cy;
          const tdist = Math.hypot(tdx, tdy) || 1;
          const ex = x2 - (tdx / tdist) * (NODE_RADIUS + END_GAP);
          const ey = y2 - (tdy / tdist) * (NODE_RADIUS + END_GAP);
          pathD = `M ${x1} ${y1} Q ${cx} ${cy} ${ex} ${ey}`;
        }

        return (
          <path
            key={`${e.source}-${e.target}-${i}`}
            d={pathD}
            fill="none"
            stroke={e.flagged ? flagColor : t.inkSoft}
            strokeWidth={e.flagged ? 3.5 : 1.3 + e.weight * 0.5}
            strokeOpacity={e.flagged ? 0.95 : 0.68}
            markerEnd={e.flagged ? "url(#np-arrow-flag)" : "url(#np-arrow)"}
          />
        );
      })}

      {/* Node circles */}
      {nodes.map((n) => (
        <circle
          key={`node-${n.id}`}
          cx={Number(xScale(n.x))}
          cy={Number(yScale(n.y))}
          r={NODE_RADIUS}
          fill={layerColors.get(n.layer) ?? t.palette[0]}
          stroke={t.pageBg}
          strokeWidth={3}
        />
      ))}

      {/* Node labels */}
      {nodes.map((n) => (
        <text
          key={`label-${n.id}`}
          x={Number(xScale(n.x))}
          y={Number(yScale(n.y)) + NODE_RADIUS + 22}
          textAnchor="middle"
          fontSize={15}
          fontWeight={500}
          fill={t.ink}
          stroke={t.pageBg}
          strokeWidth={4}
          paintOrder="stroke"
        >
          {n.id}
        </text>
      ))}

      {/* Right-side architectural layer and circular dependency legend */}
      <g transform={`translate(${legendX}, ${legendY})`}>
        <text x={0} y={14} fontSize={15} fontWeight={700} fill={t.ink}>
          Architecture Layer
        </text>
        {layerNames.map((lName, idx) => (
          <g key={lName} transform={`translate(0, ${38 + idx * 32})`}>
            <circle cx={9} cy={0} r={9} fill={layerColors.get(lName) ?? t.palette[0]} />
            <text x={28} y={5} fontSize={15} fill={t.ink}>
              {lName}
            </text>
          </g>
        ))}

        <g transform={`translate(0, ${52 + layerNames.length * 32})`}>
          <line
            x1={0}
            y1={0}
            x2={32}
            y2={0}
            stroke={flagColor}
            strokeWidth={3.5}
            markerEnd="url(#np-arrow-flag)"
          />
          <text x={44} y={5} fontSize={14} fontWeight={600} fill={t.ink}>
            Circular dependency
          </text>
        </g>

        <g transform={`translate(0, ${92 + layerNames.length * 32})`}>
          <text x={0} y={0} fontSize={14} fill={t.inkSoft}>
            Edge width = {WEIGHT_COL}
          </text>
        </g>
      </g>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div
      style={{
        width,
        height,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      <div
        style={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          fontWeight: 600,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_HEIGHT}
        margin={MARGIN}
        skipAnimation
        series={[]}
        xAxis={[{ position: "none", scaleType: "linear", min: xAxisMin, max: xAxisMax }]}
        yAxis={[{ position: "none", scaleType: "linear", min: yAxisMin, max: yAxisMax }]}
      >
        <DirectedNetworkOverlay />
      </ChartsContainer>
    </div>
  );
}
