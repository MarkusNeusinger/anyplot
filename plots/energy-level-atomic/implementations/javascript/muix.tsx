// anyplot.ai
// energy-level-atomic: Atomic Energy Level Diagram
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-25

import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";
import { Box, Typography } from "@mui/material";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "energy-level-atomic · javascript · muix · anyplot.ai";
const FONT = "'Roboto', 'Helvetica Neue', Arial, sans-serif";
const ENERGY_UNIT = "eV";
const ENERGY_AXIS_TITLE = `Energy (${ENERGY_UNIT})`;
const WAVELENGTH_UNIT = "nm";
const IONIZATION_EV = 0;
const IONIZATION_LABEL = `Ionization limit (E = ${IONIZATION_EV} ${ENERGY_UNIT})`;
const COMPRESS_POWER = 0.35;
const LEVEL_X_START_SHARE = 0.27;
const LEVEL_X_END_SHARE = 0.85;
const ARROW_INNER_PAD_SHARE = 0.08;
const Y_TOP_PAD_SHARE = 0.12;
const UV_MAX_NM = 400;
const VISIBLE_MAX_NM = 700;
const SPECTRAL_BANDS = [
  { maxNm: UV_MAX_NM, label: `Ultraviolet (< ${UV_MAX_NM} ${WAVELENGTH_UNIT})` },
  { maxNm: VISIBLE_MAX_NM, label: `Visible (${UV_MAX_NM}–${VISIBLE_MAX_NM} ${WAVELENGTH_UNIT})` },
  { maxNm: Infinity, label: `Infrared (> ${VISIBLE_MAX_NM} ${WAVELENGTH_UNIT})` },
];

// Data: named parameters for Hydrogen atom bound states and transitions
const SYSTEM = "Hydrogen atom (Z = 1)";
const RYDBERG_EV = 13.6; // role: energy
const LEVELS_SPEC = [
  { n: 1, orbital: "n = 1 (1s) — ground state" }, // role: level
  { n: 2, orbital: "n = 2 (2s, 2p)" },
  { n: 3, orbital: "n = 3 (3s, 3p, 3d)" },
  { n: 4, orbital: "n = 4 (4s–4f)" },
  { n: 5, orbital: "n = 5 (5s–5g)" },
  { n: 6, orbital: "n = 6 (6s–6h)" },
];

const TRANSITIONS_SPEC = [
  { fromN: 2, toN: 1, wavelengthNm: 121.6 }, // role: transitions
  { fromN: 3, toN: 1, wavelengthNm: 102.6 },
  { fromN: 4, toN: 1, wavelengthNm: 97.3 },
  { fromN: 3, toN: 2, wavelengthNm: 656.3 },
  { fromN: 4, toN: 2, wavelengthNm: 486.1 },
  { fromN: 1, toN: 3, wavelengthNm: 102.6 },
  { fromN: 1, toN: 4, wavelengthNm: 97.3 },
  { fromN: 2, toN: 6, wavelengthNm: 410.2 },
];

// Plot: reads only data and the constants above
const levels = LEVELS_SPEC.map((row) => {
  const ev = -RYDBERG_EV / (row.n * row.n);
  const compressedY = ev >= 0 ? ev : -((-ev) ** COMPRESS_POWER);
  return {
    id: row.n,
    label: row.orbital,
    energy: ev,
    compressedY,
  };
});

const levelById = new Map(levels.map((l) => [l.id, l]));

const spectralGroups: string[] = [];
for (const tr of TRANSITIONS_SPEC) {
  const band = SPECTRAL_BANDS.find((b) => tr.wavelengthNm <= b.maxNm)!;
  if (!spectralGroups.includes(band.label)) {
    spectralGroups.push(band.label);
  }
}

const groupColorMap = new Map<string, string>();
spectralGroups.forEach((g, idx) => {
  groupColorMap.set(g, t.palette[idx]);
});

const legendItems = spectralGroups.map((g) => ({
  label: g,
  color: groupColorMap.get(g)!,
}));

const minEv = Math.min(...levels.map((l) => l.energy));
const maxEv = Math.max(IONIZATION_EV, ...levels.map((l) => l.energy));

// Derive ticks in eV from the level energies and ionization limit
const tickEvCandidates = [maxEv, ...levels.map((l) => Number(l.energy.toFixed(1)))].sort(
  (a, b) => b - a,
);
const yTicks: { value: number; compressedY: number }[] = [];
for (const val of tickEvCandidates) {
  const compressedY = val >= 0 ? val : -((-val) ** COMPRESS_POWER);
  if (
    yTicks.length === 0 ||
    Math.abs(compressedY - yTicks[yTicks.length - 1].compressedY) >= 0.28
  ) {
    yTicks.push({ value: val, compressedY });
  }
}

const yDomainMin = Math.min(...levels.map((l) => l.compressedY));
const yCompressedSpan = Math.abs(yDomainMin);
const yDomainMax = yCompressedSpan * Y_TOP_PAD_SHARE;

const levelSpanX = LEVEL_X_END_SHARE - LEVEL_X_START_SHARE;
const arrowStartX = LEVEL_X_START_SHARE + levelSpanX * ARROW_INNER_PAD_SHARE;
const arrowEndX = LEVEL_X_END_SHARE - levelSpanX * ARROW_INNER_PAD_SHARE;
const transitionCount = TRANSITIONS_SPEC.length;

const transitions = TRANSITIONS_SPEC.map((row, idx) => {
  const xFrac = arrowStartX + ((arrowEndX - arrowStartX) * idx) / (transitionCount - 1);
  const fromLvl = levelById.get(row.fromN)!;
  const toLvl = levelById.get(row.toN)!;
  const lowerLvl = fromLvl.energy <= toLvl.energy ? fromLvl : toLvl;
  const upperCandidates = levels
    .filter((l) => l.energy > lowerLvl.energy)
    .sort((a, b) => a.energy - b.energy);
  const nextAboveLvl = upperCandidates[0];
  const band = SPECTRAL_BANDS.find((b) => row.wavelengthNm <= b.maxNm)!;
  const color = groupColorMap.get(band.label)!;
  const isEmission = fromLvl.energy > toLvl.energy;
  return {
    x: xFrac,
    y1Compressed: fromLvl.compressedY,
    y2Compressed: toLvl.compressedY,
    labelLowCompressed: lowerLvl.compressedY,
    labelHighCompressed: nextAboveLvl.compressedY,
    color,
    isEmission,
    wavelengthText: `${row.wavelengthNm.toFixed(1)} ${WAVELENGTH_UNIT} ${isEmission ? "↓" : "↑"}`,
  };
});

function EnergyLevelCanvas() {
  const xScale = useXScale() as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const { left, top, width, height } = useDrawingArea();

  const x1 = xScale(LEVEL_X_START_SHARE);
  const x2 = xScale(LEVEL_X_END_SHARE);

  return (
    <g>
      <defs>
        {legendItems.map((item) => (
          <marker
            key={item.color}
            id={`arrowhead-${item.color.replace("#", "")}`}
            viewBox="0 0 10 10"
            refX={8}
            refY={5}
            markerWidth={7}
            markerHeight={7}
            orient="auto"
          >
            <path d="M0,0 L10,5 L0,10 z" fill={item.color} />
          </marker>
        ))}
      </defs>

      {/* Energy axis and horizontal grid lines */}
      <line x1={left} x2={left} y1={top} y2={top + height} stroke={t.inkSoft} strokeWidth={1.5} />
      {yTicks.map((tick) => {
        const y = yScale(tick.compressedY);
        return (
          <g key={tick.value}>
            <line x1={left} x2={left + width} y1={y} y2={y} stroke={t.grid} strokeWidth={1} />
            <line x1={left - 8} x2={left} y1={y} y2={y} stroke={t.inkSoft} strokeWidth={1.5} />
            <text
              x={left - 14}
              y={y}
              textAnchor="end"
              dominantBaseline="central"
              fontSize={14}
              fill={t.inkSoft}
              fontFamily={FONT}
            >
              {tick.value} {ENERGY_UNIT}
            </text>
          </g>
        );
      })}

      {/* Quantized energy level bars and labels */}
      {levels.map((level) => {
        const y = yScale(level.compressedY);
        return (
          <g key={level.id}>
            <line x1={x1} x2={x2} y1={y} y2={y} stroke={t.ink} strokeWidth={3} strokeLinecap="round" />
            <text
              x={x1 - 16}
              y={y}
              textAnchor="end"
              dominantBaseline="central"
              fontSize={15}
              fill={t.ink}
              fontFamily={FONT}
            >
              {level.label}
            </text>
            <text
              x={x2 + 16}
              y={y}
              textAnchor="start"
              dominantBaseline="central"
              fontSize={14}
              fill={t.inkSoft}
              fontFamily={FONT}
            >
              {level.energy.toFixed(2)} {ENERGY_UNIT}
            </text>
          </g>
        );
      })}

      {/* Transition arrows and wavelength labels */}
      {transitions.map((tr, index) => {
        const x = xScale(tr.x);
        const y1 = yScale(tr.y1Compressed);
        const y2 = yScale(tr.y2Compressed);
        const midY = (yScale(tr.labelLowCompressed) + yScale(tr.labelHighCompressed)) / 2;
        return (
          <g key={index}>
            <line
              x1={x}
              x2={x}
              y1={y1}
              y2={y2}
              stroke={tr.color}
              strokeWidth={2.5}
              markerEnd={`url(#arrowhead-${tr.color.replace("#", "")})`}
            />
            <text
              x={x + 16}
              y={midY}
              fontSize={14}
              fontWeight={600}
              fill={tr.color}
              stroke={t.pageBg}
              strokeWidth={3.5}
              paintOrder="stroke"
              fontFamily={FONT}
              textAnchor="middle"
              transform={`rotate(-90 ${x + 16} ${midY})`}
            >
              {tr.wavelengthText}
            </text>
          </g>
        );
      })}
    </g>
  );
}

const TITLE_H = 52;
const CONTEXT_H = 30;
const LEGEND_H = 36;
const Y_LABEL_W = 40;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartAreaHeight = height - TITLE_H - CONTEXT_H - LEGEND_H;
  const chartWidth = width - Y_LABEL_W;

  return (
    <Box
      sx={{
        width,
        height,
        bgcolor: t.pageBg,
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
        fontFamily: FONT,
      }}
    >
      <Box sx={{ height: TITLE_H, display: "flex", alignItems: "center", pl: "28px" }}>
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 600, fontFamily: FONT }}>
          {TITLE}
        </Typography>
      </Box>
      <Box sx={{ height: CONTEXT_H, display: "flex", alignItems: "center", pl: "28px" }}>
        <Typography sx={{ color: t.inkSoft, fontSize: 14, fontFamily: FONT }}>
          {`${SYSTEM} (${levels.length} bound states, ${transitions.length} transitions: ↓ emission, ↑ absorption) · compressed ${ENERGY_AXIS_TITLE.toLowerCase()} scale (${minEv.toFixed(1)} to ${maxEv} ${ENERGY_UNIT})`}
        </Typography>
      </Box>
      <Box sx={{ height: LEGEND_H, display: "flex", alignItems: "center", gap: "24px", pl: "28px" }}>
        {legendItems.map((item) => (
          <Box key={item.label} sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Box sx={{ width: 14, height: 14, bgcolor: item.color, borderRadius: "3px", flexShrink: 0 }} />
            <Typography sx={{ color: t.inkSoft, fontSize: 14, fontFamily: FONT }}>{item.label}</Typography>
          </Box>
        ))}
      </Box>

      <Box sx={{ display: "flex", flexDirection: "row", height: chartAreaHeight }}>
        <Box sx={{ width: Y_LABEL_W, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Typography
            sx={{ fontSize: 16, fontWeight: 600, color: t.ink, whiteSpace: "nowrap", transform: "rotate(-90deg)", fontFamily: FONT }}
          >
            {ENERGY_AXIS_TITLE}
          </Typography>
        </Box>
        <ChartsContainer
          width={chartWidth}
          height={chartAreaHeight}
          skipAnimation
          series={[]}
          xAxis={[{ id: "x", min: 0, max: 1, scaleType: "linear", position: "none" }]}
          yAxis={[{ id: "y", min: yDomainMin, max: yDomainMax, scaleType: "linear", position: "none" }]}
          margin={{ top: 40, right: 24, bottom: 28, left: 68 }}
        >
          <EnergyLevelCanvas />
          <ChartsReferenceLine
            y={IONIZATION_EV}
            axisId="y"
            label={IONIZATION_LABEL}
            labelAlign="end"
            lineStyle={{ stroke: t.amber, strokeWidth: 2, strokeDasharray: "6 4" }}
            labelStyle={{ fill: t.ink, fontSize: 14, fontWeight: 600, fontFamily: FONT }}
          />
        </ChartsContainer>
      </Box>
    </Box>
  );
}
