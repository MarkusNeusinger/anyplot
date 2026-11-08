// anyplot.ai
// line-arrhenius: Arrhenius Plot for Reaction Kinetics
// Library: muix 9.17.0 | JavaScript 22.22.3
// Quality: 88/100 | Created: 2026-06-24
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const R_GAS = 8.314; // gas constant, J/(mol·K)
const INV_T_SCALE = 1000; // the x axis shows 1000 / T, so the slope reads in kK
const X_PAD_SHARE = 0.05; // share of the 1000/T range added beside the outermost points
const Y_PAD_SHARE = 0.08; // share of the ln k range added above and below
const NOTE_AT_SHARE = 0.5; // the slope note sits at this share of the fitted x range

// Columns: set these to your data's column names
const TEMPERATURE = "Temperature (K)"; // role: temperature_K
const RATE = "Rate constant k (s⁻¹)"; // role: rate_constant_k

// Data: replace this block with your own records, one object per measurement
// First-order thermal decomposition of N₂O₅ (2 N₂O₅ → 4 NO₂ + O₂) measured at 11
// temperatures from 278 K to 338 K: Ea = 103 kJ/mol, A = 4.94 × 10¹³ s⁻¹ (ln A = 31.53),
// with a little scatter on each ln k.
const data = (() => {
  let seed = 42;
  const rand = () => {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  return [278, 284, 290, 296, 302, 308, 314, 320, 326, 332, 338].map((kelvin) => {
    const lnK = 31.53 - 103000 / (8.314 * kelvin) + (rand() - 0.5) * 0.3;
    return { [TEMPERATURE]: kelvin, [RATE]: Number(Math.exp(lnK).toPrecision(4)) };
  });
})();

// Plot: reads only data and the constants above
const rows = data
  .filter((d) => d[TEMPERATURE] > 0 && d[RATE] > 0)
  .sort((a, b) => a[TEMPERATURE] - b[TEMPERATURE]);
const invT = rows.map((d) => INV_T_SCALE / d[TEMPERATURE]);
const lnK = rows.map((d) => Math.log(d[RATE]));
const n = rows.length;

// Least-squares fit ln k = intercept + slope · (1000 / T)
const xMean = invT.reduce((a, b) => a + b, 0) / n;
const yMean = lnK.reduce((a, b) => a + b, 0) / n;
let sxy = 0;
let sxx = 0;
let syy = 0;
for (let i = 0; i < n; i += 1) {
  sxy += (invT[i] - xMean) * (lnK[i] - yMean);
  sxx += (invT[i] - xMean) ** 2;
  syy += (lnK[i] - yMean) ** 2;
}
const slope = sxy / sxx;
const intercept = yMean - slope * xMean;
const r2 = (sxy * sxy) / (sxx * syy);
// slope = −Ea / (R · 1000), so the slope per kelvin is −Ea/R and Ea in kJ/mol follows from it
const slopeKelvin = slope * INV_T_SCALE;
const eaKj = (-slopeKelvin * R_GAS) / 1000;

const xLow = Math.min(...invT);
const xHigh = Math.max(...invT);
const xPad = (xHigh - xLow) * X_PAD_SHARE;
const fitX = [xLow, xHigh];
const fitY = fitX.map((x) => intercept + slope * x);
const yLow = Math.min(...lnK, ...fitY);
const yHigh = Math.max(...lnK, ...fitY);
const yPad = (yHigh - yLow) * Y_PAD_SHARE;
const noteX = xLow + (xHigh - xLow) * NOTE_AT_SHARE;

const rateUnit = RATE.match(/\(([^)]+)\)/)?.[1];
const Y_LABEL = rateUnit ? `ln(k / ${rateUnit})` : "ln k";
const SLOPE_NOTE = `slope = −Ea/R = ${slopeKelvin < 0 ? "−" : ""}${Math.abs(slopeKelvin).toLocaleString("en-US", { maximumFractionDigits: 0 })} K`;
const EA_NOTE = `Ea = ${eaKj.toFixed(1)} kJ/mol · R² = ${r2.toFixed(4)}`;

const TITLE = "line-arrhenius · javascript · muix · anyplot.ai";
const SUBTITLE = `${n} measurements, ${rows[0][TEMPERATURE]}–${rows[n - 1][TEMPERATURE]} K · least-squares fit of ln k against 1/T`;
const HEADER_H = 84;
const LEGEND_H = 44;

function SlopeNote() {
  const xScale = useXScale("invT");
  const yScale = useYScale();
  const x = xScale(noteX) + 24;
  const y = yScale(intercept + slope * noteX) - 52;
  return (
    <text x={x} y={y} fontSize={16} fill={t.ink}>
      <tspan x={x} fontWeight={600}>
        {SLOPE_NOTE}
      </tspan>
      <tspan x={x} dy={22}>
        {EA_NOTE}
      </tspan>
    </text>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const axisStyle = {
    tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
    labelStyle: { fontSize: 16, fill: t.ink },
  };

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <Box sx={{ height: HEADER_H, pt: "14px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.3 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.6 }}>{SUBTITLE}</Typography>
      </Box>
      <ChartsDataProvider
        width={width}
        height={height - HEADER_H - LEGEND_H}
        margin={{ top: 8, right: 48, bottom: 8, left: 20 }}
        skipAnimation
        series={[
          {
            type: "line",
            id: "fit",
            data: fitY,
            xAxisId: "invT",
            label: "Linear fit",
            color: t.palette[1],
            curve: "linear",
            showMark: false,
            labelMarkType: "line",
          },
          {
            type: "scatter",
            id: "measured",
            data: rows.map((_, i) => ({ id: i, x: invT[i], y: lnK[i] })),
            xAxisId: "invT",
            label: "Measured rate constants",
            color: t.palette[0],
            markerSize: 9,
            valueFormatter: (v) => (v ? `T = ${rows[v.id][TEMPERATURE]} K, ln k = ${v.y.toFixed(2)}` : ""),
          },
        ]}
        xAxis={[
          {
            id: "invT",
            data: fitX,
            scaleType: "linear",
            position: "bottom",
            min: xLow - xPad,
            max: xHigh + xPad,
            label: `${INV_T_SCALE} / T (K⁻¹)`,
            height: 64,
            tickNumber: 8,
            valueFormatter: (v: number) => v.toFixed(2),
            ...axisStyle,
          },
          {
            // The same scale as the bottom axis, ticked at every measured temperature
            id: "kelvin",
            scaleType: "linear",
            position: "top",
            min: xLow - xPad,
            max: xHigh + xPad,
            tickInterval: invT,
            tickLabelInterval: () => true,
            label: TEMPERATURE,
            height: 64,
            valueFormatter: (v: number) => String(Math.round(INV_T_SCALE / v)),
            ...axisStyle,
          },
        ]}
        yAxis={[
          {
            min: yLow - yPad,
            max: yHigh + yPad,
            width: 72,
            label: Y_LABEL,
            ...axisStyle,
          },
        ]}
      >
        <ChartsWrapper legendPosition={{ vertical: "bottom", horizontal: "center" }} legendDirection="horizontal">
          <ChartsLegend sx={{ fontSize: 15, color: t.ink, gap: "36px", pt: "8px" }} />
          <ChartsSurface
            sx={{
              "& .MuiLineChart-line": { strokeWidth: 3 },
              "& .MuiChartsGrid-line": { stroke: t.grid },
            }}
          >
            <ChartsGrid horizontal />
            <LinePlot skipAnimation />
            <ScatterPlot />
            <SlopeNote />
            <ChartsXAxis axisId="invT" />
            <ChartsXAxis axisId="kelvin" />
            <ChartsYAxis />
          </ChartsSurface>
          <ChartsTooltip trigger="item" />
        </ChartsWrapper>
      </ChartsDataProvider>
    </Box>
  );
}
