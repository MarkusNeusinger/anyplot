// anyplot.ai
// network-directed: Directed Network Graph
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 84/100 | Updated: 2026-10-24

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "network-directed · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 64;
const MARGIN = { top: 28, right: 260, bottom: 32, left: 44 };
const NODE_HALF_HEIGHT = 21;
const NODE_PAD_X = 16;
const CHAR_WIDTH = 8.6;
const LABEL_SIZE = 15;
const END_GAP = 6;
const PAD_X_SHARE = 0.14;
const PAD_Y_SHARE = 0.25;

// Columns: set these to your data's column names
const MODULE = "Module"; // role: node
const LAYER = "Architecture layer"; // role: group
const SOURCE = "Importer module"; // role: source
const TARGET = "Imported module"; // role: target
const WEIGHT = "Import calls"; // role: weight

// Data: replace this block with your own records
const nodes: Array<Record<string, string>> = [
  { [MODULE]: "utils", [LAYER]: "Foundation" },
  { [MODULE]: "config", [LAYER]: "Foundation" },
  { [MODULE]: "logger", [LAYER]: "Core Services" },
  { [MODULE]: "auth", [LAYER]: "Core Services" },
  { [MODULE]: "cache", [LAYER]: "Core Services" },
  { [MODULE]: "orders", [LAYER]: "Domain Logic" },
  { [MODULE]: "billing", [LAYER]: "Domain Logic" },
  { [MODULE]: "inventory", [LAYER]: "Domain Logic" },
  { [MODULE]: "rest-api", [LAYER]: "API Layer" },
  { [MODULE]: "graphql-api", [LAYER]: "API Layer" },
  { [MODULE]: "web-app", [LAYER]: "UI & Apps" },
  { [MODULE]: "mobile-app", [LAYER]: "UI & Apps" },
  { [MODULE]: "admin-panel", [LAYER]: "UI & Apps" },
];

const data: Array<Record<string, string | number>> = [
  { [SOURCE]: "config", [TARGET]: "utils", [WEIGHT]: 2 },
  { [SOURCE]: "logger", [TARGET]: "utils", [WEIGHT]: 3 },
  { [SOURCE]: "auth", [TARGET]: "utils", [WEIGHT]: 2 },
  { [SOURCE]: "auth", [TARGET]: "config", [WEIGHT]: 1 },
  { [SOURCE]: "cache", [TARGET]: "utils", [WEIGHT]: 2 },
  { [SOURCE]: "orders", [TARGET]: "auth", [WEIGHT]: 2 },
  { [SOURCE]: "orders", [TARGET]: "logger", [WEIGHT]: 3 },
  { [SOURCE]: "orders", [TARGET]: "cache", [WEIGHT]: 2 },
  { [SOURCE]: "inventory", [TARGET]: "cache", [WEIGHT]: 2 },
  { [SOURCE]: "inventory", [TARGET]: "logger", [WEIGHT]: 2 },
  { [SOURCE]: "billing", [TARGET]: "auth", [WEIGHT]: 2 },
  { [SOURCE]: "billing", [TARGET]: "orders", [WEIGHT]: 1 },
  { [SOURCE]: "rest-api", [TARGET]: "orders", [WEIGHT]: 3 },
  { [SOURCE]: "rest-api", [TARGET]: "inventory", [WEIGHT]: 2 },
  { [SOURCE]: "rest-api", [TARGET]: "billing", [WEIGHT]: 2 },
  { [SOURCE]: "graphql-api", [TARGET]: "orders", [WEIGHT]: 3 },
  { [SOURCE]: "graphql-api", [TARGET]: "billing", [WEIGHT]: 1 },
  { [SOURCE]: "web-app", [TARGET]: "rest-api", [WEIGHT]: 3 },
  { [SOURCE]: "web-app", [TARGET]: "graphql-api", [WEIGHT]: 2 },
  { [SOURCE]: "mobile-app", [TARGET]: "graphql-api", [WEIGHT]: 2 },
  { [SOURCE]: "admin-panel", [TARGET]: "rest-api", [WEIGHT]: 2 },
  { [SOURCE]: "admin-panel", [TARGET]: "inventory", [WEIGHT]: 1 },
  { [SOURCE]: "config", [TARGET]: "auth", [WEIGHT]: 1 },
];

// Plot: reads only data and the constants above
interface ModuleNode {
  id: string;
  layer: string;
  depth: number;
  x: number;
  y: number;
  halfWidth: number;
}

// Distance from a node's centre to its border along the direction (dx, dy)
function borderDistance(n: ModuleNode, dx: number, dy: number) {
  const dist = Math.hypot(dx, dy);
  const ux = Math.abs(dx / dist);
  const uy = Math.abs(dy / dist);
  return Math.min(ux > 0 ? n.halfWidth / ux : Infinity, uy > 0 ? NODE_HALF_HEIGHT / uy : Infinity);
}

const layerNames: string[] = [];
for (let i = 0; i < nodes.length; i++) {
  const layer = String(nodes[i][LAYER]);
  if (!layerNames.includes(layer)) layerNames.push(layer);
}

const rawModules = nodes.map((row) => {
  const id = String(row[MODULE]);
  const layer = String(row[LAYER]);
  const depth = layerNames.indexOf(layer);
  return { id, layer, depth };
});

const flagColor = t.palette[4];
const unusedPaletteSlots = [t.palette[0], t.palette[1], t.palette[2], t.palette[3], t.palette[5]];
const layerColors = new Map<string, string>();
for (let i = 0; i < layerNames.length; i++) {
  layerColors.set(layerNames[i], unusedPaletteSlots[i]);
}

const depthCounts = new Map<number, number>();
for (let i = 0; i < rawModules.length; i++) {
  const d = rawModules[i].depth;
  depthCounts.set(d, (depthCounts.get(d) ?? 0) + 1);
}

const depthSeen = new Map<number, number>();
const layoutNodes: ModuleNode[] = [];
const nodeById = new Map<string, ModuleNode>();

for (let i = 0; i < rawModules.length; i++) {
  const m = rawModules[i];
  const seen = depthSeen.get(m.depth) ?? 0;
  depthSeen.set(m.depth, seen + 1);
  const count = Number(depthCounts.get(m.depth));
  const node: ModuleNode = {
    id: m.id,
    layer: m.layer,
    depth: m.depth,
    x: m.depth,
    y: seen - (count - 1) / 2,
    halfWidth: (m.id.length * CHAR_WIDTH) / 2 + NODE_PAD_X,
  };
  layoutNodes.push(node);
  nodeById.set(node.id, node);
}

const edgeKeys = new Set<string>();
for (let i = 0; i < data.length; i++) {
  edgeKeys.add(`${data[i][SOURCE]}>${data[i][TARGET]}`);
}

const edges = data.map((row) => {
  const source = String(row[SOURCE]);
  const target = String(row[TARGET]);
  const weight = Number(row[WEIGHT]);
  const srcNode = nodeById.get(source)!;
  const tgtNode = nodeById.get(target)!;
  const bidirectional = edgeKeys.has(`${target}>${source}`);
  const flagged = srcNode.depth < tgtNode.depth;
  return { source, target, weight, bidirectional, flagged };
});

const xs = layoutNodes.map((n) => n.x);
const ys = layoutNodes.map((n) => n.y);
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

      {edges.map((e, i) => {
        const s = nodeById.get(e.source)!;
        const d = nodeById.get(e.target)!;
        const x1 = Number(xScale(s.x));
        const y1 = Number(yScale(s.y));
        const x2 = Number(xScale(d.x));
        const y2 = Number(yScale(d.y));

        let pathD = "";
        if (!e.bidirectional) {
          const dx = x2 - x1;
          const dy = y2 - y1;
          const dist = Math.hypot(dx, dy);
          const stop = borderDistance(d, dx, dy) + END_GAP;
          const ex = x2 - (dx / dist) * stop;
          const ey = y2 - (dy / dist) * stop;
          pathD = `M ${x1} ${y1} L ${ex} ${ey}`;
        } else {
          const mx = (x1 + x2) / 2;
          const my = (y1 + y2) / 2;
          const canonFrom = e.source < e.target ? s : d;
          const canonTo = e.source < e.target ? d : s;
          const cdx = Number(xScale(canonTo.x)) - Number(xScale(canonFrom.x));
          const cdy = Number(yScale(canonTo.y)) - Number(yScale(canonFrom.y));
          const cdist = Math.hypot(cdx, cdy);
          const nx = -cdy / cdist;
          const ny = cdx / cdist;
          const sign = e.source < e.target ? 1 : -1;
          const bow = Math.max(55, cdist * 0.4) * sign;
          const cx = mx + nx * bow;
          const cy = my + ny * bow;
          const tdx = x2 - cx;
          const tdy = y2 - cy;
          const tdist = Math.hypot(tdx, tdy);
          const stop = borderDistance(d, tdx, tdy) + END_GAP;
          const ex = x2 - (tdx / tdist) * stop;
          const ey = y2 - (tdy / tdist) * stop;
          pathD = `M ${x1} ${y1} Q ${cx} ${cy} ${ex} ${ey}`;
        }

        return (
          <path
            key={`${e.source}-${e.target}-${i}`}
            d={pathD}
            fill="none"
            stroke={e.flagged ? flagColor : t.inkSoft}
            strokeWidth={1.3 + e.weight * 0.5}
            strokeOpacity={e.flagged ? 0.95 : 0.68}
            markerEnd={e.flagged ? "url(#np-arrow-flag)" : "url(#np-arrow)"}
          />
        );
      })}

      {layoutNodes.map((n) => {
        const cx = Number(xScale(n.x));
        const cy = Number(yScale(n.y));
        const color = String(layerColors.get(n.layer));
        const box = {
          x: cx - n.halfWidth,
          y: cy - NODE_HALF_HEIGHT,
          width: n.halfWidth * 2,
          height: NODE_HALF_HEIGHT * 2,
          rx: 10,
        };
        return (
          <g key={`node-${n.id}`}>
            <rect {...box} fill={t.pageBg} />
            <rect {...box} fill={color} fillOpacity={0.24} stroke={color} strokeWidth={3} />
            <text
              x={cx}
              y={cy + 5}
              textAnchor="middle"
              fontSize={LABEL_SIZE}
              fontWeight={600}
              fill={t.ink}
            >
              {n.id}
            </text>
          </g>
        );
      })}

      <g transform={`translate(${legendX}, ${legendY})`}>
        <text x={0} y={14} fontSize={15} fontWeight={700} fill={t.ink}>
          {LAYER}
        </text>
        {layerNames.map((lName, idx) => (
          <g key={lName} transform={`translate(0, ${38 + idx * 32})`}>
            <rect
              x={0}
              y={-9}
              width={20}
              height={18}
              rx={5}
              fill={String(layerColors.get(lName))}
              fillOpacity={0.24}
              stroke={String(layerColors.get(lName))}
              strokeWidth={2.5}
            />
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
            strokeWidth={2.3}
            markerEnd="url(#np-arrow-flag)"
          />
          <text x={44} y={5} fontSize={14} fontWeight={600} fill={t.ink}>
            Upward dependency
          </text>
        </g>

        <g transform={`translate(0, ${92 + layerNames.length * 32})`}>
          <text x={0} y={0} fontSize={14} fill={t.inkSoft}>
            {`Edge width = ${WEIGHT}`}
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
