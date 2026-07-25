// anyplot.ai
// stem-basic: Basic Stem Plot
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 87/100 | Created: 2026-07-25
//# anyplot-orientation: landscape
// anyplot.ai
// stem-basic: Basic Stem Plot
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-07-25

import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// --- Data: damped-sinusoid impulse response, 40 discrete samples ------------
const N_SAMPLES = 40;
const sampleIndex = Array.from({ length: N_SAMPLES }, (_, n) => n);
const amplitude = sampleIndex.map((n) => Math.exp(-0.12 * n) * Math.cos(0.6 * n));
const scatterData = sampleIndex.map((n, i) => ({ x: n, y: amplitude[i], id: i }));

const Y_PAD = 0.15;
const yMin = Math.min(...amplitude) - Y_PAD;
const yMax = Math.max(...amplitude) + Y_PAD;

// Renders the stems (baseline-to-value lines); markers come from ScatterPlot.
// Must be rendered inside ChartContainer to access its scale context.
function Stems() {
  const xScale = useXScale();
  const yScale = useYScale();
  const y0 = yScale(0);

  return (
    <g>
      {sampleIndex.map((n, i) => (
        <line
          key={n}
          x1={xScale(n)}
          x2={xScale(n)}
          y1={y0}
          y2={yScale(amplitude[i])}
          stroke={t.palette[0]}
          strokeWidth={2.5}
          strokeLinecap="round"
        />
      ))}
    </g>
  );
}

const TITLE = "stem-basic · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 70;
const MARGIN = { top: 20, right: 50, bottom: 70, left: 90 };

export default function Chart() {
  const chartWidth = window.ANYPLOT_SIZE.width;
  const chartHeight = window.ANYPLOT_SIZE.height - TITLE_HEIGHT;

  return (
    <Box
      sx={{
        width: chartWidth,
        height: window.ANYPLOT_SIZE.height,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box
        sx={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 500 }}>
          {TITLE}
        </Typography>
      </Box>

      <ChartContainer
        skipAnimation
        width={chartWidth}
        height={chartHeight}
        margin={MARGIN}
        series={[{
          type: "scatter",
          data: scatterData,
          color: t.palette[0],
          markerSize: 9,
        }]}
        xAxis={[{
          scaleType: "linear",
          min: -1,
          max: N_SAMPLES,
          label: "Sample Index (n)",
          labelStyle: { fontSize: 15, fill: t.ink },
          tickLabelStyle: { fontSize: 13, fill: t.inkSoft },
        }]}
        yAxis={[{
          scaleType: "linear",
          min: yMin,
          max: yMax,
          label: "Amplitude",
          labelStyle: { fontSize: 15, fill: t.ink },
          tickLabelStyle: { fontSize: 13, fill: t.inkSoft },
        }]}
        sx={{
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeOpacity: 0.5 },
        }}
      >
        <ChartsGrid horizontal />
        <ChartsReferenceLine
          y={0}
          lineStyle={{ stroke: t.inkSoft, strokeWidth: 1.5 }}
        />
        <Stems />
        <ScatterPlot />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartContainer>
    </Box>
  );
}
