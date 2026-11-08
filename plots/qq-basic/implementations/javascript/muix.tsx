// anyplot.ai
// qq-basic: Basic Q-Q Plot
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 84/100 | Updated: 2026-11-08
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";

const t = window.ANYPLOT_TOKENS;

// Constants
// Acklam's rational approximation of the inverse standard-normal CDF (|error| < 1.15e-9)
const ACKLAM_A = [-39.69683028665376, 220.9460984245205, -275.9285104469687, 138.357751867269, -30.66479806614716, 2.506628277459239];
const ACKLAM_B = [-54.47609879822406, 161.5858368580409, -155.6989798598866, 66.80131188771972, -13.28068155288572];
const ACKLAM_C = [-0.007784894002430293, -0.3223964580411365, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783];
const ACKLAM_D = [0.007784695709041462, 0.3224671290700398, 2.445134137142996, 3.754408661907416];
const ACKLAM_LOW = 0.02425;
const PAD_SHARE = 0.06; // share of the quantile range kept free around the points
const TITLE_H = 48;
const SUBTITLE_H = 28;
const LEGEND_H = 40;

// Columns: set these to your data's column names
const FULFILLMENT = "Order fulfillment time (hours)"; // role: sample

// Data: replace this block with your own records, one object per row
// 60 warehouse orders, right-skewed (log-normal) times from a fixed-seed LCG and Box-Muller
let lcgState = 42;
const data = Array.from({ length: 60 }, () => {
  lcgState = (Math.imul(lcgState, 1664525) + 1013904223) >>> 0;
  const u = lcgState / 4294967296;
  lcgState = (Math.imul(lcgState, 1664525) + 1013904223) >>> 0;
  const v = lcgState / 4294967296;
  const z = Math.sqrt(-2 * Math.log(u + 1e-15)) * Math.cos(2 * Math.PI * v);
  return { [FULFILLMENT]: Math.round(Math.exp(3.4 + 0.35 * z) * 10) / 10 };
});

// Plot: reads only data and the constants above
const values = data.map((d) => d[FULFILLMENT]).filter((v) => Number.isFinite(v)).sort((a, b) => a - b);
const n = values.length;
const mean = values.reduce((a, b) => a + b, 0) / n;
const sd = Math.sqrt(values.reduce((a, b) => a + (b - mean) ** 2, 0) / (n - 1));

// Blom positions (i - 3/8) / (n + 1/4) mapped to normal quantiles with the sample's mean and sd,
// so a normal sample falls on y = x
const points = values.map((v, i) => {
  const p = (i + 1 - 0.375) / (n + 0.25);
  const tail = p < ACKLAM_LOW ? p : p > 1 - ACKLAM_LOW ? 1 - p : null;
  let z;
  if (tail === null) {
    const q = p - 0.5;
    const r = q * q;
    z =
      ((((((ACKLAM_A[0] * r + ACKLAM_A[1]) * r + ACKLAM_A[2]) * r + ACKLAM_A[3]) * r + ACKLAM_A[4]) * r + ACKLAM_A[5]) * q) /
      (((((ACKLAM_B[0] * r + ACKLAM_B[1]) * r + ACKLAM_B[2]) * r + ACKLAM_B[3]) * r + ACKLAM_B[4]) * r + 1);
  } else {
    const q = Math.sqrt(-2 * Math.log(tail));
    const magnitude =
      (((((ACKLAM_C[0] * q + ACKLAM_C[1]) * q + ACKLAM_C[2]) * q + ACKLAM_C[3]) * q + ACKLAM_C[4]) * q + ACKLAM_C[5]) /
      ((((ACKLAM_D[0] * q + ACKLAM_D[1]) * q + ACKLAM_D[2]) * q + ACKLAM_D[3]) * q + 1);
    z = p < 0.5 ? magnitude : -magnitude;
  }
  return { x: mean + sd * z, y: v, id: i };
});

const allQuantiles = points.flatMap((pt) => [pt.x, pt.y]);
const lo = Math.min(...allQuantiles);
const hi = Math.max(...allQuantiles);
const axisMin = lo - (hi - lo) * PAD_SHARE;
const axisMax = hi + (hi - lo) * PAD_SHARE;

const unitMatch = FULFILLMENT.match(/^(.*?)\s*\(([^)]+)\)$/);
const unit = unitMatch ? unitMatch[2] : "";
const unitSuffix = unit ? ` (${unit})` : "";

const TITLE = "qq-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${FULFILLMENT}: n = ${n} against a normal distribution with the sample's mean ${mean.toFixed(1)} and sd ${sd.toFixed(1)}`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, display: "flex", alignItems: "flex-end", justifyContent: "center", fontSize: 22, fontWeight: 600, color: t.ink }}>
        {TITLE}
      </div>
      <div style={{ height: SUBTITLE_H, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15, color: t.inkSoft }}>
        {SUBTITLE}
      </div>
      <ChartsDataProvider
        width={width}
        height={height - TITLE_H - SUBTITLE_H - LEGEND_H}
        margin={{ top: 16, right: 56, bottom: 8, left: 24 }}
        skipAnimation
        series={[
          {
            type: "line",
            id: "reference",
            label: "Reference line y = x",
            data: [axisMin, axisMax],
            color: t.inkSoft,
            curve: "linear",
            showMark: false,
            disableHighlight: true,
          },
          {
            type: "scatter",
            id: "sample",
            label: `Observations (n = ${n})`,
            data: points,
            color: t.palette[0],
            markerSize: 7,
          },
        ]}
        xAxis={[
          {
            id: "theoretical",
            data: [axisMin, axisMax],
            scaleType: "linear",
            min: axisMin,
            max: axisMax,
            label: `Theoretical quantiles, fitted normal${unitSuffix}`,
            height: 64,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "sample",
            scaleType: "linear",
            min: axisMin,
            max: axisMax,
            label: `Sample quantiles${unitSuffix}`,
            width: 72,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
      >
        <ChartsWrapper legendPosition={{ vertical: "top", horizontal: "center" }} legendDirection="horizontal">
          <ChartsLegend sx={{ fontSize: 15, color: t.inkSoft, height: LEGEND_H, alignItems: "center" }} />
          <ChartsSurface
            sx={{
              "& .MuiLineChart-line[data-series='reference']": { strokeWidth: 2.5, strokeDasharray: "10 7" },
              "& .MuiScatterChart-marker": { stroke: t.pageBg, strokeWidth: 1 },
              "& .MuiChartsGrid-line": { stroke: t.grid },
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
            }}
          >
            <ChartsGrid vertical horizontal />
            <LinePlot skipAnimation />
            <ScatterPlot />
            <ChartsXAxis axisId="theoretical" />
            <ChartsYAxis axisId="sample" />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
