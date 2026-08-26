// anyplot.ai
// alluvial-opinion-flow: Opinion Flow Diagram
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-26
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const SIZE = window.ANYPLOT_SIZE;
const TITLE = "alluvial-opinion-flow · javascript · muix · anyplot.ai";
const MUTED = t.theme === "light" ? "#6B6A63" : "#A8A79F"; // Imprint muted anchor

const FONT =
  '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';

// --- Data: quarterly customer-satisfaction survey, 1,000 respondents ---------
// Ordinal sentiment scale, deterministic. Populations and transition counts
// are hand-designed so row/column sums match exactly (no rounding drift):
// each wave sums to 1,000, and every transition matrix's row sums equal the
// source wave's populations while its column sums equal the target wave's.
// The scenario deliberately drifts toward the extremes (polarization) while
// "Neutral" and "Satisfied" shrink.
const CATEGORIES = [
  { id: "vs", label: "Very Satisfied", color: t.palette[0] }, // brand green — always first series
  { id: "s", label: "Satisfied", color: t.palette[7] }, // lime — still green family, reads "positive"
  { id: "n", label: "Neutral", color: MUTED }, // muted semantic anchor
  { id: "d", label: "Dissatisfied", color: t.amber }, // amber semantic anchor — caution
  { id: "vd", label: "Very Dissatisfied", color: t.palette[4] }, // matte red — bad/error semantic anchor
];
const CATEGORY_ORDER = CATEGORIES.map((c) => c.id);
const CATEGORY_BY_ID = Object.fromEntries(CATEGORIES.map((c) => [c.id, c]));

const WAVES = ["Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025"];

const POPULATIONS = [
  { vs: 150, s: 300, n: 300, d: 150, vd: 100 },
  { vs: 200, s: 250, n: 220, d: 180, vd: 150 },
  { vs: 260, s: 200, n: 160, d: 200, vd: 180 },
  { vs: 320, s: 150, n: 120, d: 190, vd: 220 },
];

// One transition matrix per wave-to-wave step (3 steps for 4 waves).
const TRANSITIONS = [
  [
    { source: "vs", target: "vs", count: 110 },
    { source: "vs", target: "s", count: 30 },
    { source: "vs", target: "n", count: 10 },
    { source: "s", target: "vs", count: 60 },
    { source: "s", target: "s", count: 180 },
    { source: "s", target: "n", count: 40 },
    { source: "s", target: "d", count: 15 },
    { source: "s", target: "vd", count: 5 },
    { source: "n", target: "vs", count: 25 },
    { source: "n", target: "s", count: 35 },
    { source: "n", target: "n", count: 140 },
    { source: "n", target: "d", count: 70 },
    { source: "n", target: "vd", count: 30 },
    { source: "d", target: "vs", count: 3 },
    { source: "d", target: "s", count: 3 },
    { source: "d", target: "n", count: 20 },
    { source: "d", target: "d", count: 80 },
    { source: "d", target: "vd", count: 44 },
    { source: "vd", target: "vs", count: 2 },
    { source: "vd", target: "s", count: 2 },
    { source: "vd", target: "n", count: 10 },
    { source: "vd", target: "d", count: 15 },
    { source: "vd", target: "vd", count: 71 },
  ],
  [
    { source: "vs", target: "vs", count: 160 },
    { source: "vs", target: "s", count: 30 },
    { source: "vs", target: "n", count: 10 },
    { source: "s", target: "vs", count: 70 },
    { source: "s", target: "s", count: 150 },
    { source: "s", target: "n", count: 20 },
    { source: "s", target: "d", count: 8 },
    { source: "s", target: "vd", count: 2 },
    { source: "n", target: "vs", count: 25 },
    { source: "n", target: "s", count: 15 },
    { source: "n", target: "n", count: 100 },
    { source: "n", target: "d", count: 60 },
    { source: "n", target: "vd", count: 20 },
    { source: "d", target: "vs", count: 3 },
    { source: "d", target: "s", count: 3 },
    { source: "d", target: "n", count: 20 },
    { source: "d", target: "d", count: 110 },
    { source: "d", target: "vd", count: 44 },
    { source: "vd", target: "vs", count: 2 },
    { source: "vd", target: "s", count: 2 },
    { source: "vd", target: "n", count: 10 },
    { source: "vd", target: "d", count: 22 },
    { source: "vd", target: "vd", count: 114 },
  ],
  [
    { source: "vs", target: "vs", count: 220 },
    { source: "vs", target: "s", count: 30 },
    { source: "vs", target: "n", count: 10 },
    { source: "s", target: "vs", count: 90 },
    { source: "s", target: "s", count: 90 },
    { source: "s", target: "n", count: 12 },
    { source: "s", target: "d", count: 6 },
    { source: "s", target: "vd", count: 2 },
    { source: "n", target: "vs", count: 8 },
    { source: "n", target: "s", count: 20 },
    { source: "n", target: "n", count: 80 },
    { source: "n", target: "d", count: 40 },
    { source: "n", target: "vd", count: 12 },
    { source: "d", target: "vs", count: 2 },
    { source: "d", target: "s", count: 8 },
    { source: "d", target: "n", count: 15 },
    { source: "d", target: "d", count: 125 },
    { source: "d", target: "vd", count: 50 },
    { source: "vd", target: "s", count: 2 },
    { source: "vd", target: "n", count: 3 },
    { source: "vd", target: "d", count: 19 },
    { source: "vd", target: "vd", count: 156 },
  ],
];

// --- Layout: fixed category row order in every column (polarization reads as
// the top and bottom bands growing wave over wave) ---------------------------
const NODE_W = 24;
const GAP = 14;
const LEFT_MARGIN = 140;
const RIGHT_MARGIN = 170; // room for the last wave's node labels + net-change deltas
const PLOT_TOP = 170;
const PLOT_BOTTOM = SIZE.height - 50;
const PLOT_H = PLOT_BOTTOM - PLOT_TOP;
const H = SIZE.height; // flips top-down pixel y into the chart's bottom-up data y

const usableW = SIZE.width - LEFT_MARGIN - RIGHT_MARGIN - NODE_W;
const COL_X = WAVES.map((_, w) => LEFT_MARGIN + (usableW * w) / (WAVES.length - 1));
const SCALE = (PLOT_H - GAP * (CATEGORIES.length - 1)) / 1000; // every wave sums to 1,000

const nodes = [];
const nodeByKey = {};
for (let w = 0; w < WAVES.length; w++) {
  let cursor = PLOT_TOP;
  for (const cat of CATEGORIES) {
    const value = POPULATIONS[w][cat.id];
    const height = value * SCALE;
    const node = {
      key: `${w}:${cat.id}`,
      wave: w,
      catId: cat.id,
      label: cat.label,
      color: cat.color,
      value,
      x0: COL_X[w],
      x1: COL_X[w] + NODE_W,
      y0: cursor,
      y1: cursor + height,
      out: [],
      in: [],
    };
    nodes.push(node);
    nodeByKey[node.key] = node;
    cursor = node.y1 + GAP;
  }
}

const flows = [];
TRANSITIONS.forEach((step, t) => {
  step.forEach((f) => {
    const source = nodeByKey[`${t}:${f.source}`];
    const target = nodeByKey[`${t + 1}:${f.target}`];
    const flow = { source, target, count: f.count, stable: f.source === f.target };
    source.out.push(flow);
    target.in.push(flow);
    flows.push(flow);
  });
});

// Stack each node's links along its edge, ordered by the counterpart's fixed
// row rank, so ribbons fan out with minimal crossing near the node.
const rankOf = (catId) => CATEGORY_ORDER.indexOf(catId);
for (const n of nodes) {
  n.out.sort((a, b) => rankOf(a.target.catId) - rankOf(b.target.catId));
  let oc = n.y0;
  for (const f of n.out) {
    f.sy0 = oc;
    f.sy1 = oc + f.count * SCALE;
    f.sx = n.x1;
    oc = f.sy1;
  }
  n.in.sort((a, b) => rankOf(a.source.catId) - rankOf(b.source.catId));
  let ic = n.y0;
  for (const f of n.in) {
    f.ty0 = ic;
    f.ty1 = ic + f.count * SCALE;
    f.tx = n.x0;
    ic = f.ty1;
  }
}

function ribbonPath(xs, ys, f) {
  const cx = (f.sx + f.tx) / 2;
  const P = (x, yPix) => `${xs(x).toFixed(1)} ${ys(H - yPix).toFixed(1)}`;
  const C = (yPix) => `${xs(cx).toFixed(1)} ${ys(H - yPix).toFixed(1)}`;
  return (
    `M ${P(f.sx, f.sy0)} ` +
    `C ${C(f.sy0)}, ${C(f.ty0)}, ${P(f.tx, f.ty0)} ` +
    `L ${P(f.tx, f.ty1)} ` +
    `C ${C(f.ty1)}, ${C(f.sy1)}, ${P(f.sx, f.sy1)} Z`
  );
}

// --- Overlay layers -----------------------------------------------------------
function Links() {
  const xs = useXScale();
  const ys = useYScale();
  return (
    <g>
      {flows.map((f, k) => (
        <path
          key={k}
          d={ribbonPath(xs, ys, f)}
          fill={CATEGORY_BY_ID[f.source.catId].color}
          fillOpacity={f.stable ? 0.55 : 0.16}
        >
          <title>
            {`${f.source.label} (${WAVES[f.source.wave]}) → ${f.target.label} (${WAVES[f.target.wave]}): ${f.count} respondents`}
          </title>
        </path>
      ))}
    </g>
  );
}

function Nodes() {
  const xs = useXScale();
  const ys = useYScale();
  return (
    <g>
      {nodes.map((n) => (
        <rect
          key={n.key}
          x={xs(n.x0).toFixed(1)}
          y={ys(H - n.y0).toFixed(1)}
          width={(xs(n.x1) - xs(n.x0)).toFixed(1)}
          height={(ys(H - n.y1) - ys(H - n.y0)).toFixed(1)}
          fill={n.color}
          rx={3}
        >
          <title>{`${n.label} · ${WAVES[n.wave]}: ${n.value} respondents`}</title>
        </rect>
      ))}
    </g>
  );
}

function Labels() {
  const xs = useXScale();
  const ys = useYScale();
  const firstWaveByCat = Object.fromEntries(CATEGORIES.map((c) => [c.id, POPULATIONS[0][c.id]]));
  return (
    <g fontFamily={FONT}>
      {WAVES.map((label, w) => (
        <text
          key={label}
          x={xs(COL_X[w] + NODE_W / 2)}
          y={ys(H - (PLOT_TOP - 22))}
          textAnchor="middle"
          fontSize={13}
          fontWeight={600}
          letterSpacing={1}
          fill={t.inkSoft}
        >
          {label.toUpperCase()}
        </text>
      ))}
      {nodes.map((n) => {
        const cy = (n.y0 + n.y1) / 2;
        const lx = xs(n.x1) + 10;
        const isLast = n.wave === WAVES.length - 1;
        const delta = isLast ? n.value - firstWaveByCat[n.catId] : null;
        return (
          <g key={n.key}>
            <text x={lx} y={ys(H - (cy - 2))} textAnchor="start" fontSize={13} fontWeight={600} fill={t.ink}>
              {n.label}
            </text>
            <text x={lx} y={ys(H - (cy + 14))} textAnchor="start" fontSize={12} fill={t.inkSoft}>
              {n.value}
            </text>
            {isLast && (
              <text
                x={lx}
                y={ys(H - (cy + 28))}
                textAnchor="start"
                fontSize={12}
                fontWeight={600}
                fill={delta >= 0 ? t.palette[0] : t.palette[4]}
              >
                {delta >= 0 ? `▲ +${delta}` : `▼ ${delta}`}
              </text>
            )}
          </g>
        );
      })}
    </g>
  );
}

function Frame() {
  const xs = useXScale();
  const ys = useYScale();
  return (
    <g fontFamily={FONT}>
      <text x={xs(SIZE.width / 2)} y={ys(H - 40)} textAnchor="middle" fontSize={26} fontWeight={600} fill={t.ink}>
        {TITLE}
      </text>
      <text x={xs(SIZE.width / 2)} y={ys(H - 66)} textAnchor="middle" fontSize={15} fill={t.inkSoft}>
        Quarterly customer-satisfaction survey · 1,000 respondents tracked Q1–Q4 2025
      </text>
      <text x={xs(SIZE.width / 2)} y={ys(H - 90)} textAnchor="middle" fontSize={12} fill={MUTED}>
        Bold ribbon = same rating next wave · Faint ribbon = rating changed · ▲▼ = net change vs Q1
      </text>
    </g>
  );
}

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  return (
    <ChartContainer
      width={SIZE.width}
      height={SIZE.height}
      margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
      series={[]}
      xAxis={[{ id: "x", scaleType: "linear", min: 0, max: SIZE.width }]}
      yAxis={[{ id: "y", scaleType: "linear", min: 0, max: SIZE.height }]}
      skipAnimation
    >
      <Links />
      <Nodes />
      <Labels />
      <Frame />
    </ChartContainer>
  );
}
