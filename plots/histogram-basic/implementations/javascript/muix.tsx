// anyplot.ai
// histogram-basic: Basic Histogram
// Library: muix 9.17.0 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-26
import { BarChart } from "@mui/x-charts/BarChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TARGET_BINS = 14; // about this many bins; the width is rounded to a 1-2-2.5-5 step
const NICE_STEPS = [1, 2, 2.5, 5, 10];

// Columns: set these to your data's column names
const AGE = "Subscriber Age (years)"; // role: values

// Data: replace this block with your own records, one object per observation
// Ages of 600 streaming-service subscribers: a log-normal draw gives a young-
// skewed base with a long tail of older loyal customers.
const data = (() => {
  let state = 42 >>> 0;
  const rand = () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
  return Array.from({ length: 600 }, () => {
    const z = Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-9))) * Math.cos(2 * Math.PI * rand());
    return { [AGE]: Math.round(Math.min(85, Math.max(16, Math.exp(Math.log(29) + 0.34 * z)))) };
  });
})();

// Plot: reads only data and the constants above
const values = data.map((d) => d[AGE]).filter((v) => v != null);
const minValue = Math.min(...values);
const maxValue = Math.max(...values);
const rawWidth = (maxValue - minValue) / TARGET_BINS;
const magnitude = 10 ** Math.floor(Math.log10(rawWidth));
const binWidth = NICE_STEPS.map((s) => s * magnitude).find((w) => w >= rawWidth);
const binStart = Math.floor(minValue / binWidth) * binWidth;
const binCount = Math.floor((maxValue - binStart) / binWidth) + 1;
// Half-open bins [edge, edge + width): the maximum falls in the last one
const edges = Array.from({ length: binCount + 1 }, (_, i) => Number((binStart + i * binWidth).toPrecision(12)));
const binLabels = edges.slice(0, -1).map((lo, i) => `${lo}–${edges[i + 1]}`);
const counts = new Array(binCount).fill(0);
for (const v of values) counts[Math.floor((v - binStart) / binWidth)] += 1;

const unit = AGE.match(/\(([^)]+)\)/)?.[1] ?? "";
const TITLE = "histogram-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `n = ${values.length} · bin width ${binWidth}${unit ? ` ${unit}` : ""}`;
const COUNT_LABEL = "Frequency (count per bin)";
const HEADER_H = 76;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <Box sx={{ height: HEADER_H, pt: "14px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.3 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.5 }}>{SUBTITLE}</Typography>
      </Box>
      <BarChart
        width={width}
        height={height - HEADER_H}
        skipAnimation
        hideLegend
        borderRadius={0}
        grid={{ horizontal: true }}
        margin={{ top: 12, right: 40, bottom: 16, left: 24 }}
        series={[{ id: "counts", data: counts, label: COUNT_LABEL, color: t.palette[0] }]}
        xAxis={[
          {
            scaleType: "band",
            data: binLabels,
            // Contiguous bins: no gap between bars, the bar stroke marks the edges
            categoryGapRatio: 0,
            height: 64,
            label: AGE,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 0,
            width: 72,
            label: COUNT_LABEL,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        sx={{
          "& .MuiBarChart-element": { stroke: t.pageBg, strokeWidth: 1.5 },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      />
    </Box>
  );
}
