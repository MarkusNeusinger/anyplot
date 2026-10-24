// anyplot.ai
// scatter-basic: Basic Scatter Plot
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 88/100 | Created: 2026-06-25

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "scatter-basic · javascript · muix · anyplot.ai";
const MARKER_ALPHA = 0.72;
const MARGIN = { top: 72, right: 52, bottom: 28, left: 24 };

// Columns: set these to your data's column names
const X_VAL = "Weekly Hours on Creative Projects"; // role: x
const Y_VAL = "Innovation Score"; // role: y

// Data: replace this block with your own records
const N_POINTS = 120;
let seed = 42;
const data = Array.from({ length: N_POINTS }, () => {
  seed = (1664525 * seed + 1013904223) >>> 0;
  const uHours = seed / 4294967296;
  seed = (1664525 * seed + 1013904223) >>> 0;
  const u1 = seed / 4294967296;
  seed = (1664525 * seed + 1013904223) >>> 0;
  const u2 = seed / 4294967296;
  const z = Math.sqrt(-2 * Math.log(u1 + 1e-15)) * Math.cos(2 * Math.PI * u2);
  const hours = 2 + uHours * 36;
  const score = 28 + (hours / 40) * 58 + z * 11;
  return {
    [X_VAL]: Math.round(hours * 10) / 10,
    [Y_VAL]: Math.min(98, Math.max(12, Math.round(score * 10) / 10)),
  };
});

// Plot: reads only data and the constants above
const scatterData = data.map((row, id) => ({
  id,
  x: Number(row[X_VAL]),
  y: Number(row[Y_VAL]),
}));

const xs = scatterData.map((p) => p.x);
const ys = scatterData.map((p) => p.y);
const xMinRaw = Math.min(...xs);
const xMaxRaw = Math.max(...xs);
const yMinRaw = Math.min(...ys);
const yMaxRaw = Math.max(...ys);
const xPad = (xMaxRaw - xMinRaw) * 0.08;
const yPad = (yMaxRaw - yMinRaw) * 0.08;
const xMin = Math.max(0, Math.floor(xMinRaw - xPad));
const xMax = Math.ceil(xMaxRaw + xPad);
const yMin = Math.floor(yMinRaw - yPad);
const yMax = Math.ceil(yMaxRaw + yPad);

const p0 = parseInt(t.palette[0].slice(1), 16);
const pointColor = `rgba(${(p0 >> 16) & 255}, ${(p0 >> 8) & 255}, ${p0 & 255}, ${MARKER_ALPHA})`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <ChartsContainer
      width={width}
      height={height}
      margin={MARGIN}
      skipAnimation
      series={[
        {
          type: "scatter",
          id: "observations",
          label: Y_VAL,
          color: pointColor,
          markerSize: 7,
          data: scatterData,
          valueFormatter: (v) => (v ? `${v.x} · ${v.y}` : ""),
        },
      ]}
      xAxis={[
        {
          scaleType: "linear",
          min: xMin,
          max: xMax,
          height: 64,
          label: X_VAL,
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          labelStyle: { fontSize: 16, fill: t.ink },
        },
      ]}
      yAxis={[
        {
          scaleType: "linear",
          min: yMin,
          max: yMax,
          width: 84,
          label: Y_VAL,
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          labelStyle: { fontSize: 16, fill: t.ink },
        },
      ]}
    >
      <ChartsGrid horizontal vertical />
      <ScatterPlot skipAnimation />
      <ChartsXAxis />
      <ChartsYAxis />
      <text
        x={width / 2}
        y={38}
        textAnchor="middle"
        fontSize={22}
        fontWeight={600}
        fill={t.ink}
      >
        {TITLE}
      </text>
    </ChartsContainer>
  );
}
