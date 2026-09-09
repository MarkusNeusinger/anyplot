// anyplot.ai
// violin-box: Violin Plot with Embedded Box Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-09
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const TITLE = "violin-box · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 56;

// --- Data (in-memory, deterministic LCG — no seeded RNG in the browser) -----
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}

function randomNormal(rand, mean, stdDev) {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + z * stdDev;
}

const rand = lcg(7);

// Simple-reaction-time experiment across 4 caffeine-dosage conditions. The
// shapes are deliberately different: placebo carries a slow right-skewed
// "attention lapse" tail, 200mg is the tight, fast optimum, and 300mg turns
// bimodal (impulsive-fast vs. normal-latency) — the overstimulation pattern
// the Yerkes-Dodson law predicts. A plain box plot's median alone would hide
// that split; the violin's KDE makes it visible while the embedded box still
// reports the quartiles.
function sampleReactionTime(dose) {
  let v;
  if (dose === "300 mg") {
    v = rand() < 0.35 ? randomNormal(rand, 350, 22) : randomNormal(rand, 465, 34);
  } else {
    const base = { "0 mg (Placebo)": 515, "100 mg": 468, "200 mg": 408 }[dose];
    const std = { "0 mg (Placebo)": 52, "100 mg": 40, "200 mg": 26 }[dose];
    v = randomNormal(rand, base, std);
    const lapseProb = { "0 mg (Placebo)": 0.06, "100 mg": 0.03, "200 mg": 0.01 }[dose];
    if (rand() < lapseProb) v += 130 + rand() * 110;
  }
  return Math.max(220, v);
}

const N_PER_GROUP = 240;
const categories = ["0 mg (Placebo)", "100 mg", "200 mg", "300 mg"];
const valuesByCategory = categories.map((dose) => Array.from({ length: N_PER_GROUP }, () => sampleReactionTime(dose)));

const allValues = valuesByCategory.flat();
const dataMin = Math.min(...allValues);
const dataMax = Math.max(...allValues);
const yPad = (dataMax - dataMin) * 0.08;
const Y_MIN = dataMin - yPad;
const Y_MAX = dataMax + yPad;

// --- Quartile stats (Tukey whiskers, 1.5×IQR) with explicit outlier points --
function quantile(sorted, q) {
  const pos = (sorted.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  return base + 1 < sorted.length ? sorted[base] + rest * (sorted[base + 1] - sorted[base]) : sorted[base];
}
function boxStats(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const q1 = quantile(sorted, 0.25);
  const median = quantile(sorted, 0.5);
  const q3 = quantile(sorted, 0.75);
  const iqr = q3 - q1;
  const lowerFence = q1 - 1.5 * iqr;
  const upperFence = q3 + 1.5 * iqr;
  const inliers = sorted.filter((v) => v >= lowerFence && v <= upperFence);
  const outliers = sorted.filter((v) => v < lowerFence || v > upperFence);
  return {
    q1,
    median,
    q3,
    whiskerLow: inliers.length ? inliers[0] : q1,
    whiskerHigh: inliers.length ? inliers[inliers.length - 1] : q3,
    outliers,
  };
}
const statsByCategory = valuesByCategory.map(boxStats);

// --- Gaussian KDE per group, Silverman bandwidth, normalized to its own peak
// so each violin shows shape (including 300mg's bimodal split), not sample n.
const GRID_N = 140;
const grid = Array.from({ length: GRID_N }, (_, k) => Y_MIN + (k * (Y_MAX - Y_MIN)) / (GRID_N - 1));
function stdOf(values) {
  const m = values.reduce((a, b) => a + b, 0) / values.length;
  const variance = values.reduce((a, b) => a + (b - m) ** 2, 0) / (values.length - 1);
  return Math.sqrt(variance);
}
function kde(values) {
  const n = values.length;
  const bandwidth = 0.9 * stdOf(values) * Math.pow(n, -0.2);
  const raw = grid.map((gy) => values.reduce((sum, v) => sum + Math.exp(-0.5 * ((gy - v) / bandwidth) ** 2), 0));
  const peak = Math.max(...raw);
  return raw.map((v) => v / peak);
}
const densityByCategory = valuesByCategory.map(kde);

// --- Mirrored violin (KDE on both sides) + inner quartile box + outliers ---
// The community package (7.29.1) has no violin/box-plot component. A custom
// SVG layer positioned via the chart's own band/linear scale hooks reproduces
// one while staying entirely within the community ChartContainer surface —
// the documented "composition" technique for chart types MUI X doesn't ship.
function ViolinBoxes() {
  const xScale = useXScale();
  const yScale = useYScale();
  const bandwidth = xScale.bandwidth();
  const violinHalfWidth = bandwidth * 0.42;
  const boxHalfWidth = Math.min(15, bandwidth * 0.09);

  return (
    <g>
      {categories.map((cat, i) => {
        const color = t.palette[i % t.palette.length];
        const center = xScale(cat) + bandwidth / 2;
        const density = densityByCategory[i];

        const leftSide = grid.map((gy, k) => `${center - density[k] * violinHalfWidth},${yScale(gy)}`);
        const rightSide = grid.map((gy, k) => `${center + density[k] * violinHalfWidth},${yScale(gy)}`).reverse();
        const violinPath = `M${leftSide.join(" L")} L${rightSide.join(" L")} Z`;

        const { q1, median, q3, whiskerLow, whiskerHigh, outliers } = statsByCategory[i];

        return (
          <g key={cat}>
            <path d={violinPath} fill={color} fillOpacity={0.42} stroke={color} strokeWidth={2} strokeLinejoin="round" />
            <line x1={center} x2={center} y1={yScale(whiskerLow)} y2={yScale(whiskerHigh)} stroke={t.ink} strokeWidth={1.5} />
            <rect
              x={center - boxHalfWidth}
              y={yScale(q3)}
              width={boxHalfWidth * 2}
              height={Math.max(1, yScale(q1) - yScale(q3))}
              fill={color}
              stroke={t.pageBg}
              strokeWidth={1.5}
              rx={3}
            />
            <line
              x1={center - boxHalfWidth}
              x2={center + boxHalfWidth}
              y1={yScale(median)}
              y2={yScale(median)}
              stroke={t.pageBg}
              strokeWidth={2.5}
            />
            {outliers.map((v, j) => (
              <circle key={j} cx={center} cy={yScale(v)} r={4.5} fill={t.pageBg} stroke={color} strokeWidth={2} />
            ))}
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const chartHeight = window.ANYPLOT_SIZE.height - TITLE_HEIGHT;

  return (
    <div style={{ width: window.ANYPLOT_SIZE.width, height: window.ANYPLOT_SIZE.height }}>
      <div
        style={{
          height: TITLE_HEIGHT,
          lineHeight: `${TITLE_HEIGHT}px`,
          paddingLeft: 24,
          fontSize: 22,
          fontWeight: 500,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <ChartContainer
        width={window.ANYPLOT_SIZE.width}
        height={chartHeight}
        series={[]}
        skipAnimation
        margin={{ top: 32, right: 50, bottom: 70, left: 105 }}
        xAxis={[
          {
            id: "doses",
            data: categories,
            scaleType: "band",
            label: "Caffeine Dose",
            labelStyle: { fontSize: 16 },
            tickLabelStyle: { fontSize: 14 },
          },
        ]}
        yAxis={[
          {
            id: "reaction",
            min: Y_MIN,
            max: Y_MAX,
            label: "Reaction Time (ms)",
            labelStyle: { fontSize: 16 },
            tickLabelStyle: { fontSize: 14 },
            tickFontSize: 34,
          },
        ]}
      >
        <ChartsGrid
          horizontal
          sx={{
            "& .MuiChartsGrid-line": {
              stroke: t.grid,
              opacity: 0.2,
            },
          }}
        />
        <ViolinBoxes />
        <ChartsXAxis axisId="doses" disableTicks />
        <ChartsYAxis axisId="reaction" />
      </ChartContainer>
    </div>
  );
}
