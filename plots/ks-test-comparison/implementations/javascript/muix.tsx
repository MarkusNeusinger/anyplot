// anyplot.ai
// ks-test-comparison: Kolmogorov-Smirnov Plot for Distribution Comparison
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 88/100 | Updated: 2026-11-08
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const CDF_MIN = 0; // a cumulative proportion runs from 0 to 1
const CDF_MAX = 1;
const CDF_TICKS = 10; // tick steps between CDF_MIN and CDF_MAX
const X_PAD_SHARE = 0.04; // share of the value range shown beyond the smallest and largest value
const Y_PAD_SHARE = 0.02; // room below 0 and above 1 so the flat ends of the steps stay visible
const KOLMOGOROV_TERMS = 100; // terms of the alternating series for the asymptotic p-value

// Columns: set these to your data's column names
const GOOD = "Good-standing customers"; // role: sample1
const BAD = "Bad-standing customers"; // role: sample2
const MEASURE = "Credit score (points)"; // the quantity both sample columns hold, with its unit: the x-axis title

// Data: replace this block with your own records, one object per row; a shorter sample
// leaves its cells null
// Model scores of 400 good- and 400 bad-standing customers of a credit-scoring model that
// separates the two groups: good ~ N(680, 55), bad ~ N(590, 70).
const data = (() => {
  let seed = 42;
  const uniform = () => {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
  const normal = (mean: number, sd: number) =>
    mean + sd * Math.sqrt(-2 * Math.log(uniform() || 1e-9)) * Math.cos(2 * Math.PI * uniform());
  const good = Array.from({ length: 400 }, () => normal(680, 55));
  const bad = Array.from({ length: 400 }, () => normal(590, 70));
  return good.map((g, i) => ({ [GOOD]: Number(g.toFixed(1)), [BAD]: Number(bad[i].toFixed(1)) }));
})();

// Plot: reads only data and the constants above
const sample1 = data.map((d) => d[GOOD]).filter((v) => v != null).sort((a, b) => a - b);
const sample2 = data.map((d) => d[BAD]).filter((v) => v != null).sort((a, b) => a - b);
const n1 = sample1.length;
const n2 = sample2.length;

// Both ECDFs on the union of observed values, one step at each value, plus one point
// beyond each end so the curves start at 0 and reach 1 inside the axis
const values = [...new Set([...sample1, ...sample2])].sort((a, b) => a - b);
const xPad = (values[values.length - 1] - values[0]) * X_PAD_SHARE;
const grid = [values[0] - xPad, ...values, values[values.length - 1] + xPad];
const ecdf1: number[] = [];
const ecdf2: number[] = [];
let below1 = 0;
let below2 = 0;
for (const x of grid) {
  while (below1 < n1 && sample1[below1] <= x) below1 += 1;
  while (below2 < n2 && sample2[below2] <= x) below2 += 1;
  ecdf1.push(below1 / n1);
  ecdf2.push(below2 / n2);
}

// K-S statistic D: the largest vertical distance between the two step functions
const gaps = grid.map((_, i) => Math.abs(ecdf1[i] - ecdf2[i]));
const dIndex = gaps.indexOf(Math.max(...gaps));
const dStatistic = gaps[dIndex];
const dX = grid[dIndex];

// Asymptotic two-sample p-value from the Kolmogorov distribution, with the effective
// sample size n1·n2 / (n1 + n2) and Stephens' small-sample correction
const effectiveN = (n1 * n2) / (n1 + n2);
const lambda = (Math.sqrt(effectiveN) + 0.12 + 0.11 / Math.sqrt(effectiveN)) * dStatistic;
let pSeries = 0;
for (let k = 1; k <= KOLMOGOROV_TERMS; k += 1) {
  pSeries += 2 * (-1) ** (k - 1) * Math.exp(-2 * k * k * lambda * lambda);
}
const pValue = Math.min(1, Math.max(0, pSeries));
const pLabel = pValue < 0.001 ? "p < 0.001" : `p = ${pValue.toFixed(3)}`;

const TITLE = "ks-test-comparison · javascript · muix · anyplot.ai";
const STAT_LINE = `K-S statistic D = ${dStatistic.toFixed(3)} · ${pLabel}`;
const SAMPLE_LINE = `two-sample test, n = ${n1} and ${n2} · bar: the largest gap between the two ECDFs`;
const HEADER_H = 108;
const LEGEND_H = 44;

function GapBar() {
  const xScale = useXScale();
  const yScale = useYScale();
  const x = xScale(dX);
  const yTop = yScale(Math.max(ecdf1[dIndex], ecdf2[dIndex]));
  const yBottom = yScale(Math.min(ecdf1[dIndex], ecdf2[dIndex]));
  return (
    <g>
      <line x1={x} x2={x} y1={yTop} y2={yBottom} stroke={t.ink} strokeWidth={4} />
      <circle cx={x} cy={yTop} r={6} fill={t.ink} stroke={t.pageBg} strokeWidth={1.5} />
      <circle cx={x} cy={yBottom} r={6} fill={t.ink} stroke={t.pageBg} strokeWidth={1.5} />
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <Box sx={{ height: HEADER_H, pt: "14px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.3 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 18, fontWeight: 600, color: t.ink, lineHeight: 1.5 }}>{STAT_LINE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.5 }}>{SAMPLE_LINE}</Typography>
      </Box>
      <LineChart
        width={width}
        height={height - HEADER_H - LEGEND_H}
        skipAnimation
        grid={{ horizontal: true }}
        margin={{ top: 12, right: 40, bottom: 8, left: 20 }}
        series={[
          {
            id: "sample1",
            data: ecdf1,
            label: `${GOOD} (n = ${n1})`,
            color: t.palette[0],
            curve: "stepAfter",
            showMark: false,
            labelMarkType: "line",
          },
          {
            id: "sample2",
            data: ecdf2,
            label: `${BAD} (n = ${n2})`,
            color: t.palette[1],
            curve: "stepAfter",
            showMark: false,
            labelMarkType: "line",
          },
        ]}
        xAxis={[
          {
            data: grid,
            scaleType: "linear",
            min: grid[0],
            max: grid[grid.length - 1],
            label: MEASURE,
            height: 64,
            valueFormatter: (v: number) => String(Math.round(v)),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: CDF_MIN - (CDF_MAX - CDF_MIN) * Y_PAD_SHARE,
            max: CDF_MAX + (CDF_MAX - CDF_MIN) * Y_PAD_SHARE,
            tickInterval: Array.from({ length: CDF_TICKS + 1 }, (_, i) => CDF_MIN + ((CDF_MAX - CDF_MIN) * i) / CDF_TICKS),
            valueFormatter: (v: number) => v.toFixed(1),
            width: 72,
            label: "Cumulative proportion",
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "center" },
            sx: { fontSize: 15, color: t.ink, gap: "36px" },
          },
        }}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ChartsReferenceLine
          x={dX}
          label={`largest gap at ${Math.round(dX)}`}
          labelAlign="start"
          spacing={{ x: 10, y: 8 }}
          labelStyle={{ fontSize: 15, fill: t.inkSoft }}
          lineStyle={{ stroke: t.inkSoft, strokeWidth: 1.5, strokeDasharray: "6 4" }}
        />
        <GapBar />
      </LineChart>
    </Box>
  );
}
