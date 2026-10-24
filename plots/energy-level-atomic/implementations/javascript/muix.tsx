// anyplot.ai
// energy-level-atomic: Atomic Energy Level Diagram
// Library: muix 9.0.0 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-25

import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";
import { Box, Typography } from "@mui/material";

const t = window.ANYPLOT_TOKENS;
const FONT = "'Roboto', 'Helvetica Neue', Arial, sans-serif";

// Constants
const LEVEL_ID = "levelId";
const LEVEL_LABEL = "levelLabel";
const ENERGY_EV = "energyEv";
const FROM_LEVEL = "fromLevel";
const TO_LEVEL = "toLevel";
const SERIES_GROUP = "seriesGroup";
const WAVELENGTH_NM = "wavelengthNm";

const ENERGY_UNIT = "eV";
const WAVELENGTH_UNIT = "nm";
const IONIZATION_EV = 0;
const IONIZATION_LABEL = "Ionization limit (E = 0 eV)";
const COMPRESS_POWER = 0.35;
const LEVEL_X_START_SHARE = 0.27;
const LEVEL_X_END_SHARE = 0.85;
const ARROW_INNER_PAD_SHARE = 0.08;
const Y_TOP_PAD_SHARE = 0.12;
const Y_TICK_SHARES = [0, 0.0735, 0.2206, 0.4412, 1];

// Data: Hydrogen atom (Z = 1) bound-state energies (E_n = -13.6 eV / n^2) and transitions
const levelData = [
  { [LEVEL_ID]: 1, [LEVEL_LABEL]: "n = 1 (1s) — ground state", [ENERGY_EV]: -13.6 },
  { [LEVEL_ID]: 2, [LEVEL_LABEL]: "n = 2 (2s, 2p)", [ENERGY_EV]: -3.4 },
  { [LEVEL_ID]: 3, [LEVEL_LABEL]: "n = 3 (3s, 3p, 3d)", [ENERGY_EV]: -1.5111 },
  { [LEVEL_ID]: 4, [LEVEL_LABEL]: "n = 4 (4s–4f)", [ENERGY_EV]: -0.85 },
  { [LEVEL_ID]: 5, [LEVEL_LABEL]: "n = 5 (5s–5g)", [ENERGY_EV]: -0.544 },
  { [LEVEL_ID]: 6, [LEVEL_LABEL]: "n = 6 (6s–6h)", [ENERGY_EV]: -0.3778 },
];

const transitionData = [
  {
    [FROM_LEVEL]: 2,
    [TO_LEVEL]: 1,
    [SERIES_GROUP]: "Lyman series · emission → n = 1 (UV) ↓",
    [WAVELENGTH_NM]: 121.6,
  },
  {
    [FROM_LEVEL]: 3,
    [TO_LEVEL]: 1,
    [SERIES_GROUP]: "Lyman series · emission → n = 1 (UV) ↓",
    [WAVELENGTH_NM]: 102.6,
  },
  {
    [FROM_LEVEL]: 4,
    [TO_LEVEL]: 1,
    [SERIES_GROUP]: "Lyman series · emission → n = 1 (UV) ↓",
    [WAVELENGTH_NM]: 97.3,
  },
  {
    [FROM_LEVEL]: 3,
    [TO_LEVEL]: 2,
    [SERIES_GROUP]: "Balmer series · emission → n = 2 (visible) ↓",
    [WAVELENGTH_NM]: 656.3,
  },
  {
    [FROM_LEVEL]: 4,
    [TO_LEVEL]: 2,
    [SERIES_GROUP]: "Balmer series · emission → n = 2 (visible) ↓",
    [WAVELENGTH_NM]: 486.1,
  },
  {
    [FROM_LEVEL]: 1,
    [TO_LEVEL]: 3,
    [SERIES_GROUP]: "Ground-state absorption ↑",
    [WAVELENGTH_NM]: 102.6,
  },
  {
    [FROM_LEVEL]: 1,
    [TO_LEVEL]: 4,
    [SERIES_GROUP]: "Ground-state absorption ↑",
    [WAVELENGTH_NM]: 97.3,
  },
  {
    [FROM_LEVEL]: 2,
    [TO_LEVEL]: 6,
    [SERIES_GROUP]: "Excited-state absorption (n = 2 → n = 6) ↑",
    [WAVELENGTH_NM]: 410.2,
  },
];

// Derived series groups in order of first appearance
const seriesGroups: string[] = [];
for (const row of transitionData) {
  const g = row[SERIES_GROUP];
  if (!seriesGroups.includes(g)) {
    seriesGroups.push(g);
  }
}

const groupColorMap = new Map<string, string>();
seriesGroups.forEach((g, idx) => {
  groupColorMap.set(g, t.palette[idx]);
});

const legendItems = seriesGroups.map((g) => ({
  label: g,
  color: groupColorMap.get(g) ?? t.inkSoft,
}));

// Compressed vertical coordinates for energy levels
const levels = levelData.map((row) => {
  const ev = row[ENERGY_EV];
  const compressedY = ev >= 0 ? ev : -((-ev) ** COMPRESS_POWER);
  return {
    id: row[LEVEL_ID],
    label: row[LEVEL_LABEL],
    energy: ev,
    compressedY,
  };
});

const levelById = new Map(levels.map((l) => [l.id, l]));

const minEv = Math.min(...levels.map((l) => l.energy));
const maxEv = Math.max(IONIZATION_EV, ...levels.map((l) => l.energy));
const evSpan = maxEv - minEv || 1;

const yTicks = Y_TICK_SHARES.map((share) => {
  const rawVal = Number((maxEv - share * evSpan).toFixed(1));
  const compressedY = rawVal >= 0 ? rawVal : -((-rawVal) ** COMPRESS_POWER);
  return { value: rawVal, compressedY };
});

const yDomainMin = Math.min(...levels.map((l) => l.compressedY));
const yCompressedSpan = Math.abs(yDomainMin) || 1;
const yDomainMax = yCompressedSpan * Y_TOP_PAD_SHARE;

const levelSpanX = LEVEL_X_END_SHARE - LEVEL_X_START_SHARE;
const arrowStartX = LEVEL_X_START_SHARE + levelSpanX * ARROW_INNER_PAD_SHARE;
const arrowEndX = LEVEL_X_END_SHARE - levelSpanX * ARROW_INNER_PAD_SHARE;
const transitionCount = transitionData.length;

const transitions = transitionData.map((row, idx) => {
  const xFrac =
    transitionCount > 1
      ? arrowStartX + ((arrowEndX - arrowStartX) * idx) / (transitionCount - 1)
      : (arrowStartX + arrowEndX) / 2;
  const fromLvl = levelById.get(row[FROM_LEVEL]) ?? levels[0];
  const toLvl = levelById.get(row[TO_LEVEL]) ?? levels[0];
  const lowerLvl = fromLvl.energy <= toLvl.energy ? fromLvl : toLvl;
  const upperCandidates = levels
    .filter((l) => l.energy > lowerLvl.energy)
    .sort((a, b) => a.energy - b.energy);
  const nextAboveLvl = upperCandidates[0] ?? toLvl;
  const color = groupColorMap.get(row[SERIES_GROUP]) ?? t.palette[0];
  return {
    x: xFrac,
    y1Compressed: fromLvl.compressedY,
    y2Compressed: toLvl.compressedY,
    labelLowCompressed: lowerLvl.compressedY,
    labelHighCompressed: nextAboveLvl.compressedY,
    color,
    wavelengthText: `${row[WAVELENGTH_NM].toFixed(1)} ${WAVELENGTH_UNIT}`,
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
          energy-level-atomic · javascript · muix · anyplot.ai
        </Typography>
      </Box>
      <Box sx={{ height: CONTEXT_H, display: "flex", alignItems: "center", pl: "28px" }}>
        <Typography sx={{ color: t.inkSoft, fontSize: 14, fontFamily: FONT }}>
          Hydrogen atom (Z = 1, {levels.length} bound states, {transitions.length} transitions) · compressed energy
          scale ({ENERGY_UNIT})
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
            Energy ({ENERGY_UNIT})
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
            labelStyle={{ fill: t.amber, fontSize: 14, fontWeight: 600, fontFamily: FONT }}
          />
        </ChartsContainer>
      </Box>
    </Box>
  );
}
