// anyplot.ai
// ecdf-basic: Basic ECDF Plot
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 82/100 | Created: 2026-06-25
//# anyplot-orientation: landscape
// anyplot.ai
// ecdf-basic: Basic ECDF Plot
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-25

import { LineChart } from "@mui/x-charts/LineChart";

const t = window.ANYPLOT_TOKENS;

// Seeded LCG for deterministic data generation (no seeded RNG in browser)
let seed = 42;
function rand() {
  seed = (Math.imul(1664525, seed) + 1013904223) | 0;
  return (seed >>> 0) / 4294967296;
}
function randn() {
  const u = Math.max(rand(), 1e-10);
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rand());
}
function normalSorted(mean, std, n) {
  return Array.from({ length: n }, () => mean + std * randn()).sort((a, b) => a - b);
}

// Exam scores from two teaching methods, 80 students each
const N = 80;
const traditional = normalSorted(72, 12, N);   // Traditional instruction: μ=72, σ=12
const projectBased = normalSorted(78, 10, N);  // Project-based learning:  μ=78, σ=10

// Merge and sort all x-values to build a shared axis for both ECDF curves
const allX = [...traditional, ...projectBased].sort((a, b) => a - b);

// ECDF: fraction of observations ≤ x evaluated at every merged x-value
function computeEcdf(sorted, xValues) {
  let j = 0;
  return xValues.map((x) => {
    while (j < sorted.length && sorted[j] <= x) j++;
    return j / sorted.length;
  });
}

const ecdfTrad = computeEcdf(traditional, allX);
const ecdfProj = computeEcdf(projectBased, allX);

const TITLE_H = 52;

export default function Chart() {
  return (
    <div
      style={{
        width: window.ANYPLOT_SIZE.width,
        height: window.ANYPLOT_SIZE.height,
        display: "flex",
        flexDirection: "column",
        backgroundColor: t.pageBg,
      }}
    >
      <div
        style={{
          padding: "18px 36px 0",
          fontSize: 22,
          fontWeight: 500,
          color: t.ink,
          height: TITLE_H,
          boxSizing: "border-box",
          fontFamily: "sans-serif",
        }}
      >
        ecdf-basic · javascript · muix · anyplot.ai
      </div>
      <LineChart
        width={window.ANYPLOT_SIZE.width}
        height={window.ANYPLOT_SIZE.height - TITLE_H}
        skipAnimation
        series={[
          {
            data: ecdfTrad,
            curve: "stepAfter",
            label: "Traditional Teaching",
            showMark: false,
            color: t.palette[0],
          },
          {
            data: ecdfProj,
            curve: "stepAfter",
            label: "Project-based Learning",
            showMark: false,
            color: t.palette[1],
          },
        ]}
        xAxis={[
          {
            data: allX,
            label: "Exam Score",
            tickMinStep: 10,
            valueFormatter: (v) => String(Math.round(v)),
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: 1,
            label: "Cumulative Proportion",
            tickMinStep: 0.25,
            valueFormatter: (v) => `${Math.round(v * 100)}%`,
          },
        ]}
        grid={{ horizontal: true }}
        sx={{
          "& .MuiLineElement-root": { strokeWidth: 2.5 },
          "& .MuiChartsGrid-line": { strokeOpacity: 0.12 },
        }}
        margin={{ left: 90, right: 30, top: 20, bottom: 100 }}
      />
    </div>
  );
}
