// anyplot.ai
// stem-basic: Basic Stem Plot
// Library: muix 7.29.1 | JavaScript 22.23.1
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
const Y_PAD = 0.15;
const TITLE_HEIGHT = 70;
const MARGIN = { top: 20, right: 50, bottom: 72, left: 96 };

// Columns: set these to your data's column names
const X_POS = "Sample Index (n)"; // role: x
const Y_VAL = "Impulse Response Amplitude"; // role: y

// Data: replace this block with your own records
const nSamplesGen = 40;
const data = Array.from({ length: nSamplesGen }, (_, n) => ({
  [X_POS]: n,
  [Y_VAL]: Number((Math.exp(-0.12 * n) * Math.cos(0.6 * n)).toFixed(4)),
}));

// Plot: reads only data and the constants above
const scatterData = data.map((row, idx) => ({
  id: idx,
  x: Number(row[X_POS]),
  y: Number(row[Y_VAL]),
}));

const xValues = scatterData.map((pt) => pt.x);
const yValues = scatterData.map((pt) => pt.y);
const xMin = Math.min(...xValues) - 1;
const xMax = Math.max(...xValues) + 1;
const yMin = Math.min(...yValues) - Y_PAD;
const yMax = Math.max(...yValues) + Y_PAD;

function Stems() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const y0 = yScale(0);

  return (
    <g>
      {scatterData.map((pt) => (
        <line
          key={pt.id}
          x1={xScale(pt.x)}
          x2={xScale(pt.x)}
          y1={y0}
          y2={yScale(pt.y)}
          stroke={t.palette[0]}
          strokeWidth={2.5}
          strokeLinecap="round"
        />
      ))}
    </g>
  );
}

export default function Chart() {
  const chartWidth = window.ANYPLOT_SIZE.width;
  const chartHeight = window.ANYPLOT_SIZE.height - TITLE_HEIGHT;

  return (
    <Box
      sx={{
        width: chartWidth,
        height: window.ANYPLOT_SIZE.height,
        bgcolor: t.pageBg,
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
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 600 }}>
          Damped Sinusoid Impulse Response · stem-basic · javascript · muix · anyplot.ai
        </Typography>
      </Box>

      <ChartsContainer
        width={chartWidth}
        height={chartHeight}
        margin={MARGIN}
        series={[
          {
            type: "scatter",
            data: scatterData,
            color: t.palette[0],
            markerSize: 9,
          },
        ]}
        xAxis={[
          {
            scaleType: "linear",
            min: xMin,
            max: xMax,
            height: 60,
            label: X_POS,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: yMin,
            max: yMax,
            width: 84,
            label: Y_VAL,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
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
        <ScatterPlot skipAnimation />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
    </Box>
  );
}
