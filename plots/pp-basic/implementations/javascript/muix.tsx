// anyplot.ai
// pp-basic: Probability-Probability (P-P) Plot
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 85/100 | Updated: 2026-11-08
//# anyplot-orientation: square
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
const REFERENCE = "normal"; // role: theoretical_distribution; its CDF is evaluated with the sample's mean and sd
const AS_P = 0.2316419; // Abramowitz & Stegun 26.2.17 approximation of the normal CDF
const AS_B = [0.31938153, -0.356563782, 1.781477937, -1.821255978, 1.330274429];
const PROBABILITY_TICKS = Array.from({ length: 11 }, (_, i) => i / 10); // the fixed 0–1 domain in steps of 0.1
const TITLE_H = 48;
const SUBTITLE_H = 28;
const LEGEND_H = 40;
const AXIS_BAND = 72; // y-axis width and x-axis height, px
const MARGIN = { top: 16, right: 40, bottom: 24, left: 16 }; // left + band + right = top + band + bottom keeps the plot area square

// Columns: set these to your data's column names
const LEAD_TIME = "Delivery lead time (days)"; // role: observed

// Data: replace this block with your own records, one object per row
// 200 supplier lead times, mildly right-skewed (log-normal), from fixed-seed mulberry32 uniforms and Box-Muller
let rngState = 42;
const uniforms = Array.from({ length: 200 }, () => {
  rngState = (rngState + 0x6d2b79f5) | 0;
  let z = Math.imul(rngState ^ (rngState >>> 15), 1 | rngState);
  z = (z + Math.imul(z ^ (z >>> 7), 61 | z)) ^ z;
  return ((z ^ (z >>> 14)) >>> 0) / 4294967296;
});
const data = Array.from({ length: 200 }, (_, i) => {
  const pair = i - (i % 2);
  const radius = Math.sqrt(-2 * Math.log(Math.max(uniforms[pair], 1e-10)));
  const angle = 2 * Math.PI * uniforms[pair + 1];
  const z = i % 2 === 0 ? radius * Math.cos(angle) : radius * Math.sin(angle);
  return { [LEAD_TIME]: 4 * Math.exp(0.35 * z) };
});

// Plot: reads only data and the constants above
const values = data.map((d) => d[LEAD_TIME]).filter((v) => Number.isFinite(v)).sort((a, b) => a - b);
const n = values.length;
const mean = values.reduce((a, b) => a + b, 0) / n;
const sd = Math.sqrt(values.reduce((a, b) => a + (b - mean) ** 2, 0) / (n - 1));

// Empirical plotting positions i / (n + 1) against the fitted normal CDF at the same value
const points = values.map((v, i) => {
  const z = (v - mean) / sd;
  const k = 1 / (1 + AS_P * Math.abs(z));
  const tail = (Math.exp(-0.5 * z * z) / Math.sqrt(2 * Math.PI)) * k * (AS_B[0] + k * (AS_B[1] + k * (AS_B[2] + k * (AS_B[3] + k * AS_B[4]))));
  return { x: z >= 0 ? 1 - tail : tail, y: (i + 1) / (n + 1), id: i };
});

const unitMatch = LEAD_TIME.match(/\(([^)]+)\)/);
const unit = unitMatch ? ` ${unitMatch[1]}` : "";

const TITLE = "pp-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${LEAD_TIME}: n = ${n} against a ${REFERENCE} distribution with the sample's mean ${mean.toFixed(2)}${unit} and sd ${sd.toFixed(2)}${unit}`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const side = Math.min(width, height - TITLE_H - SUBTITLE_H - LEGEND_H);

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <div style={{ height: TITLE_H, display: "flex", alignItems: "flex-end", fontSize: 22, fontWeight: 600, color: t.ink }}>
        {TITLE}
      </div>
      <div style={{ height: SUBTITLE_H, display: "flex", alignItems: "center", fontSize: 15, color: t.inkSoft }}>
        {SUBTITLE}
      </div>
      <ChartsDataProvider
        width={side}
        height={side}
        margin={MARGIN}
        skipAnimation
        series={[
          {
            type: "line",
            id: "diagonal",
            label: "Perfect fit (y = x)",
            data: [0, 1],
            color: t.inkSoft,
            curve: "linear",
            showMark: false,
            disableHighlight: true,
          },
          {
            type: "scatter",
            id: "observations",
            label: `Observations (n = ${n})`,
            data: points,
            color: t.palette[0],
            markerSize: 5,
          },
        ]}
        xAxis={[
          {
            id: "theoretical",
            data: [0, 1],
            scaleType: "linear",
            min: 0,
            max: 1,
            tickInterval: PROBABILITY_TICKS,
            label: `Theoretical cumulative probability (fitted ${REFERENCE})`,
            height: AXIS_BAND,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "empirical",
            scaleType: "linear",
            min: 0,
            max: 1,
            tickInterval: PROBABILITY_TICKS,
            label: "Empirical cumulative probability",
            width: AXIS_BAND,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
      >
        <ChartsWrapper legendPosition={{ vertical: "top", horizontal: "center" }} legendDirection="horizontal">
          <ChartsLegend
            sx={{
              fontSize: 15,
              color: t.inkSoft,
              height: LEGEND_H,
              alignItems: "center",
              // the legend sample repeats the diagonal's dash so the key reads as the line it explains
              "& [data-series='diagonal'] .MuiChartsLegend-mark": { width: 40 },
              "& [data-series='diagonal'] .MuiChartsLegend-mark path": { strokeWidth: 2, strokeDasharray: "9 6", strokeLinecap: "butt" },
            }}
          />
          <ChartsSurface
            sx={{
              "& .MuiLineChart-line[data-series='diagonal']": { strokeWidth: 2, strokeDasharray: "9 6" },
              "& .MuiScatterChart-marker": { stroke: t.pageBg, strokeWidth: 0.75 },
              "& .MuiChartsGrid-line": { stroke: t.grid },
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
            }}
          >
            <ChartsGrid vertical horizontal />
            <LinePlot skipAnimation />
            <ScatterPlot />
            <ChartsXAxis axisId="theoretical" />
            <ChartsYAxis axisId="empirical" />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
