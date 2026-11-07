// anyplot.ai
// histogram-cumulative: Cumulative Histogram
// Library: muix 9.17.0 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-05
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TARGET_BINS = 12; // about this many bins; the width is rounded to a 1-2-2.5-5 step
const NICE_STEPS = [1, 2, 2.5, 5, 10];
const PERCENT_MAX = 100; // a cumulative share ends at 100 %

// Columns: set these to your data's column names
const WAIT = "Wait Time Before Answer (min)"; // role: value

// Data: replace this block with your own records, one object per observation
// Call-centre wait times before an agent answers, 1,200 calls: a log-normal
// draw where most callers wait a couple of minutes and a tail queues at peak load.
const data = (() => {
  let state = 42 >>> 0;
  const rand = () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
  return Array.from({ length: 1200 }, () => {
    const z = Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-9))) * Math.cos(2 * Math.PI * rand());
    return { [WAIT]: Number(Math.min(12, Math.exp(Math.log(2.2) + 0.45 * z)).toFixed(2)) };
  });
})();

// Plot: reads only data and the constants above
const values = data.map((d) => d[WAIT]).filter((v) => v != null);
const n = values.length;
const minValue = Math.min(...values);
const maxValue = Math.max(...values);
const rawWidth = (maxValue - minValue) / TARGET_BINS;
const magnitude = 10 ** Math.floor(Math.log10(rawWidth));
const binWidth = NICE_STEPS.map((s) => s * magnitude).find((w) => w >= rawWidth);
const binStart = Math.floor(minValue / binWidth) * binWidth;
const binCount = Math.floor((maxValue - binStart) / binWidth) + 1;
const edges = Array.from({ length: binCount + 1 }, (_, i) => Number((binStart + i * binWidth).toPrecision(12)));
// Half-open bins [edge, edge + width): the maximum falls in the last one
const counts = new Array(binCount).fill(0);
for (const v of values) counts[Math.floor((v - binStart) / binWidth)] += 1;
// One level per bin at the running share up to its upper edge; the leading 0
// anchors the first step at the lower edge of the first bin
const cumulativeShare = [0];
let running = 0;
for (const c of counts) {
  running += c;
  cumulativeShare.push((running / n) * PERCENT_MAX);
}

const sorted = [...values].sort((a, b) => a - b);
const median = n % 2 ? sorted[(n - 1) / 2] : (sorted[n / 2 - 1] + sorted[n / 2]) / 2;

const unit = WAIT.match(/\(([^)]+)\)/)?.[1] ?? "";
const unitSuffix = unit ? ` ${unit}` : "";
const TITLE = "histogram-cumulative · javascript · muix · anyplot.ai";
const SUBTITLE = `n = ${n.toLocaleString("en-US")} · bin width ${binWidth}${unitSuffix} · dashed line: median`;
const SHARE_LABEL = "Cumulative share (%)";
const HEADER_H = 76;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <Box sx={{ height: HEADER_H, pt: "14px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.3 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.5 }}>{SUBTITLE}</Typography>
      </Box>
      <LineChart
        width={width}
        height={height - HEADER_H}
        skipAnimation
        hideLegend
        grid={{ horizontal: true }}
        margin={{ top: 16, right: 40, bottom: 16, left: 24 }}
        series={[
          {
            id: "cumulative",
            data: cumulativeShare,
            label: SHARE_LABEL,
            color: t.palette[0],
            curve: "stepBefore",
            area: true,
            showMark: false,
            valueFormatter: (v) => `${v.toFixed(1)} %`,
          },
        ]}
        xAxis={[
          {
            data: edges,
            scaleType: "linear",
            min: edges[0],
            max: edges[edges.length - 1],
            tickInterval: edges,
            valueFormatter: (v: number) => String(v),
            height: 64,
            label: WAIT,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: PERCENT_MAX,
            width: 72,
            label: SHARE_LABEL,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        sx={{
          "& .MuiLineChart-area": { fillOpacity: 0.18 },
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ChartsReferenceLine
          x={median}
          label={`Median ${median.toFixed(1)}${unitSuffix}`}
          labelAlign="start"
          labelStyle={{ fontSize: 15, fill: t.inkSoft }}
          lineStyle={{ stroke: t.inkSoft, strokeWidth: 1.5, strokeDasharray: "6 4" }}
        />
      </LineChart>
    </Box>
  );
}
