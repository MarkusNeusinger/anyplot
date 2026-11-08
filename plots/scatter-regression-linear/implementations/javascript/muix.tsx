// anyplot.ai
// scatter-regression-linear: Scatter Plot with Linear Regression
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: pending | Created: 2026-08-05
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { LinePlot } from "@mui/x-charts/LineChart";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
// The muted anchor (confidence-band fill), theme-adaptive like the chrome
const MUTED = window.ANYPLOT_THEME === "dark" ? "#A8A79F" : "#6B6A63";

// Constants
const CONFIDENCE_LEVEL = 95; // two-sided confidence band for the mean response, percent
// Two-tailed t critical values by level (percent): [degrees of freedom, t]. The band takes the
// entry with the largest df not above the fit's own, so it is never narrower than exact; a level
// without a table fails loudly instead of mislabelling the band.
const T_CRIT = {
  95: [
    [1, 12.706], [2, 4.303], [3, 3.182], [4, 2.776], [5, 2.571], [6, 2.447], [7, 2.365], [8, 2.306],
    [9, 2.262], [10, 2.228], [12, 2.179], [15, 2.131], [20, 2.086], [25, 2.06], [30, 2.042],
    [40, 2.021], [60, 2.0], [80, 1.99], [100, 1.984], [120, 1.98], [1000, 1.962],
  ],
};
const GRID_POINTS = 60; // samples along the fitted line and its band
const X_PAD_SHARE = 0.04; // room beyond the outermost observations, as a share of the x span
const Y_PAD_SHARE = 0.08;
const POINT_OPACITY = 0.65;
const NOTE_INSET = 28; // px from the plot corner to the fit statistics

// Columns: set these to your data's column names
const AD_SPEND = "Advertising spend ($k)"; // role: x
const REVENUE = "Sales revenue ($k)"; // role: y

// Data: replace this block with your own records, one object per row
// 90 regional campaigns: advertising spend against sales revenue, linear with noise.
const data = (() => {
  let state = 42;
  const uniform = () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
  return Array.from({ length: 90 }, () => {
    const spend = 5 + uniform() * 45;
    const noise = Math.sqrt(-2 * Math.log(Math.max(uniform(), 1e-9))) * Math.cos(2 * Math.PI * uniform());
    const revenue = 22 + spend * 3.4 + noise * 24;
    return { [AD_SPEND]: Number(spend.toFixed(2)), [REVENUE]: Number(Math.max(revenue, 8).toFixed(2)) };
  });
})();

// Plot: reads only data and the constants above
const xs = data.map((d) => d[AD_SPEND]);
const ys = data.map((d) => d[REVENUE]);
const n = data.length;
const xMean = xs.reduce((a, b) => a + b, 0) / n;
const yMean = ys.reduce((a, b) => a + b, 0) / n;
const sxy = data.reduce((s, d) => s + (d[AD_SPEND] - xMean) * (d[REVENUE] - yMean), 0);
const sxx = xs.reduce((s, x) => s + (x - xMean) ** 2, 0);
const slope = sxy / sxx;
const intercept = yMean - slope * xMean;
const ssRes = data.reduce((s, d) => s + (d[REVENUE] - (intercept + slope * d[AD_SPEND])) ** 2, 0);
const ssTot = ys.reduce((s, y) => s + (y - yMean) ** 2, 0);
const rSquared = 1 - ssRes / ssTot;
const correlation = Math.sign(slope) * Math.sqrt(rSquared);
const df = n - 2;
const residualStdErr = Math.sqrt(ssRes / df);
const tCrit = T_CRIT[CONFIDENCE_LEVEL].filter(([d]) => d <= df).pop()[1];

const xMin = Math.min(...xs);
const xMax = Math.max(...xs);
const gridX = Array.from({ length: GRID_POINTS }, (_, i) => xMin + ((xMax - xMin) * i) / (GRID_POINTS - 1));
const fittedY = gridX.map((x) => intercept + slope * x);
const halfWidth = gridX.map((x) => tCrit * residualStdErr * Math.sqrt(1 / n + (x - xMean) ** 2 / sxx));
const upperY = fittedY.map((y, i) => y + halfWidth[i]);
const lowerY = fittedY.map((y, i) => y - halfWidth[i]);

const xPad = (xMax - xMin) * X_PAD_SHARE;
const yAll = [...ys, ...upperY, ...lowerY];
const yPad = (Math.max(...yAll) - Math.min(...yAll)) * Y_PAD_SHARE;

const TITLE = "scatter-regression-linear · javascript · muix · anyplot.ai";
const STATS = `Least-squares fit to n = ${n} observations   ·   r = ${correlation.toFixed(3).replace("-", "−")}`;
const BAND_NOTE = `Shaded band: ${CONFIDENCE_LEVEL}% confidence interval for the mean response`;
const R_SQUARED_NOTE = `R² = ${rSquared.toFixed(3)}`;
const EQUATION_NOTE = `y = ${slope.toFixed(2).replace("-", "−")}x ${intercept < 0 ? "−" : "+"} ${Math.abs(intercept).toFixed(1)}`;
const HEADER_HEIGHT = 104;

function ConfidenceBand() {
  const xScale = useXScale();
  const yScale = useYScale();
  const upper = gridX.map((x, i) => `${xScale(x)},${yScale(upperY[i])}`).join(" L ");
  const lower = [...gridX.keys()].reverse().map((i) => `${xScale(gridX[i])},${yScale(lowerY[i])}`).join(" L ");
  return <path d={`M ${upper} L ${lower} Z`} fill={MUTED} fillOpacity={0.24} stroke="none" />;
}

// The fit statistics go into the top corner the line leaves empty: top left for a rising fit,
// top right for a falling one
function FitNote() {
  const { left, top, width } = useDrawingArea();
  const rising = slope >= 0;
  const x = rising ? left + NOTE_INSET : left + width - NOTE_INSET;
  const anchor = rising ? "start" : "end";
  return (
    <g>
      <text x={x} y={top + NOTE_INSET + 18} textAnchor={anchor} fontSize={22} fontWeight={600} fill={t.ink}>
        {R_SQUARED_NOTE}
      </text>
      <text x={x} y={top + NOTE_INSET + 44} textAnchor={anchor} fontSize={16} fill={t.inkSoft}>
        {EQUATION_NOTE}
      </text>
    </g>
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
        <div style={{ fontSize: 16, color: t.ink }}>{STATS}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{BAND_NOTE}</div>
      </div>
      <ChartsDataProvider
        width={width}
        height={height - HEADER_HEIGHT}
        margin={{ top: 8, right: 48, bottom: 12, left: 32 }}
        skipAnimation
        series={[
          {
            type: "scatter",
            id: "observations",
            label: "Observations",
            data: data.map((d, i) => ({ id: `pt-${i}`, x: d[AD_SPEND], y: d[REVENUE] })),
            markerSize: 7,
            color: t.palette[0],
          },
          {
            type: "line",
            id: "fit",
            label: "Least-squares fit",
            data: fittedY,
            curve: "linear",
            color: t.ink,
            showMark: false,
            disableHighlight: true,
          },
        ]}
        xAxis={[
          {
            id: "x",
            data: gridX,
            scaleType: "linear",
            min: xMin - xPad,
            max: xMax + xPad,
            label: AD_SPEND,
            height: 64,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 17, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "y",
            scaleType: "linear",
            min: Math.min(...yAll) - yPad,
            max: Math.max(...yAll) + yPad,
            label: REVENUE,
            width: 80,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 17, fill: t.ink },
          },
        ]}
      >
        <ChartsWrapper hideLegend>
          <ChartsSurface
            sx={{
              "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
              "& .MuiScatterChart-marker": { fillOpacity: POINT_OPACITY, stroke: t.pageBg, strokeWidth: 1 },
              "& .MuiLineChart-line": { strokeWidth: 3 },
            }}
          >
            <ChartsGrid horizontal vertical />
            <ConfidenceBand />
            <ScatterPlot />
            <LinePlot skipAnimation />
            <FitNote />
            <ChartsXAxis />
            <ChartsYAxis />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
