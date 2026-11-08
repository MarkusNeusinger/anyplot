// anyplot.ai
// sn-curve-basic: S-N Curve (Wöhler Curve)
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-02

import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { useDrawingArea, useXScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const LCF_HCF_BOUNDARY = 1e4; // cycles: the conventional divide between low-cycle and high-cycle fatigue
const LIMIT_LINES = [
  { key: "ultimateStrength", name: "Ultimate strength", dash: "12 6" },
  { key: "yieldStrength", name: "Yield strength", dash: "6 5" },
  { key: "enduranceLimit", name: "Endurance limit", dash: "2 5" },
];
const REGION_NAMES = ["Low-cycle fatigue", "High-cycle fatigue", "Infinite life"];
const SPECIMEN_LABEL = "Test specimens";
const FIT_LABEL = "Basquin fit";
const X_PAD_SHARE = 0.06; // share of the log cycle span added left of the data
const PLATEAU_SHARE = 0.25; // share of the log cycle span shown past the knee, so the endurance plateau reads
const Y_PAD_SHARE = 0.08; // share of the log stress span added above and below
const Y_TICK_TARGET = 5;
const FIT_POINTS = 80;
const SUPERSCRIPT = ["⁰", "¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸", "⁹"];

// Columns: set these to your data's column names
const CYCLES = "Cycles to failure, N"; // role: cycles
const STRESS = "Stress amplitude (MPa)"; // role: stress

// Data: replace this block with your own records, one object per row
// Material properties of the tested steel, in the stress unit of the records
const material = { ultimateStrength: 760, yieldStrength: 620, enduranceLimit: 380 };
// Constant-amplitude coupon tests: three specimens per stress level, their lives
// scattered around a Basquin curve that reaches the endurance limit at 10⁶ cycles
const data = (() => {
  let seed = 42;
  const rand = () => {
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  const exponent = Math.log(material.enduranceLimit / 700) / Math.log(1e6 / 1e3);
  const coefficient = 700 * Math.pow(1e3, -exponent);
  return [700, 650, 600, 550, 500, 450, 420, 400].flatMap((stress) =>
    Array.from({ length: 3 }, () => ({
      [CYCLES]: Math.round(Math.pow(stress / coefficient, 1 / exponent) * Math.pow(10, (rand() - 0.5) * 0.3)),
      [STRESS]: stress,
    })),
  );
})();

// Plot: reads only data and the constants above
const stressUnit = /\(([^)]+)\)/.exec(STRESS)?.[1] ?? "";
const enduranceLimit = material.enduranceLimit;

// Basquin fit S = A · N^b, least squares in log-log space over the finite-life specimens
const finite = data.filter((d) => d[STRESS] > enduranceLimit);
const logN = finite.map((d) => Math.log10(d[CYCLES]));
const logS = finite.map((d) => Math.log10(d[STRESS]));
const meanLogN = logN.reduce((a, b) => a + b, 0) / logN.length;
const meanLogS = logS.reduce((a, b) => a + b, 0) / logS.length;
const sxx = logN.reduce((acc, x) => acc + (x - meanLogN) ** 2, 0);
const sxy = logN.reduce((acc, x, i) => acc + (x - meanLogN) * (logS[i] - meanLogS), 0);
const basquinExponent = sxy / sxx;
const basquinLogA = meanLogS - basquinExponent * meanLogN;
const ssRes = logN.reduce((acc, x, i) => acc + (logS[i] - (basquinLogA + basquinExponent * x)) ** 2, 0);
const ssTot = logS.reduce((acc, y) => acc + (y - meanLogS) ** 2, 0);
const rSquared = 1 - ssRes / ssTot;
const logKnee = (Math.log10(enduranceLimit) - basquinLogA) / basquinExponent;

// Axis extents in log space: the data, the knee and every limit line inside the drawing area
const allLogN = data.map((d) => Math.log10(d[CYCLES]));
const logNLo = Math.min(...allLogN);
const logNHi = Math.max(...allLogN, logKnee);
const logNSpan = logNHi - logNLo;
const xMin = 10 ** (logNLo - logNSpan * X_PAD_SHARE);
const xMax = 10 ** (logNHi + logNSpan * PLATEAU_SHARE);
const stressValues = [...data.map((d) => d[STRESS]), ...LIMIT_LINES.map((l) => material[l.key])];
const logSLo = Math.log10(Math.min(...stressValues));
const logSHi = Math.log10(Math.max(...stressValues));
const logSPad = (logSHi - logSLo) * Y_PAD_SHARE;
const yMin = 10 ** (logSLo - logSPad);
const yMax = 10 ** (logSHi + logSPad);

const cycleTicks = Array.from(
  { length: Math.floor(Math.log10(xMax)) - Math.ceil(Math.log10(xMin)) + 1 },
  (_, i) => 10 ** (Math.ceil(Math.log10(xMin)) + i),
);
const rawStep = (yMax - yMin) / Y_TICK_TARGET;
const stepMagnitude = 10 ** Math.floor(Math.log10(rawStep));
const stressStep = [1, 2, 5, 10].map((m) => m * stepMagnitude).find((s) => s >= rawStep);
const stressTicks = Array.from(
  { length: Math.floor(yMax / stressStep) - Math.ceil(yMin / stressStep) + 1 },
  (_, i) => (Math.ceil(yMin / stressStep) + i) * stressStep,
);

// Fit curve on a log-spaced grid: the Basquin line from the left edge down to the knee, where it
// meets the endurance limit; the limit's reference line carries the plateau beyond
const fitCycles = [
  ...Array.from({ length: FIT_POINTS }, (_, i) =>
    10 ** (Math.log10(xMin) + (i / (FIT_POINTS - 1)) * (Math.log10(xMax) - Math.log10(xMin))),
  ).filter((n) => Math.log10(n) < logKnee),
  10 ** logKnee,
];
const fitStress = fitCycles.map((n) => 10 ** (basquinLogA + basquinExponent * Math.log10(n)));

// Fatigue regions along the cycle axis, clipped to the axis extent
const regionEdges = [xMin, Math.min(Math.max(LCF_HCF_BOUNDARY, xMin), xMax), Math.min(10 ** logKnee, xMax), xMax];
const regions = REGION_NAMES.map((name, i) => ({ name, from: regionEdges[i], to: regionEdges[i + 1] })).filter(
  (r) => r.to > r.from,
);

const specimens = data.map((d, i) => ({ id: `specimen-${i}`, x: d[CYCLES], y: d[STRESS] }));
const levelCount = new Set(data.map((d) => d[STRESS])).size;
const kneeExponent = [...String(Math.floor(logKnee))].map((digit) => SUPERSCRIPT[Number(digit)]).join("");

const TITLE = "sn-curve-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `n = ${data.length} · ${levelCount} stress levels · ${FIT_LABEL} S = ${Math.round(
  10 ** basquinLogA,
)} · N^${basquinExponent.toFixed(3).replace("-", "−")} (R² = ${rSquared.toFixed(2)}) · knee at N = ${(
  10 ** (logKnee - Math.floor(logKnee))
).toFixed(1)} × 10${kneeExponent}`;
const HEADER_H = 80;
const LEGEND_H = 40;
const X_AXIS_H = 64;
const REGION_BAND_H = 52;

function FatigueRegions() {
  const xScale = useXScale("cycles");
  const { top, height } = useDrawingArea();
  const lineY = top + height + X_AXIS_H + 14;
  return (
    <g stroke={t.inkSoft} strokeWidth={1.2}>
      {regions.map((r) => {
        const x0 = xScale(r.from) + 4;
        const x1 = xScale(r.to) - 4;
        return (
          <g key={r.name}>
            <line x1={x0} y1={lineY} x2={x1} y2={lineY} />
            <line x1={x0} y1={lineY - 5} x2={x0} y2={lineY + 5} />
            <line x1={x1} y1={lineY - 5} x2={x1} y2={lineY + 5} />
            <text
              x={(x0 + x1) / 2}
              y={lineY + 24}
              textAnchor="middle"
              fontSize={14}
              stroke="none"
              fill={t.inkSoft}
            >
              {r.name}
            </text>
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 8,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>
      <ChartsDataProvider
        width={width}
        height={height - HEADER_H - LEGEND_H}
        margin={{ top: 12, right: 48, bottom: REGION_BAND_H, left: 24 }}
        skipAnimation
        series={[
          {
            type: "scatter",
            id: "specimens",
            xAxisId: "cycles",
            yAxisId: "stress",
            data: specimens,
            color: t.palette[0],
            markerSize: 9,
            label: SPECIMEN_LABEL,
          },
          {
            type: "line",
            id: "fit",
            xAxisId: "cycles",
            yAxisId: "stress",
            data: fitStress,
            color: t.palette[1],
            showMark: false,
            curve: "linear",
            label: FIT_LABEL,
          },
        ]}
        xAxis={[
          {
            id: "cycles",
            scaleType: "log",
            data: fitCycles,
            min: xMin,
            max: xMax,
            tickInterval: cycleTicks,
            valueFormatter: (n) =>
              `10${[...String(Math.round(Math.log10(n)))].map((digit) => SUPERSCRIPT[Number(digit)]).join("")}`,
            label: CYCLES,
            height: X_AXIS_H,
            tickLabelStyle: { fontSize: 16, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "stress",
            scaleType: "log",
            min: yMin,
            max: yMax,
            tickInterval: stressTicks,
            label: STRESS,
            width: 84,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
      >
        <ChartsWrapper legendPosition={{ vertical: "top", horizontal: "end" }} legendDirection="horizontal">
          <ChartsLegend sx={{ fontSize: 15, color: t.ink, pr: 6 }} />
          <ChartsSurface
            sx={{
              "& .MuiLineChart-line": { strokeWidth: 3 },
              "& .MuiScatterChart-marker": { stroke: t.pageBg, strokeWidth: 1.5 },
              "& .MuiChartsGrid-line": { stroke: t.grid },
            }}
          >
            <ChartsGrid horizontal />
            <LinePlot skipAnimation />
            {LIMIT_LINES.map((l) => (
              <ChartsReferenceLine
                key={l.key}
                y={material[l.key]}
                axisId="stress"
                label={`${l.name} · ${material[l.key]} ${stressUnit}`}
                labelAlign="end"
                labelStyle={{ fill: t.inkSoft, fontSize: 14 }}
                lineStyle={{ stroke: t.inkSoft, strokeDasharray: l.dash, strokeWidth: 1.5 }}
              />
            ))}
            <ScatterPlot />
            <ChartsXAxis axisId="cycles" />
            <ChartsYAxis axisId="stress" />
            <FatigueRegions />
          </ChartsSurface>
          <ChartsTooltip trigger="item" />
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
