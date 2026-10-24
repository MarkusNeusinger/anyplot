// anyplot.ai
// sankey-basic: Basic Sankey Diagram
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 90/100 | Created: 2026-07-25

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "sankey-basic · javascript · muix · anyplot.ai";
const SUBTITLE = "National energy flow: primary sources → carriers → end-use sectors";
const COL_HEADERS = ["PRIMARY SOURCES", "ENERGY CARRIERS", "END-USE SECTORS"];
const COL_X = [170, 760, 1440];
const NODE_W = 26;
const GAP = 18;
const PLOT_TOP = 150;
const PLOT_BOTTOM = 838;
const PLOT_H = PLOT_BOTTOM - PLOT_TOP;
const SAFE_PALETTE_INDICES = [0, 1, 2, 3, 5, 6, 7];

// Columns: set these to your data's column names
const SOURCE = "Origin node"; // role: source
const TARGET = "Destination node"; // role: target
const VALUE = "Flow (TWh)"; // role: value

// Data: replace this block with your own records
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
const unitMatch = /\(([^)]+)\)/.exec(VALUE);
const unitStr = unitMatch ? unitMatch[1] : "";
const unitSuffix = unitStr ? ` ${unitStr}` : "";

const links = data.map((row) => ({
  source: String(row[SOURCE]),
  target: String(row[TARGET]),
  value: Number(row[VALUE]),
  sx: 0,
  sy0: 0,
  sy1: 0,
  tx: 0,
  ty0: 0,
  ty1: 0,
}));

const nodeNames = Array.from(
  new Set(links.flatMap((l) => [l.source, l.target]))
);
const nodes = nodeNames.map((label) => ({
  id: label,
  label,
  col: 0,
  color: t.inkSoft,
  out: [],
  in: [],
  value: 0,
  rank: 0,
  x0: 0,
  x1: 0,
  y0: 0,
  y1: 0,
  h: 0,
}));
const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));

for (const l of links) {
  byId[l.source].out.push(l);
  byId[l.target].in.push(l);
}

let changed = true;
while (changed) {
  changed = false;
  for (const l of links) {
    if (byId[l.target].col < byId[l.source].col + 1) {
      byId[l.target].col = byId[l.source].col + 1;
      changed = true;
    }
  }
}

const maxCol = Math.max(...nodes.map((n) => n.col));
const mutedColor = t.theme === "light" ? "#6B6A63" : "#A8A79F";
let paletteCursor = 0;
for (let c = 0; c <= maxCol; c += 1) {
  for (const n of nodes.filter((node) => node.col === c)) {
    const outSum = n.out.reduce((s, l) => s + l.value, 0);
    const inSum = n.in.reduce((s, l) => s + l.value, 0);
    n.value = Math.max(outSum, inSum);
    if (c < maxCol) {
      const pIdx = SAFE_PALETTE_INDICES[paletteCursor % SAFE_PALETTE_INDICES.length];
      n.color = t.palette[pIdx];
      paletteCursor += 1;
    } else {
      n.color = mutedColor;
    }
  }
}

const columns = Array.from({ length: maxCol + 1 }, (_, c) =>
  nodes.filter((n) => n.col === c)
);

columns[0].forEach((n, i) => {
  n.rank = i;
});

for (let pass = 0; pass < 4; pass += 1) {
  if (pass % 2 === 0) {
    for (let c = 1; c < columns.length; c += 1) {
      columns[c] = columns[c]
        .map((n, i) => {
          const total = n.in.reduce((s, l) => s + l.value, 0);
          const key = total
            ? n.in.reduce((s, l) => s + byId[l.source].rank * l.value, 0) / total
            : (n.rank ?? i);
          return { n, key };
        })
        .sort((a, b) => a.key - b.key)
        .map((s) => s.n);
      columns[c].forEach((n, i) => {
        n.rank = i;
      });
    }
  } else {
    for (let c = columns.length - 2; c >= 0; c -= 1) {
      columns[c] = columns[c]
        .map((n, i) => {
          const total = n.out.reduce((s, l) => s + l.value, 0);
          const key = total
            ? n.out.reduce((s, l) => s + byId[l.target].rank * l.value, 0) / total
            : (n.rank ?? i);
          return { n, key };
        })
        .sort((a, b) => a.key - b.key)
        .map((s) => s.n);
      columns[c].forEach((n, i) => {
        n.rank = i;
      });
    }
  }
}

const scale = Math.min(
  ...columns.map((col) => {
    const total = col.reduce((s, n) => s + n.value, 0);
    return (PLOT_H - GAP * (col.length - 1)) / total;
  })
);

for (const col of columns) {
  const stackH = col.reduce((s, n) => s + n.value * scale, 0) + GAP * (col.length - 1);
  let cursor = PLOT_TOP + (PLOT_H - stackH) / 2;
  for (const n of col) {
    n.x0 = COL_X[n.col] ?? 170 + (n.col * 1270) / maxCol;
    n.x1 = n.x0 + NODE_W;
    n.y0 = cursor;
    n.h = n.value * scale;
    n.y1 = n.y0 + n.h;
    cursor = n.y1 + GAP;
  }
}

for (const n of nodes) {
  n.out.sort((a, b) => byId[a.target].y0 - byId[b.target].y0);
  let oc = n.y0;
  for (const l of n.out) {
    l.sy0 = oc;
    l.sy1 = oc + l.value * scale;
    l.sx = n.x1;
    oc = l.sy1;
  }
  n.in.sort((a, b) => byId[a.source].y0 - byId[b.source].y0);
  let ic = n.y0;
  for (const l of n.in) {
    l.ty0 = ic;
    l.ty1 = ic + l.value * scale;
    l.tx = n.x0;
    ic = l.ty1;
  }
}

function SankeyLayer() {
  const xs = useXScale();
  const ys = useYScale();
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <g>
      {links.map((l, k) => {
        const cx = (l.sx + l.tx) / 2;
        const d =
          `M ${xs(l.sx).toFixed(1)} ${ys(height - l.sy0).toFixed(1)} ` +
          `C ${xs(cx).toFixed(1)} ${ys(height - l.sy0).toFixed(1)}, ${xs(cx).toFixed(1)} ${ys(height - l.ty0).toFixed(1)}, ${xs(l.tx).toFixed(1)} ${ys(height - l.ty0).toFixed(1)} ` +
          `L ${xs(l.tx).toFixed(1)} ${ys(height - l.ty1).toFixed(1)} ` +
          `C ${xs(cx).toFixed(1)} ${ys(height - l.ty1).toFixed(1)}, ${xs(cx).toFixed(1)} ${ys(height - l.sy1).toFixed(1)}, ${xs(l.sx).toFixed(1)} ${ys(height - l.sy1).toFixed(1)} Z`;
        return (
          <path key={k} d={d} fill={byId[l.source].color} fillOpacity={0.42}>
            <title>{`${byId[l.source].label} → ${byId[l.target].label}: ${l.value}${unitSuffix}`}</title>
          </path>
        );
      })}

      {nodes.map((n) => (
        <rect
          key={n.id}
          x={xs(n.x0).toFixed(1)}
          y={ys(height - n.y0).toFixed(1)}
          width={(xs(n.x1) - xs(n.x0)).toFixed(1)}
          height={(ys(height - n.y1) - ys(height - n.y0)).toFixed(1)}
          fill={n.color}
          rx={3}
        >
          <title>{`${n.label}: ${n.value}${unitSuffix}`}</title>
        </rect>
      ))}

      {COL_HEADERS.map((label, c) => (
        <text
          key={label}
          x={xs(COL_X[c] + NODE_W / 2)}
          y={ys(height - (PLOT_TOP - 26))}
          textAnchor="middle"
          fontSize={13}
          fontWeight={600}
          letterSpacing={1}
          fill={t.inkSoft}
        >
          {label}
        </text>
      ))}

      {nodes.map((n) => {
        const cy = ys(height - (n.y0 + n.h / 2));
        const anchor = n.col === 0 ? "end" : n.col === maxCol ? "start" : "middle";
        const lx = n.col === 0 ? xs(n.x0) - 12 : n.col === maxCol ? xs(n.x1) + 12 : xs((n.x0 + n.x1) / 2);
        const midAbove = n.col > 0 && n.col < maxCol;
        return (
          <g key={n.id}>
            <text
              x={lx}
              y={midAbove ? ys(height - n.y0) - 22 : cy - 6}
              textAnchor={anchor}
              dominantBaseline="middle"
              fontSize={16}
              fontWeight={600}
              fill={t.ink}
            >
              {n.label}
            </text>
            <text
              x={lx}
              y={midAbove ? ys(height - n.y0) - 4 : cy + 14}
              textAnchor={anchor}
              dominantBaseline="middle"
              fontSize={13}
              fill={t.inkSoft}
            >
              {`${n.value}${unitSuffix}`}
            </text>
          </g>
        );
      })}

      <text x={xs(width / 2)} y={ys(height - 46)} textAnchor="middle" fontSize={27} fontWeight={600} fill={t.ink}>
        {TITLE}
      </text>
      <text x={xs(width / 2)} y={ys(height - 78)} textAnchor="middle" fontSize={16} fill={t.inkSoft}>
        {SUBTITLE}
      </text>
      <text x={xs(width / 2)} y={ys(height - 872)} textAnchor="middle" fontSize={14} fill={t.inkSoft}>
        {`Link width and node height ∝ ${VALUE}`}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <ChartsContainer
      width={width}
      height={height}
      margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
      series={[]}
      xAxis={[{ id: "x", scaleType: "linear", min: 0, max: width, position: "none" }]}
      yAxis={[{ id: "y", scaleType: "linear", min: 0, max: height, position: "none" }]}
      skipAnimation
    >
      <SankeyLayer />
    </ChartsContainer>
  );
}
