// anyplot.ai
// boxen-basic: Basic Boxen Plot (Letter-Value Plot)
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-01
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const MAX_LEVELS = 5;
const WIDTH_FACTORS = [1.0, 0.8, 0.62, 0.46, 0.32];
const LEVEL_MIX = [0.86, 0.68, 0.52, 0.37, 0.24];
const LEVEL_NAMES = [
  "Fourths (50%)",
  "Eighths (75%)",
  "Sixteenths (87.5%)",
  "32nds (93.8%)",
  "64ths (96.9%)",
];
const Y_LOW_FACTOR = 0.85;
const Y_HIGH_FACTOR = 1.15;
const BASE_WIDTH_SHARE = 0.56;
const HEADER_H = 108;

// Columns: set these to your data's column names
const CATEGORY = "Service endpoint"; // role: category
const VALUE = "Response time (ms)"; // role: value

// Data: replace this block with your own records, one object per row
const data = (() => {
  let state = 42;
  const endpoints = [
    { name: "/api/search", medianMs: 45, sigma: 0.3 },
    { name: "/api/profile", medianMs: 65, sigma: 0.35 },
    { name: "/api/checkout", medianMs: 120, sigma: 0.45 },
    { name: "/api/upload", medianMs: 260, sigma: 0.55 },
  ];
  const nPerEndpoint = 1500;
  const rows: { [key: string]: string | number }[] = [];

  for (const ep of endpoints) {
    const mu = Math.log(ep.medianMs);
    for (let i = 0; i < nPerEndpoint; i += 1) {
      state = (state * 1664525 + 1013904223) % 4294967296;
      const u1 = Math.max(state / 4294967296, 1e-9);
      state = (state * 1664525 + 1013904223) % 4294967296;
      const u2 = state / 4294967296;
      const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
      const val = Math.exp(mu + ep.sigma * z);
      rows.push({
        [CATEGORY]: ep.name,
        [VALUE]: Number(val.toFixed(2)),
      });
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
const categories: string[] = [];
for (const row of data) {
  const c = String(row[CATEGORY]);
  if (!categories.includes(c)) categories.push(c);
}

const bgInt = parseInt(t.pageBg.slice(1), 16);
const bgRgb = [(bgInt >> 16) & 255, (bgInt >> 8) & 255, bgInt & 255];

const categoryStats = categories.map((name, ci) => {
  const values = data
    .filter((row) => String(row[CATEGORY]) === name)
    .map((row) => Number(row[VALUE]))
    .sort((a, b) => a - b);
  const n = values.length;

  let depth = (n + 1) / 2;
  const medLo = Math.floor(depth) - 1;
  const medHi = Math.ceil(depth) - 1;
  const median = (values[medLo] + values[medHi]) / 2;

  const boxes: { lower: number; upper: number }[] = [];
  for (let i = 0; i < MAX_LEVELS; i += 1) {
    const nextDepth = (Math.floor(depth) + 1) / 2;
    if (nextDepth === depth) break;
    depth = nextDepth;
    const loIdx1 = Math.floor(depth) - 1;
    const loIdx2 = Math.ceil(depth) - 1;
    const lower = (values[loIdx1] + values[loIdx2]) / 2;

    const upDepth = n - depth + 1;
    const hiIdx1 = Math.floor(upDepth) - 1;
    const hiIdx2 = Math.ceil(upDepth) - 1;
    const upper = (values[hiIdx1] + values[hiIdx2]) / 2;

    boxes.push({ lower, upper });
  }

  const outer = boxes[boxes.length - 1] ?? { lower: median, upper: median };
  const outliers = values.filter((v) => v < outer.lower || v > outer.upper);

  const colHex = t.palette[ci];
  const colInt = parseInt(colHex.slice(1), 16);
  const colRgb = [(colInt >> 16) & 255, (colInt >> 8) & 255, colInt & 255];
  const levelFills = LEVEL_MIX.map((mix) => {
    const r = Math.round(bgRgb[0] + (colRgb[0] - bgRgb[0]) * mix);
    const g = Math.round(bgRgb[1] + (colRgb[1] - bgRgb[1]) * mix);
    const b = Math.round(bgRgb[2] + (colRgb[2] - bgRgb[2]) * mix);
    return `rgb(${r}, ${g}, ${b})`;
  });

  return { name, median, boxes, outer, outliers, color: colHex, levelFills };
});

const allExtremes = categoryStats.flatMap((s) => [
  s.outer.lower,
  s.outer.upper,
  ...s.outliers,
]);
const yMin = Math.min(...allExtremes) * Y_LOW_FACTOR;
const yMax = Math.max(...allExtremes) * Y_HIGH_FACTOR;
const levelsDrawn = Math.max(...categoryStats.map((s) => s.boxes.length));
const levelLabels = LEVEL_NAMES.slice(0, levelsDrawn);

const TITLE = "API Response Times · boxen-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${data.length.toLocaleString("en-US")} observations · ${categories.length} groups (${CATEGORY}) · ${levelsDrawn} letter-value levels`;

function BoxenLayer() {
  const xScale = useXScale("endpoints");
  const yScale = useYScale("latency");
  const bandwidth = xScale.bandwidth();
  const baseWidth = bandwidth * BASE_WIDTH_SHARE;

  return (
    <g>
      {categoryStats.map((cat) => {
        const center = xScale(cat.name) + bandwidth / 2;
        const innerWidth = baseWidth * WIDTH_FACTORS[0];
        const yMed = yScale(cat.median);

        return (
          <g key={cat.name}>
            {[...cat.boxes].reverse().map((box, ri) => {
              const idx = cat.boxes.length - 1 - ri;
              const w = baseWidth * WIDTH_FACTORS[idx];
              const yTop = yScale(box.upper);
              const yBottom = yScale(box.lower);
              return (
                <rect
                  key={idx}
                  x={center - w / 2}
                  y={yTop}
                  width={w}
                  height={Math.max(1, yBottom - yTop)}
                  rx={2}
                  fill={cat.levelFills[idx]}
                  stroke={cat.color}
                  strokeWidth={1.4}
                />
              );
            })}
            <line
              x1={center - innerWidth / 2}
              x2={center + innerWidth / 2}
              y1={yMed}
              y2={yMed}
              stroke={t.pageBg}
              strokeWidth={5}
              strokeLinecap="round"
            />
            <line
              x1={center - innerWidth / 2}
              x2={center + innerWidth / 2}
              y1={yMed}
              y2={yMed}
              stroke={t.ink}
              strokeWidth={2.5}
              strokeLinecap="round"
            />
            {cat.outliers.map((v, j) => (
              <circle
                key={j}
                cx={center}
                cy={yScale(v)}
                r={4.5}
                fill={t.pageBg}
                stroke={cat.color}
                strokeWidth={1.8}
              />
            ))}
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const chartHeight = window.ANYPLOT_SIZE.height - HEADER_H;
  const legendSwatches = categoryStats[0].levelFills;
  const brand = t.palette[0];

  return (
    <div
      style={{
        width: window.ANYPLOT_SIZE.width,
        height: window.ANYPLOT_SIZE.height,
        background: t.pageBg,
        fontFamily: "Inter, system-ui, sans-serif",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>
          {TITLE}
        </div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 22,
            fontSize: 14,
            color: t.inkSoft,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
            <div style={{ width: 16, height: 2.5, background: t.ink }} />
            <span>Median</span>
          </div>
          {levelLabels.map((label, idx) => (
            <div
              key={label}
              style={{ display: "flex", alignItems: "center", gap: 7 }}
            >
              <div
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: 3,
                  background: legendSwatches[idx],
                  border: `1.2px solid ${brand}`,
                }}
              />
              <span>{label}</span>
            </div>
          ))}
          <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: "50%",
                background: t.pageBg,
                border: `1.8px solid ${brand}`,
              }}
            />
            <span>Outliers</span>
          </div>
        </div>
      </div>

      <ChartsContainer
        width={window.ANYPLOT_SIZE.width}
        height={chartHeight}
        series={[]}
        skipAnimation
        margin={{ top: 20, right: 40, bottom: 20, left: 40 }}
        xAxis={[
          {
            id: "endpoints",
            data: categories,
            scaleType: "band",
            height: 64,
            label: CATEGORY,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "latency",
            scaleType: "log",
            min: yMin,
            max: yMax,
            width: 88,
            label: VALUE,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": {
            stroke: t.grid,
            opacity: 0.65,
            strokeDasharray: "3 4",
          },
        }}
      >
        <ChartsGrid horizontal />
        <BoxenLayer />
        <ChartsXAxis axisId="endpoints" />
        <ChartsYAxis axisId="latency" />
      </ChartsContainer>
    </div>
  );
}
