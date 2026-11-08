// anyplot.ai
// scatter-constellation-diagram: Digital Modulation Constellation Diagram
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: pending | Created: 2026-06-18
//# anyplot-orientation: square

import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const IDEAL_COLOR = t.palette[4]; // matte red: the spec's convention for the ideal reference markers
const EXTENT_PAD_SHARE = 0.25; // room beyond the outermost symbol, as a share of its distance from the origin
const RECEIVED_OPACITY = 0.45;
const TICK_COUNT = 8; // about this many ticks per axis

// Columns: set these to your data's column names
const I = "In-Phase (I)"; // role: i
const Q = "Quadrature (Q)"; // role: q
const IDEAL_I = "Ideal I"; // role: ideal_i
const IDEAL_Q = "Ideal Q"; // role: ideal_q

// Data: replace this block with your own records, one object per row
// 16-QAM received symbols with additive Gaussian noise (sigma 0.15 per axis),
// each row carrying the ideal constellation point it was sent as.
const data = (() => {
  let seed = 42;
  const uniform = () => {
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    return seed / 0x100000000;
  };
  const noise = () => 0.15 * Math.sqrt(-2 * Math.log(Math.max(1e-10, uniform()))) * Math.cos(2 * Math.PI * uniform());
  const levels = [-3, -1, 1, 3];
  const rows = [];
  for (const iq of levels) {
    for (const ii of levels) {
      for (let k = 0; k < 62; k += 1) {
        rows.push({
          [I]: Number((ii + noise()).toFixed(3)),
          [Q]: Number((iq + noise()).toFixed(3)),
          [IDEAL_I]: ii,
          [IDEAL_Q]: iq,
        });
      }
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
const idealKeys = [...new Set(data.map((d) => `${d[IDEAL_I]}|${d[IDEAL_Q]}`))];
const idealPoints = idealKeys.map((key, k) => {
  const row = data.find((d) => `${d[IDEAL_I]}|${d[IDEAL_Q]}` === key);
  return { id: `ideal-${k}`, x: row[IDEAL_I], y: row[IDEAL_Q] };
});
const receivedPoints = data.map((d, k) => ({ id: `rx-${k}`, x: d[I], y: d[Q] }));

// RMS error vector magnitude, normalised by the mean power of the ideal symbols sent
const errorPower = data.reduce((s, d) => s + (d[I] - d[IDEAL_I]) ** 2 + (d[Q] - d[IDEAL_Q]) ** 2, 0) / data.length;
const idealPower = data.reduce((s, d) => s + d[IDEAL_I] ** 2 + d[IDEAL_Q] ** 2, 0) / data.length;
const evmPercent = Math.sqrt(errorPower / idealPower) * 100;

// Decision boundaries run midway between neighbouring ideal levels on each axis
const iLevels = [...new Set(data.map((d) => d[IDEAL_I]))].sort((a, b) => a - b);
const qLevels = [...new Set(data.map((d) => d[IDEAL_Q]))].sort((a, b) => a - b);
const iBoundaries = iLevels.slice(1).map((v, k) => (v + iLevels[k]) / 2);
const qBoundaries = qLevels.slice(1).map((v, k) => (v + qLevels[k]) / 2);

// One symmetric extent on both axes, centred on the origin
const reach = Math.max(...data.flatMap((d) => [Math.abs(d[I]), Math.abs(d[Q]), Math.abs(d[IDEAL_I]), Math.abs(d[IDEAL_Q])]));
const extent = reach * (1 + EXTENT_PAD_SHARE);

const TITLE = "scatter-constellation-diagram · javascript · muix · anyplot.ai";
const SUBTITLE = `${data.length} received symbols around ${idealPoints.length} ideal points · dashed lines: decision boundaries`;
const HEADER_HEIGHT = 84;
const LEGEND_HEIGHT = 40;
const X_AXIS_HEIGHT = 64;
const Y_AXIS_WIDTH = 72;
const chartWidth = window.ANYPLOT_SIZE.width;
const chartHeight = window.ANYPLOT_SIZE.height - HEADER_HEIGHT - LEGEND_HEIGHT;

// A square drawing area keeps px per unit equal on both axes, so the grid geometry is true
const side = Math.min(chartWidth - Y_AXIS_WIDTH - 48, chartHeight - X_AXIS_HEIGHT - 24);
const marginX = (chartWidth - Y_AXIS_WIDTH - side) / 2;
const marginY = (chartHeight - X_AXIS_HEIGHT - side) / 2;

const boundaryStyle = { stroke: t.inkSoft, strokeOpacity: 0.6, strokeWidth: 1.5, strokeDasharray: "9 6" };

function EvmLabel() {
  const { left, top } = useDrawingArea();
  return (
    <text
      x={left + 18}
      y={top + 34}
      fontSize={20}
      fontWeight={600}
      fill={t.ink}
      stroke={t.pageBg}
      strokeWidth={4}
      paintOrder="stroke"
    >
      {`EVM = ${evmPercent.toFixed(1)}%`}
    </text>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_HEIGHT,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>
      <ChartsDataProvider
        width={chartWidth}
        height={chartHeight}
        margin={{ top: marginY, bottom: marginY, left: marginX, right: marginX }}
        skipAnimation
        series={[
          {
            type: "scatter",
            id: "received",
            label: "Received symbols",
            data: receivedPoints,
            markerSize: 4,
            color: t.palette[0],
          },
          {
            type: "scatter",
            id: "ideal",
            label: "Ideal points",
            data: idealPoints,
            markerSize: 11,
            color: IDEAL_COLOR,
          },
        ]}
        xAxis={[
          {
            id: "i",
            scaleType: "linear",
            min: -extent,
            max: extent,
            label: I,
            tickNumber: TICK_COUNT,
            height: X_AXIS_HEIGHT,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 17, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "q",
            scaleType: "linear",
            min: -extent,
            max: extent,
            label: Q,
            tickNumber: TICK_COUNT,
            width: Y_AXIS_WIDTH,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 17, fill: t.ink },
          },
        ]}
      >
        <ChartsWrapper legendPosition={{ vertical: "top", horizontal: "center" }} legendDirection="horizontal">
          <ChartsLegend sx={{ fontSize: 16, color: t.ink, height: LEGEND_HEIGHT, alignItems: "center" }} />
          <ChartsSurface
            sx={{
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
              '& [data-series="received"] .MuiScatterChart-marker': { fillOpacity: RECEIVED_OPACITY },
              '& [data-series="ideal"] .MuiScatterChart-marker': { stroke: t.pageBg, strokeWidth: 2.5 },
            }}
          >
            {iBoundaries.map((v) => (
              <ChartsReferenceLine key={`i-${v}`} x={v} lineStyle={boundaryStyle} />
            ))}
            {qBoundaries.map((v) => (
              <ChartsReferenceLine key={`q-${v}`} y={v} lineStyle={boundaryStyle} />
            ))}
            <ChartsXAxis />
            <ChartsYAxis />
            <ScatterPlot />
            <EvmLabel />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
