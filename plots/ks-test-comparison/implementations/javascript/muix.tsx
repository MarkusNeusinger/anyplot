// anyplot.ai
// ks-test-comparison: Kolmogorov-Smirnov Plot for Distribution Comparison
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-26

import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// --- Deterministic PRNG (LCG) + Box-Muller normal sampler --------------------
let seed = 42;
function nextUniform(): number {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
function nextNormal(mean: number, std: number): number {
  const u1 = nextUniform() || 1e-9;
  const u2 = nextUniform();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + std * z;
}

// --- Data: credit-scoring samples for a model-discrimination check -----------
// Good-standing vs. bad-standing customers should show separated score
// distributions if the scoring model discriminates well.
const SAMPLE_SIZE = 400;
const goodScores = Array.from({ length: SAMPLE_SIZE }, () => nextNormal(680, 55));
const badScores = Array.from({ length: SAMPLE_SIZE }, () => nextNormal(590, 70));

const sortedGood = [...goodScores].sort((a, b) => a - b);
const sortedBad = [...badScores].sort((a, b) => a - b);

// Fraction of a sorted sample that is ≤ x (binary search)
function ecdfAt(sorted: number[], x: number): number {
  let lo = 0;
  let hi = sorted.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (sorted[mid] <= x) lo = mid + 1;
    else hi = mid;
  }
  return lo / sorted.length;
}

// Evaluate both ECDFs at every observed score so the step jumps land exactly
// where either sample has a data point.
const xGrid = [...goodScores, ...badScores].sort((a, b) => a - b);
const ecdfGood = xGrid.map((x) => ecdfAt(sortedGood, x));
const ecdfBad = xGrid.map((x) => ecdfAt(sortedBad, x));

let ksStatistic = 0;
let ksLocation = xGrid[0];
xGrid.forEach((x, i) => {
  const distance = Math.abs(ecdfGood[i] - ecdfBad[i]);
  if (distance > ksStatistic) {
    ksStatistic = distance;
    ksLocation = x;
  }
});

// Asymptotic two-sample K-S p-value (Kolmogorov distribution tail probability)
const effectiveN = (SAMPLE_SIZE * SAMPLE_SIZE) / (SAMPLE_SIZE + SAMPLE_SIZE);
const lambda = (Math.sqrt(effectiveN) + 0.12 + 0.11 / Math.sqrt(effectiveN)) * ksStatistic;
let pValue = 0;
for (let k = 1; k <= 100; k += 1) {
  pValue += 2 * (-1) ** (k - 1) * Math.exp(-2 * k * k * lambda * lambda);
}
pValue = Math.min(1, Math.max(0, pValue));
const pLabel = pValue < 0.001 ? "p < 0.001" : `p = ${pValue.toFixed(3)}`;

const HEADER_HEIGHT = 96;

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, display: "flex", flexDirection: "column", paddingTop: "20px" }}>
      <Typography
        sx={{ color: t.ink, fontSize: 22, fontWeight: 500, textAlign: "center", lineHeight: 1.2 }}
      >
        ks-test-comparison · javascript · muix · anyplot.ai
      </Typography>
      <Typography
        sx={{ color: t.inkSoft, fontSize: 16, textAlign: "center", lineHeight: 1.4, marginTop: "6px" }}
      >
        K-S statistic D = {ksStatistic.toFixed(3)} · {pLabel}
      </Typography>
      <LineChart
        width={width}
        height={height - HEADER_HEIGHT}
        skipAnimation
        series={[
          {
            data: ecdfGood,
            label: "Good-standing customers (n=400)",
            color: t.palette[0],
            curve: "stepAfter" as const,
            showMark: false,
          },
          {
            data: ecdfBad,
            label: "Bad-standing customers (n=400)",
            color: t.palette[4],
            curve: "stepAfter" as const,
            showMark: false,
          },
        ]}
        xAxis={[
          {
            data: xGrid,
            scaleType: "linear",
            label: "Credit Score",
            valueFormatter: (v: number) => `${Math.round(v)}`,
          },
        ]}
        yAxis={[
          {
            label: "Cumulative Proportion",
            min: 0,
            max: 1,
          },
        ]}
        grid={{ horizontal: true }}
        margin={{ left: 90, right: 60, top: 20, bottom: 80 }}
        sx={{
          "& .MuiChartsAxis-tickLabel": { fontSize: "14px" },
          "& .MuiChartsAxis-label": { fontSize: "16px" },
          "& .MuiChartsLegend-label": { fontSize: "14px" },
          "& .MuiLineElement-root": { strokeWidth: 2.5 },
        }}
      >
        <ChartsReferenceLine
          x={ksLocation}
          label={`max |ΔF| at ${Math.round(ksLocation)}`}
          labelAlign="end"
          lineStyle={{ stroke: t.ink, strokeDasharray: "6 4", strokeWidth: 1.5 }}
          labelStyle={{ fill: t.ink, fontSize: 13 }}
        />
      </LineChart>
    </Box>
  );
}
