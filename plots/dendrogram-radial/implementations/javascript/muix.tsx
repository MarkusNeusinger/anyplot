// anyplot.ai
// dendrogram-radial: Radial Dendrogram
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-09-05
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

// Data
const SAMPLE_ID = "Sample ID";
const REGION = "Origin Region";
const ACIDITY = "Acidity";
const BODY = "Body";
const SWEETNESS = "Sweetness";
const FLORAL = "Floral Aroma";
const EARTHINESS = "Earthiness";
const SUBTITLE =
  "Complete-linkage clustering of coffee origin sensory profiles · Outer metadata ring by region";

const SAMPLE_PROFILES = [
  { code: "ETH", name: "Ethiopian Highlands", center: [8.5, 3.0, 7.0, 8.5, 1.0] },
  { code: "KEN", name: "Kenyan Highlands", center: [8.8, 4.0, 6.0, 5.0, 1.5] },
  { code: "COL", name: "Colombian Andes", center: [5.5, 6.0, 7.5, 2.5, 2.0] },
  { code: "GUA", name: "Guatemalan Volcanic", center: [6.0, 5.0, 5.5, 4.0, 2.5] },
  { code: "SUM", name: "Sumatran Lowlands", center: [2.0, 8.5, 3.0, 1.0, 8.5] },
];

const DATA: Record<string, string | number>[] = [];
let lcgState = 42 >>> 0;
for (const reg of SAMPLE_PROFILES) {
  for (let s = 0; s < 6; s++) {
    const vals: number[] = [];
    for (let d = 0; d < 5; d++) {
      lcgState = (Math.imul(1664525, lcgState) + 1013904223) >>> 0;
      const u1 = Math.max(lcgState / 4294967296, 1e-9);
      lcgState = (Math.imul(1664525, lcgState) + 1013904223) >>> 0;
      const u2 = lcgState / 4294967296;
      const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
      vals.push(reg.center[d] + z * 0.7);
    }
    DATA.push({
      [SAMPLE_ID]: `${reg.code}-${s + 1}`,
      [REGION]: reg.name,
      [ACIDITY]: vals[0],
      [BODY]: vals[1],
      [SWEETNESS]: vals[2],
      [FLORAL]: vals[3],
      [EARTHINESS]: vals[4],
    });
  }
}

// Constants
const t = window.ANYPLOT_TOKENS;
const FONT = "Inter, system-ui, -apple-system, sans-serif";
const FEATURE_COLS = [ACIDITY, BODY, SWEETNESS, FLORAL, EARTHINESS];
const REF_RINGS = [0.25, 0.5, 0.75, 1.0];
const RING_INNER = 1.06;
const RING_OUTER = 1.13;
const RING_MID = (RING_INNER + RING_OUTER) / 2;
const LABEL_RADIUS = 1.21;
const DOMAIN_LIMIT = 1.38;
const ARC_STEPS = 14;

// Preparation
const n = DATA.length;
const nodeCount = 2 * n - 1;
const REGION_NAMES = Array.from(new Set(DATA.map((d) => String(d[REGION]))));
const REGION_COLORS = Object.fromEntries(
  REGION_NAMES.map((reg, i) => [reg, t.palette[i]])
);

const D = Array.from({ length: nodeCount }, () => new Array(nodeCount).fill(Infinity));
for (let i = 0; i < n; i++) {
  for (let j = i + 1; j < n; j++) {
    let sumSq = 0;
    for (const col of FEATURE_COLS) {
      const diff = Number(DATA[i][col]) - Number(DATA[j][col]);
      sumSq += diff * diff;
    }
    const dist = Math.sqrt(sumSq);
    D[i][j] = dist;
    D[j][i] = dist;
  }
}

const active = new Set(Array.from({ length: n }, (_, i) => i));
const linkage: [number, number, number][] = [];
let nextId = n;
while (active.size > 1) {
  let a = -1;
  let b = -1;
  let best = Infinity;
  const ids = Array.from(active);
  for (let i = 0; i < ids.length; i++) {
    for (let j = i + 1; j < ids.length; j++) {
      if (D[ids[i]][ids[j]] < best) {
        best = D[ids[i]][ids[j]];
        a = ids[i];
        b = ids[j];
      }
    }
  }
  const newId = nextId++;
  active.forEach((c) => {
    if (c === a || c === b) return;
    const d = Math.max(D[a][c], D[b][c]);
    D[newId][c] = d;
    D[c][newId] = d;
  });
  linkage.push([a, b, best]);
  active.delete(a);
  active.delete(b);
  active.add(newId);
}

const root = nextId - 1;
const maxHeight = Math.max(...linkage.map((row) => row[2]));

const order: number[] = [];
const stack: number[] = [root];
while (stack.length > 0) {
  const nodeId = stack.pop()!;
  if (nodeId < n) {
    order.push(nodeId);
  } else {
    const [a, b] = linkage[nodeId - n];
    stack.push(b);
    stack.push(a);
  }
}

const angleOf = new Array(nodeCount).fill(0);
const radiusOf = new Array(nodeCount).fill(0);
const regionOf: (string | null)[] = new Array(nodeCount).fill(null);

order.forEach((leafId, idx) => {
  angleOf[leafId] = Math.PI / 2 - idx * ((2 * Math.PI) / n);
  radiusOf[leafId] = 1;
  regionOf[leafId] = String(DATA[leafId][REGION]);
});

for (let id = n; id < nodeCount; id++) {
  const [a, b, height] = linkage[id - n];
  angleOf[id] = (angleOf[a] + angleOf[b]) / 2;
  radiusOf[id] = 1 - height / maxHeight;
  regionOf[id] =
    regionOf[a] !== null && regionOf[a] === regionOf[b] ? regionOf[a] : null;
}

const scatterSeries = REGION_NAMES.map((reg) => ({
  type: "scatter" as const,
  id: reg,
  data: DATA.map((row, i) => ({ row, i }))
    .filter(({ row }) => row[REGION] === reg)
    .map(({ row, i }) => ({
      id: String(row[SAMPLE_ID]),
      x: Math.cos(angleOf[i]),
      y: Math.sin(angleOf[i]),
    })),
  label: reg,
  color: REGION_COLORS[reg],
  markerSize: 8,
  xAxisId: "x",
  yAxisId: "y",
}));

function RadialDendrogram() {
  const xs = useXScale("x");
  const ys = useYScale("y");
  if (!xs || !ys) return null;

  const cx = xs(0) ?? 0;
  const cy = ys(0) ?? 0;
  const unitPx = Math.abs((xs(1) ?? 0) - cx);
  const ringThickness = Math.abs((xs(RING_OUTER) ?? 0) - (xs(RING_INNER) ?? 0));

  const branches = [];
  for (let id = n; id < nodeCount; id++) {
    const [a, b] = linkage[id - n];
    const rParent = radiusOf[id];
    const bridgeColor =
      regionOf[id] !== null ? REGION_COLORS[regionOf[id]!] : t.inkSoft;

    let diff = angleOf[b] - angleOf[a];
    while (diff > Math.PI) diff -= 2 * Math.PI;
    while (diff < -Math.PI) diff += 2 * Math.PI;
    let dArc = "";
    for (let k = 0; k <= ARC_STEPS; k++) {
      const th = angleOf[a] + (diff * k) / ARC_STEPS;
      const px = xs(rParent * Math.cos(th)) ?? 0;
      const py = ys(rParent * Math.sin(th)) ?? 0;
      dArc += `${k === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)} `;
    }
    branches.push(
      <path
        key={`arc-${id}`}
        d={dArc}
        fill="none"
        stroke={bridgeColor}
        strokeWidth={2.5}
        strokeLinecap="round"
      />
    );

    for (const child of [a, b]) {
      const childColor =
        regionOf[child] !== null ? REGION_COLORS[regionOf[child]!] : t.inkSoft;
      const th = angleOf[child];
      const rChild = radiusOf[child];
      branches.push(
        <line
          key={`seg-${id}-${child}`}
          x1={xs(rParent * Math.cos(th)) ?? 0}
          y1={ys(rParent * Math.sin(th)) ?? 0}
          x2={xs(rChild * Math.cos(th)) ?? 0}
          y2={ys(rChild * Math.sin(th)) ?? 0}
          stroke={childColor}
          strokeWidth={2.5}
          strokeLinecap="round"
        />
      );
    }
  }

  const halfLeafSpan = (Math.PI / n) * 0.72;
  const metadataRing = order.map((leafId) => {
    const th0 = angleOf[leafId] - halfLeafSpan;
    const th1 = angleOf[leafId] + halfLeafSpan;
    let dRing = "";
    for (let k = 0; k <= 4; k++) {
      const th = th0 + ((th1 - th0) * k) / 4;
      const px = xs(RING_MID * Math.cos(th)) ?? 0;
      const py = ys(RING_MID * Math.sin(th)) ?? 0;
      dRing += `${k === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)} `;
    }
    return (
      <path
        key={`ring-${leafId}`}
        d={dRing}
        fill="none"
        stroke={REGION_COLORS[String(DATA[leafId][REGION])]}
        strokeWidth={ringThickness}
        strokeLinecap="butt"
      />
    );
  });

  const labels = order.map((leafId) => {
    const theta = angleOf[leafId];
    const px = xs(LABEL_RADIUS * Math.cos(theta)) ?? 0;
    const py = ys(LABEL_RADIUS * Math.sin(theta)) ?? 0;
    const rotDeg = (Math.atan2(py - cy, px - cx) * 180) / Math.PI;
    const flip = Math.cos(theta) < 0;
    return (
      <text
        key={`label-${leafId}`}
        x={px}
        y={py}
        transform={`rotate(${flip ? rotDeg + 180 : rotDeg}, ${px}, ${py})`}
        textAnchor={flip ? "end" : "start"}
        dominantBaseline="middle"
        fontSize={14}
        fontWeight={500}
        fontFamily={FONT}
        fill={t.inkSoft}
      >
        {String(DATA[leafId][SAMPLE_ID])}
      </text>
    );
  });

  return (
    <g>
      {REF_RINGS.map((frac) => (
        <circle
          key={`ref-${frac}`}
          cx={cx}
          cy={cy}
          r={unitPx * frac}
          fill="none"
          stroke={t.grid}
          strokeWidth={1}
        />
      ))}
      {metadataRing}
      {branches}
      <circle cx={cx} cy={cy} r={5} fill={t.inkSoft} />
      {labels}
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const HEADER_H = 84;
  const LEGEND_H = 76;
  const chartSize = Math.min(W, H - HEADER_H - LEGEND_H);

  return (
    <div
      style={{
        width: W,
        height: H,
        background: t.pageBg,
        fontFamily: FONT,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 4,
          paddingTop: 10,
        }}
      >
        <span style={{ fontSize: 22, fontWeight: 700, color: t.ink }}>
          dendrogram-radial · javascript · muix · anyplot.ai
        </span>
        <span style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</span>
      </div>
      <ChartsContainer
        width={chartSize}
        height={chartSize}
        skipAnimation
        series={scatterSeries}
        margin={{ top: 16, right: 16, bottom: 16, left: 16 }}
        xAxis={[{ id: "x", min: -DOMAIN_LIMIT, max: DOMAIN_LIMIT, position: "none" }]}
        yAxis={[{ id: "y", min: -DOMAIN_LIMIT, max: DOMAIN_LIMIT, position: "none" }]}
      >
        <RadialDendrogram />
        <ScatterPlot />
      </ChartsContainer>
      <div
        style={{
          height: LEGEND_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 28,
          flexWrap: "wrap",
          padding: "0 24px",
        }}
      >
        {REGION_NAMES.map((reg) => (
          <div key={reg} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                width: 14,
                height: 14,
                borderRadius: "50%",
                background: REGION_COLORS[reg],
                display: "inline-block",
              }}
            />
            <span style={{ fontSize: 14, color: t.ink }}>{reg}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
