// anyplot.ai
// stem-basic: Basic Stem Plot
// Library: muix 9.17.0 | JavaScript 22.23.1
// Quality: 87/100 | Created: 2026-07-25
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const BASELINE = 0; // stems start at zero
const X_PAD_SHARE = 0.025;
const Y_PAD_SHARE = 0.1;

// Columns: set these to your data's column names
const SAMPLE = "Sample index (n)"; // role: x
const AMPLITUDE = "Amplitude"; // role: y

// Data: replace this block with your own records, one object per row
// Impulse response of a damped oscillator, sampled at 40 discrete steps
const data = Array.from({ length: 40 }, (_, n) => ({
  [SAMPLE]: n,
  [AMPLITUDE]: Number((Math.exp(-0.12 * n) * Math.cos(0.6 * n)).toFixed(4)),
}));

// Plot: reads only data and the constants above
const rows = data
  .filter((d) => d[SAMPLE] != null && d[AMPLITUDE] != null)
  .sort((a, b) => a[SAMPLE] - b[SAMPLE]);
const xs = rows.map((d) => d[SAMPLE]);
const ys = rows.map((d) => d[AMPLITUDE]);
const points = rows.map((d, i) => ({ x: d[SAMPLE], y: d[AMPLITUDE], id: i }));

const xSpan = Math.max(...xs) - Math.min(...xs);
const yLow = Math.min(...ys, BASELINE);
const yHigh = Math.max(...ys, BASELINE);
const ySpan = yHigh - yLow;
const xMin = Math.min(...xs) - xSpan * X_PAD_SHARE;
const xMax = Math.max(...xs) + xSpan * X_PAD_SHARE;
const yMin = yLow - ySpan * Y_PAD_SHARE;
const yMax = yHigh + ySpan * Y_PAD_SHARE;

const TITLE = "stem-basic · javascript · muix · anyplot.ai";
const TITLE_H = 64;

// One stem per sample, from the baseline to its value; the markers come from ScatterPlot
function Stems() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const y0 = yScale(BASELINE);
  return (
    <g>
      {rows.map((d) => (
        <line
          key={d[SAMPLE]}
          x1={xScale(d[SAMPLE])}
          x2={xScale(d[SAMPLE])}
          y1={y0}
          y2={yScale(d[AMPLITUDE])}
          stroke={t.palette[0]}
          strokeWidth={2.5}
          strokeLinecap="round"
        />
      ))}
    </g>
  );
}

export default function Chart() {
  const { width: W, height: H } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width: W, height: H, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: TITLE_H, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 600 }}>{TITLE}</Typography>
      </Box>
      <ChartsContainer
        skipAnimation
        width={W}
        height={H - TITLE_H}
        margin={{ top: 16, right: 48, bottom: 16, left: 24 }}
        series={[{ type: "scatter", id: "samples", label: AMPLITUDE, data: points, color: t.palette[0], markerSize: 9 }]}
        xAxis={[
          {
            scaleType: "linear",
            min: xMin,
            max: xMax,
            label: SAMPLE,
            tickNumber: 10,
            height: 64,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: yMin,
            max: yMax,
            label: AMPLITUDE,
            tickNumber: 8,
            width: 72,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ChartsGrid horizontal />
        <ChartsReferenceLine y={BASELINE} lineStyle={{ stroke: t.inkSoft, strokeWidth: 1.5 }} />
        <Stems />
        <ScatterPlot />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </Box>
  );
}
