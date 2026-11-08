// anyplot.ai
// sankey-basic: Basic Sankey Diagram
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const LOSS_SLOT = 4; // Imprint slot 5 (matte red) stays reserved for bad/loss roles
const GAP_SHARE = 0.12; // vertical gap between stacked nodes as a share of the largest stage total
const SWEEPS = 4; // barycentre passes that reorder nodes to reduce link crossings
const NODE_WIDTH = 26; // px
const LINK_ALPHA = 0.45;

// Columns: set these to your data's column names
const SOURCE = "Source"; // role: source
const TARGET = "Target"; // role: target
const VALUE = "Energy flow (TWh)"; // role: value

// Data: replace this block with your own records, one object per row
// National energy flow: primary sources to energy carriers to end-use sectors.
const data = [
  { [SOURCE]: "Coal", [TARGET]: "Electricity", [VALUE]: 42 },
  { [SOURCE]: "Gas", [TARGET]: "Electricity", [VALUE]: 28 },
  { [SOURCE]: "Gas", [TARGET]: "Heat", [VALUE]: 18 },
  { [SOURCE]: "Nuclear", [TARGET]: "Electricity", [VALUE]: 22 },
  { [SOURCE]: "Renewables", [TARGET]: "Electricity", [VALUE]: 24 },
  { [SOURCE]: "Renewables", [TARGET]: "Heat", [VALUE]: 3 },
  { [SOURCE]: "Electricity", [TARGET]: "Residential", [VALUE]: 34 },
  { [SOURCE]: "Electricity", [TARGET]: "Industrial", [VALUE]: 40 },
  { [SOURCE]: "Electricity", [TARGET]: "Commercial", [VALUE]: 30 },
  { [SOURCE]: "Electricity", [TARGET]: "Transport", [VALUE]: 12 },
  { [SOURCE]: "Heat", [TARGET]: "Residential", [VALUE]: 14 },
  { [SOURCE]: "Heat", [TARGET]: "Industrial", [VALUE]: 7 },
];

// Plot: reads only data and the constants above
// A flow from a node back to itself has no place in a sankey
const links = data.filter((d) => d[SOURCE] !== d[TARGET]);
const nodeNames = [...new Set(links.flatMap((d) => [d[SOURCE], d[TARGET]]))];
const senders = new Set(links.map((d) => d[SOURCE]));
const unit = VALUE.match(/\(([^)]+)\)/)?.[1] ?? "";

// Stage = longest path from a node without inflow; nodes that only receive go to the last stage
const stageOf: Record<string, number> = Object.fromEntries(nodeNames.map((name) => [name, 0]));
for (let pass = 0; pass < nodeNames.length; pass += 1) {
  links.forEach((d) => {
    stageOf[d[TARGET]] = Math.max(stageOf[d[TARGET]], stageOf[d[SOURCE]] + 1);
  });
}
const stageCount = Math.max(...Object.values(stageOf)) + 1;
nodeNames.forEach((name) => {
  if (!senders.has(name)) stageOf[name] = stageCount - 1;
});

const inflow: Record<string, number> = {};
const outflow: Record<string, number> = {};
links.forEach((d) => {
  outflow[d[SOURCE]] = (outflow[d[SOURCE]] ?? 0) + d[VALUE];
  inflow[d[TARGET]] = (inflow[d[TARGET]] ?? 0) + d[VALUE];
});
const nodeValue = Object.fromEntries(
  nodeNames.map((name) => [name, Math.max(inflow[name] ?? 0, outflow[name] ?? 0)]),
);

// Every sending node gets the next Imprint hue in its order of appearance in the source column;
// its links carry it. Nodes that only receive stay neutral.
const senderNames = [...senders];
const sourcePalette = t.palette.filter((_, i) => i !== LOSS_SLOT);
const nodeColor = Object.fromEntries(
  nodeNames.map((name) => [name, senders.has(name) ? sourcePalette[senderNames.indexOf(name)] : t.inkSoft]),
);

// Order within each stage: barycentre sweeps, forward by sources, backward by targets
const stages = Array.from({ length: stageCount }, (_, s) => nodeNames.filter((name) => stageOf[name] === s));
const rank: Record<string, number> = {};
stages.forEach((col) => col.forEach((name, i) => (rank[name] = i)));
for (let pass = 0; pass < SWEEPS; pass += 1) {
  const forward = pass % 2 === 0;
  const stageOrder = forward
    ? stages.map((_, s) => s).slice(1)
    : stages.map((_, s) => s).reverse().slice(1);
  stageOrder.forEach((s) => {
    stages[s] = stages[s]
      .map((name) => {
        const attached = links.filter((d) => (forward ? d[TARGET] : d[SOURCE]) === name);
        const weight = attached.reduce((sum, d) => sum + d[VALUE], 0);
        const centre = attached.reduce((sum, d) => sum + rank[forward ? d[SOURCE] : d[TARGET]] * d[VALUE], 0) / weight;
        return { name, centre };
      })
      .sort((a, b) => a.centre - b.centre)
      .map((entry) => entry.name);
    stages[s].forEach((name, i) => (rank[name] = i));
  });
}

// Vertical layout in value units: one scale for every link and bar, each stage centred
const stageSums = stages.map((col) => col.reduce((sum, name) => sum + nodeValue[name], 0));
const gapUnits = Math.max(...stageSums) * GAP_SHARE;
const stageHeights = stages.map((col, s) => stageSums[s] + gapUnits * (col.length - 1));
const layoutHeight = Math.max(...stageHeights);
const nodeTop: Record<string, number> = {};
stages.forEach((col, s) => {
  let cursor = (layoutHeight - stageHeights[s]) / 2;
  col.forEach((name) => {
    nodeTop[name] = cursor;
    cursor += nodeValue[name] + gapUnits;
  });
});

// Each node stacks its links along its edge in the order of the nodes at their other end
const linkSourceTop = new Map();
const linkTargetTop = new Map();
nodeNames.forEach((name) => {
  let outCursor = nodeTop[name];
  links
    .filter((d) => d[SOURCE] === name)
    .sort((a, b) => nodeTop[a[TARGET]] - nodeTop[b[TARGET]])
    .forEach((d) => {
      linkSourceTop.set(d, outCursor);
      outCursor += d[VALUE];
    });
  let inCursor = nodeTop[name];
  links
    .filter((d) => d[TARGET] === name)
    .sort((a, b) => nodeTop[a[SOURCE]] - nodeTop[b[SOURCE]])
    .forEach((d) => {
      linkTargetTop.set(d, inCursor);
      inCursor += d[VALUE];
    });
});

const TITLE = "sankey-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `Link width and bar height proportional to ${VALUE} · ${links.length} flows across ${stageCount} stages`;
const HEADER_HEIGHT = 84;

function SankeyLayer() {
  const area = useDrawingArea();
  const pxPerUnit = area.height / layoutHeight;
  const stageStep = (area.width - NODE_WIDTH) / Math.max(1, stageCount - 1);
  const nodeX: Record<string, number> = Object.fromEntries(
    nodeNames.map((name) => [name, area.left + stageOf[name] * stageStep]),
  );
  const toY = (units: number) => area.top + units * pxPerUnit;
  return (
    <g>
      {links.map((d) => {
        const sx = nodeX[d[SOURCE]] + NODE_WIDTH;
        const tx = nodeX[d[TARGET]];
        const mx = (sx + tx) / 2;
        const sy0 = toY(linkSourceTop.get(d));
        const sy1 = toY(linkSourceTop.get(d) + d[VALUE]);
        const ty0 = toY(linkTargetTop.get(d));
        const ty1 = toY(linkTargetTop.get(d) + d[VALUE]);
        return (
          <path
            key={`link-${d[SOURCE]}-${d[TARGET]}`}
            d={`M ${sx} ${sy0} C ${mx} ${sy0}, ${mx} ${ty0}, ${tx} ${ty0} L ${tx} ${ty1} C ${mx} ${ty1}, ${mx} ${sy1}, ${sx} ${sy1} Z`}
            fill={nodeColor[d[SOURCE]]}
            fillOpacity={LINK_ALPHA}
          >
            <title>{`${d[SOURCE]} → ${d[TARGET]}: ${d[VALUE]} ${unit}`}</title>
          </path>
        );
      })}
      {nodeNames.map((name) => (
        <rect
          key={`node-${name}`}
          x={nodeX[name]}
          y={toY(nodeTop[name])}
          width={NODE_WIDTH}
          height={nodeValue[name] * pxPerUnit}
          rx={3}
          fill={nodeColor[name]}
        >
          <title>{`${name}: ${nodeValue[name]} ${unit}`}</title>
        </rect>
      ))}
      {nodeNames.map((name) => {
        const stage = stageOf[name];
        const top = toY(nodeTop[name]);
        const middle = top + (nodeValue[name] * pxPerUnit) / 2;
        // First stage labels sit left of the bar, last stage right, middle stages above it
        const side = stage === 0 ? "left" : stage === stageCount - 1 ? "right" : "above";
        const x =
          side === "left" ? nodeX[name] - 12 : side === "right" ? nodeX[name] + NODE_WIDTH + 12 : nodeX[name] + NODE_WIDTH / 2;
        const anchor = side === "left" ? "end" : side === "right" ? "start" : "middle";
        const nameY = side === "above" ? top - 34 : middle - 10;
        return (
          <g key={`label-${name}`} stroke={t.pageBg} strokeWidth={4} paintOrder="stroke" strokeLinejoin="round">
            <text x={x} y={nameY} textAnchor={anchor} dominantBaseline="central" fontSize={16} fontWeight={600} fill={t.ink}>
              {name}
            </text>
            <text x={x} y={nameY + 20} textAnchor={anchor} dominantBaseline="central" fontSize={14} fill={t.inkSoft}>
              {`${nodeValue[name]} ${unit}`}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_HEIGHT,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>
      <ChartsContainer
        width={width}
        height={height - HEADER_HEIGHT}
        series={[]}
        xAxis={[{ position: "none" }]}
        yAxis={[{ position: "none" }]}
        margin={{ top: 56, right: 150, bottom: 32, left: 150 }}
        skipAnimation
      >
        <SankeyLayer />
      </ChartsContainer>
    </div>
  );
}
