// anyplot.ai
// sn-curve-basic: S-N Curve (Wöhler Curve)
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-02

import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const ULTIMATE_STRENGTH = 760;
const YIELD_STRENGTH = 620;
const ENDURANCE_LIMIT = 380;
const N_KNEE = 1e6;
const LOW_HIGH_BOUNDARY = 1e4;
const X_MIN = 500;
const X_MAX = 1e7;
const GRID_N = 60;
const CYCLE_TICKS = [1e3, 1e4, 1e5, 1e6, 1e7];
const STRESS_TICKS = [400, 500, 600, 700, 800];
const SUPERSCRIPT: Record<string, string> = {
  "0": "⁰",
  "1": "¹",
  "2": "²",
  "3": "³",
  "4": "⁴",
  "5": "⁵",
  "6": "⁶",
  "7": "⁷",
  "8": "⁸",
  "9": "⁹",
};
const REGIONS = [
  { label: "LOW-CYCLE FATIGUE", xMin: X_MIN, xMax: LOW_HIGH_BOUNDARY },
  { label: "HIGH-CYCLE FATIGUE", xMin: LOW_HIGH_BOUNDARY, xMax: N_KNEE },
  { label: "INFINITE LIFE", xMin: N_KNEE, xMax: X_MAX },
];

// Columns: set these to your data's column names
const CYCLES = "Cycles to Failure, N"; // role: cycles
const STRESS = "Stress Amplitude (MPa)"; // role: stress

// Data: replace this block with your own records
const n1Anchor = 1e3;
const s1Anchor = 700;
const bAnchor = Math.log(ENDURANCE_LIMIT / s1Anchor) / Math.log(N_KNEE / n1Anchor);
const cAnchor = s1Anchor * Math.pow(n1Anchor, -bAnchor);
const stressLevels = [700, 650, 600, 550, 500, 450, 420, 400];
const specimensPerLevel = 3;

let seed = 42;
const data: Array<Record<string, number>> = [];
for (let levelIdx = 0; levelIdx < stressLevels.length; levelIdx++) {
  const stress = stressLevels[levelIdx];
  const baseCycles = Math.pow(stress / cAnchor, 1 / bAnchor);
  for (let k = 0; k < specimensPerLevel; k++) {
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    const u = seed / 4294967296;
    const jitter = Math.pow(10, (u - 0.5) * 0.3);
    data.push({
      [CYCLES]: Math.round(baseCycles * jitter),
      [STRESS]: stress,
    });
  }
}

// Plot: reads only data and the constants above
const specimens = data.map((row, idx) => ({
  id: `S-${idx}`,
  x: Number(row[CYCLES]),
  y: Number(row[STRESS]),
}));

// Fit Basquin power-law S = C * N^b on log-transformed finite-life specimens
const finiteSpecimens = specimens.filter((pt) => pt.x <= N_KNEE);
const nFit = finiteSpecimens.length;
let sumLogN = 0;
let sumLogS = 0;
let sumLogNN = 0;
let sumLogNS = 0;
for (const pt of finiteSpecimens) {
  const ln = Math.log(pt.x);
  const ls = Math.log(pt.y);
  sumLogN += ln;
  sumLogS += ls;
  sumLogNN += ln * ln;
  sumLogNS += ln * ls;
}
const bExp =
  (nFit * sumLogNS - sumLogN * sumLogS) /
  (nFit * sumLogNN - sumLogN * sumLogN);
const cCoef = Math.exp((sumLogS - bExp * sumLogN) / nFit);

const logMin = Math.log10(X_MIN);
const logMax = Math.log10(X_MAX);
const fitCycles = Array.from({ length: GRID_N }, (_, i) =>
  Math.pow(10, logMin + (i / (GRID_N - 1)) * (logMax - logMin)),
);
const fitStress = fitCycles.map((n) =>
  n <= N_KNEE ? Math.max(ENDURANCE_LIMIT, cCoef * Math.pow(n, bExp)) : ENDURANCE_LIMIT,
);

function SafeZoneBand() {
  const { left, top, width, height } = useDrawingArea();
  const yScale = useYScale("stress") as (v: number) => number;
  const yTop = yScale(ENDURANCE_LIMIT);
  const yBottom = top + height;
  return (
    <g>
      <rect
        x={left}
        y={yTop}
        width={width}
        height={Math.max(yBottom - yTop, 1)}
        fill={t.inkSoft}
        opacity={0.07}
      />
      <text
        x={left + width - 14}
        y={yTop + (yBottom - yTop) / 2}
        textAnchor="end"
        dominantBaseline="middle"
        fontSize={14}
        fontStyle="italic"
        fill={t.inkSoft}
      >
        Safe zone — infinite life below endurance limit
      </text>
    </g>
  );
}

function FatigueRegionLabels() {
  const { top, height } = useDrawingArea();
  const xScale = useXScale("cycles") as (v: number) => number;
  const lineY = top + height + 68;
  const textY = lineY + 18;
  return (
    <g>
      {REGIONS.map((r) => {
        const x0 = xScale(Math.max(r.xMin, X_MIN));
        const x1 = xScale(Math.min(r.xMax, X_MAX));
        const xMid = (x0 + x1) / 2;
        return (
          <React.Fragment key={r.label}>
            <line
              x1={x0 + 4}
              y1={lineY}
              x2={x1 - 4}
              y2={lineY}
              stroke={t.inkSoft}
              strokeWidth={1}
              opacity={0.4}
            />
            <line
              x1={x0 + 4}
              y1={lineY - 4}
              x2={x0 + 4}
              y2={lineY + 4}
              stroke={t.inkSoft}
              strokeWidth={1}
              opacity={0.4}
            />
            <line
              x1={x1 - 4}
              y1={lineY - 4}
              x2={x1 - 4}
              y2={lineY + 4}
              stroke={t.inkSoft}
              strokeWidth={1}
              opacity={0.4}
            />
            <text
              x={xMid}
              y={textY}
              textAnchor="middle"
              fontSize={14}
              letterSpacing={0.6}
              fill={t.inkSoft}
            >
              {r.label}
            </text>
          </React.Fragment>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const headerH = 82;
  const chartH = height - headerH;

  return (
    <Box
      sx={{
        width,
        height,
        background: t.pageBg,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box
        sx={{
          height: headerH,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "6px",
          pt: "8px",
        }}
      >
        <Typography
          sx={{
            fontSize: "22px",
            fontWeight: 600,
            color: t.ink,
            textAlign: "center",
            lineHeight: 1.2,
          }}
        >
          AISI 4340 Steel S-N Curve · sn-curve-basic · javascript · muix · anyplot.ai
        </Typography>
        <Box sx={{ display: "flex", alignItems: "center", gap: "28px" }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Box
              sx={{
                width: 12,
                height: 12,
                borderRadius: "50%",
                bgcolor: t.palette[0],
              }}
            />
            <Typography sx={{ fontSize: "14px", color: t.inkSoft }}>
              Test Specimens (n = {specimens.length})
            </Typography>
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Box
              sx={{
                width: 22,
                height: 3.5,
                borderRadius: "2px",
                bgcolor: t.palette[1],
              }}
            />
            <Typography sx={{ fontSize: "14px", color: t.inkSoft }}>
              Basquin Power-Law Fit (b = {bExp.toFixed(3)})
            </Typography>
          </Box>
        </Box>
      </Box>
      <ChartsContainer
        width={width}
        height={chartH}
        margin={{ top: 20, right: 48, bottom: 112, left: 108 }}
        sx={{
          '[data-series="fit"] .MuiLineChart-line': { strokeWidth: 3.5 },
          "& circle": { stroke: t.pageBg, strokeWidth: 2 },
        }}
        series={[
          {
            type: "scatter",
            id: "specimens",
            xAxisId: "cycles",
            yAxisId: "stress",
            data: specimens,
            color: t.palette[0],
            markerSize: 9,
            label: "Test Specimens",
          },
          {
            type: "line",
            id: "fit",
            xAxisId: "cycles",
            yAxisId: "stress",
            data: fitStress,
            color: t.palette[1],
            showMark: false,
            curve: "monotoneX",
            label: "Basquin Fit (Power-Law)",
          },
        ]}
        xAxis={[
          {
            id: "cycles",
            scaleType: "log",
            data: fitCycles,
            min: X_MIN,
            max: X_MAX,
            height: 64,
            label: CYCLES,
            valueFormatter: (n: number) => {
              const exp = Math.round(Math.log10(n));
              return `10${String(exp)
                .split("")
                .map((d) => SUPERSCRIPT[d] || d)
                .join("")}`;
            },
            tickInterval: CYCLE_TICKS,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "stress",
            scaleType: "log",
            min: 340,
            max: 820,
            width: 96,
            label: STRESS,
            tickInterval: STRESS_TICKS,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
      >
        <ChartsGrid horizontal />
        <SafeZoneBand />
        <LinePlot skipAnimation />
        <ScatterPlot skipAnimation />
        <ChartsReferenceLine
          y={ULTIMATE_STRENGTH}
          axisId="stress"
          label={`Ultimate Strength = ${ULTIMATE_STRENGTH} MPa`}
          labelAlign="start"
          labelStyle={{ fill: t.inkSoft, fontSize: 14 }}
          lineStyle={{
            stroke: t.amber,
            strokeDasharray: "2 4",
            strokeWidth: 1.5,
            opacity: 0.85,
          }}
        />
        <ChartsReferenceLine
          y={YIELD_STRENGTH}
          axisId="stress"
          label={`Yield Strength = ${YIELD_STRENGTH} MPa`}
          labelAlign="start"
          labelStyle={{ fill: t.inkSoft, fontSize: 14 }}
          lineStyle={{
            stroke: t.amber,
            strokeDasharray: "6 4",
            strokeWidth: 1.5,
            opacity: 0.85,
          }}
        />
        <ChartsReferenceLine
          y={ENDURANCE_LIMIT}
          axisId="stress"
          label={`Endurance Limit = ${ENDURANCE_LIMIT} MPa`}
          labelAlign="start"
          labelStyle={{ fill: t.inkSoft, fontSize: 14 }}
          lineStyle={{
            stroke: t.amber,
            strokeDasharray: "3 5",
            strokeWidth: 4,
            opacity: 0.85,
          }}
        />
        <ChartsXAxis axisId="cycles" />
        <ChartsYAxis axisId="stress" />
        <ChartsTooltip trigger="item" />
        <FatigueRegionLabels />
      </ChartsContainer>
    </Box>
  );
}
