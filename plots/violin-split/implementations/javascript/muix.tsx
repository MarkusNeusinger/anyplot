// anyplot.ai
// violin-split: Split Violin Plot
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-09
import { Box, Typography } from "@mui/material";
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

const CAT_AXIS_ID = "category-axis";
const VAL_AXIS_ID = "value-axis";

// --- Data (in-memory, deterministic — tiny fixed-seed LCG) ------------------
function makeLcg(seed: number) {
  let state = seed >>> 0;
  return function next() {
    state = (Math.imul(1664525, state) + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rng = makeLcg(20260909);

function gaussian(mean: number, std: number) {
  let u1 = rng();
  while (u1 <= 1e-12) u1 = rng();
  const u2 = rng();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * std;
}

function clamp(v: number, lo: number, hi: number) {
  return Math.min(hi, Math.max(lo, v));
}

const N_PER_GROUP = 140;
const SPLIT_GROUPS = ["Control group", "Experimental group"];

const CATEGORY_PARAMS = [
  {
    name: "Mathematics",
    control: { mean: 68, std: 11 },
    experimental: { mean: 74, std: 9 },
  },
  {
    name: "Science",
    control: { mean: 74, std: 9 },
    experimental: { mean: 80, std: 7 },
  },
  {
    name: "Language Arts",
    control: { mean: 76, std: 8 },
    experimental: { mean: 81, std: 7 },
  },
  {
    name: "History",
    control: { mean: 70, std: 10 },
    experimental: { mean: 76, std: 8 },
  },
];
const CATEGORIES = CATEGORY_PARAMS.map((c) => c.name);

const DATA: Record<string, Record<string, number[]>> = {};
CATEGORY_PARAMS.forEach(({ name, control, experimental }) => {
  DATA[name] = {
    // Only the physical floor (0) is clamped — a hard clamp at 100 would pile
    // up upper-tail samples on the boundary and flatten the violin's tip.
    "Control group": Array.from({ length: N_PER_GROUP }, () =>
      clamp(gaussian(control.mean, control.std), 0, Infinity),
    ),
    "Experimental group": Array.from({ length: N_PER_GROUP }, () =>
      clamp(gaussian(experimental.mean, experimental.std), 0, Infinity),
    ),
  };
});

const ALL_VALUES = CATEGORIES.flatMap((cat) =>
  SPLIT_GROUPS.flatMap((grp) => DATA[cat][grp]),
);
const RAW_MIN = Math.min(...ALL_VALUES);
const RAW_MAX = Math.max(...ALL_VALUES);
const PAD = (RAW_MAX - RAW_MIN) * 0.1;
const Y_MIN = Math.max(0, Math.floor(RAW_MIN - PAD));
// Test scores don't exceed 100 — cap the axis window there. The underlying
// data stays unclamped (see above) so the KDE tail decays smoothly into this
// boundary instead of piling up on it.
const Y_MAX = Math.min(100, Math.ceil(RAW_MAX + PAD));

const GRID_N = 140;
const GRID_Y = Array.from(
  { length: GRID_N },
  (_, i) => Y_MIN + ((Y_MAX - Y_MIN) * i) / (GRID_N - 1),
);

const GROUP_COLORS = [t.palette[0], t.palette[1]];

// --- KDE (Gaussian kernel, Silverman bandwidth) — draws the violin curves ---
function silvermanBandwidth(values: number[]) {
  const n = values.length;
  const mean = values.reduce((s, v) => s + v, 0) / n;
  const variance = values.reduce((s, v) => s + (v - mean) ** 2, 0) / (n - 1);
  const sigma = Math.sqrt(variance) || 1;
  return Math.max(0.9 * sigma * Math.pow(n, -0.2), 0.6);
}

function kdeCurve(values: number[], gridY: number[]) {
  const h = silvermanBandwidth(values);
  const n = values.length;
  const norm = 1 / (n * h * Math.sqrt(2 * Math.PI));
  return gridY.map((y) => {
    let sum = 0;
    for (let i = 0; i < n; i++) {
      const u = (y - values[i]) / h;
      sum += Math.exp(-0.5 * u * u);
    }
    return sum * norm;
  });
}

// Trims the near-zero density tails so each half pinches to the center spine
// instead of drawing a near-invisible sliver across the whole y-range.
function trimToSupport(density: number[], thresholdRatio: number) {
  const max = Math.max(...density);
  const threshold = max * thresholdRatio;
  let lo = 0;
  let hi = density.length - 1;
  while (lo < hi && density[lo] < threshold) lo++;
  while (hi > lo && density[hi] < threshold) hi--;
  lo = Math.max(0, lo - 1);
  hi = Math.min(density.length - 1, hi + 1);
  return { lo, hi, max };
}

function quartileStats(values: number[]) {
  const sorted = [...values].sort((a, b) => a - b);
  const quantile = (p: number) => {
    const pos = (sorted.length - 1) * p;
    const base = Math.floor(pos);
    const rest = pos - base;
    return sorted[base + 1] !== undefined
      ? sorted[base] + rest * (sorted[base + 1] - sorted[base])
      : sorted[base];
  };
  return { q1: quantile(0.25), median: quantile(0.5), q3: quantile(0.75) };
}

// --- Custom-drawn split violins (community @mui/x-charts has no built-in
// violin mark — composed from ChartContainer's cartesian scales instead) ----
function Violins() {
  const xScale = useXScale(CAT_AXIS_ID);
  const yScale = useYScale(VAL_AXIS_ID);

  return (
    <>
      {CATEGORIES.map((cat) => {
        const bandStart = xScale(cat);
        if (bandStart === undefined) return null;
        const bandwidth = xScale.bandwidth();
        const cx = bandStart + bandwidth / 2;
        const halfWidthMax = bandwidth * 0.42;

        return (
          <g key={cat}>
            {SPLIT_GROUPS.map((grp, gi) => {
              const values = DATA[cat][grp];
              const density = kdeCurve(values, GRID_Y);
              const { lo, hi, max } = trimToSupport(density, 0.01);
              const side = gi === 0 ? -1 : 1;
              const color = GROUP_COLORS[gi];

              const points: [number, number][] = [];
              for (let i = lo; i <= hi; i++) {
                const w = (density[i] / max) * halfWidthMax;
                points.push([cx + side * w, yScale(GRID_Y[i]) as number]);
              }
              const d =
                `M ${cx} ${points[0][1]} ` +
                points.map(([x, y]) => `L ${x} ${y}`).join(" ") +
                ` L ${cx} ${points[points.length - 1][1]} Z`;

              const { q1, median, q3 } = quartileStats(values);
              const markerX = cx + side * 7;

              return (
                <g key={grp}>
                  <path
                    d={d}
                    fill={color}
                    fillOpacity={0.75}
                    stroke={color}
                    strokeWidth={1.5}
                    strokeOpacity={0.95}
                    strokeLinejoin="round"
                  />
                  <line
                    x1={markerX}
                    x2={markerX}
                    y1={yScale(q1)}
                    y2={yScale(q3)}
                    stroke={t.pageBg}
                    strokeWidth={5}
                    strokeLinecap="round"
                    opacity={0.85}
                  />
                  <circle
                    cx={markerX}
                    cy={yScale(median)}
                    r={4.5}
                    fill={t.pageBg}
                    stroke={color}
                    strokeWidth={1.5}
                  />
                </g>
              );
            })}
          </g>
        );
      })}
    </>
  );
}

// --- Chart (default-exported component — the harness mounts it) -----------
export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const TITLE_H = 46;
  const LEGEND_H = 34;
  const CHART_H = H - TITLE_H - LEGEND_H;

  return (
    <Box sx={{ width: W, height: H, display: "flex", flexDirection: "column" }}>
      <Typography
        sx={{
          height: TITLE_H,
          lineHeight: `${TITLE_H}px`,
          fontSize: 22,
          fontWeight: 700,
          textAlign: "center",
        }}
      >
        violin-split · javascript · muix · anyplot.ai
      </Typography>
      <Box
        sx={{
          height: LEGEND_H,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          gap: 4,
        }}
      >
        {SPLIT_GROUPS.map((grp, i) => (
          <Box key={grp} sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Box
              sx={{
                width: 16,
                height: 16,
                borderRadius: "3px",
                backgroundColor: GROUP_COLORS[i],
              }}
            />
            <Typography sx={{ fontSize: 16, color: "text.secondary" }}>
              {grp}
            </Typography>
          </Box>
        ))}
      </Box>
      <ChartContainer
        width={W}
        height={CHART_H}
        series={[]}
        margin={{ top: 20, right: 50, bottom: 74, left: 96 }}
        xAxis={[
          {
            id: CAT_AXIS_ID,
            scaleType: "band",
            data: CATEGORIES,
            label: "Subject",
            tickLabelStyle: { fontSize: 14 },
            labelStyle: { fontSize: 16, fontWeight: 600 },
          },
        ]}
        yAxis={[
          {
            id: VAL_AXIS_ID,
            scaleType: "linear",
            min: Y_MIN,
            max: Y_MAX,
            label: "Test score (points)",
            tickLabelStyle: { fontSize: 14 },
            labelStyle: { fontSize: 16, fontWeight: 600 },
          },
        ]}
      >
        <ChartsGrid horizontal />
        <Violins />
        <ChartsXAxis axisId={CAT_AXIS_ID} position="bottom" />
        <ChartsYAxis axisId={VAL_AXIS_ID} position="left" />
      </ChartContainer>
    </Box>
  );
}
