//# anyplot-orientation: square
// anyplot.ai
// venn-basic: Venn Diagram
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-09
import * as React from "react";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Skill overlap across a 200-person data team.
const setLabels = ["Python", "SQL", "Statistics"];
const setSizes = [120, 95, 80];
const pairAB = 45; // Python & SQL
const pairAC = 38; // Python & Statistics
const pairBC = 30; // SQL & Statistics
const tripleABC = 18; // all three

const onlyA = setSizes[0] - pairAB - pairAC + tripleABC;
const onlyB = setSizes[1] - pairAB - pairBC + tripleABC;
const onlyC = setSizes[2] - pairAC - pairBC + tripleABC;
const onlyAB = pairAB - tripleABC;
const onlyAC = pairAC - tripleABC;
const onlyBC = pairBC - tripleABC;

const seriesColors = [t.palette[0], t.palette[1], t.palette[2]];

// --- Custom SVG marks, placed via ChartContainer's drawing area -------------
// MUI X community has no native Venn primitive, so this follows MUI X's
// documented composition pattern (ChartContainer + useDrawingArea) to
// hand-place plain SVG circles/text inside the theme-aware ChartsSurface.
function VennMarks() {
  const area = useDrawingArea();
  const cx = area.left + area.width / 2;
  const cy = area.top + area.height / 2;

  const maxRadius = Math.min(area.width, area.height) * 0.32;
  const scale = maxRadius / Math.sqrt(Math.max(...setSizes));
  const radii = setSizes.map((size) => Math.sqrt(size) * scale);
  const avgRadius = (radii[0] + radii[1] + radii[2]) / 3;
  const offset = avgRadius * 0.55;

  const centers = [
    { x: cx, y: cy - offset },
    { x: cx - offset * 0.87, y: cy + offset * 0.5 },
    { x: cx + offset * 0.87, y: cy + offset * 0.5 },
  ];

  const textProps = {
    textAnchor: "middle" as const,
    dominantBaseline: "middle" as const,
    fill: t.ink,
    paintOrder: "stroke" as const,
    stroke: t.pageBg,
    strokeWidth: 5,
    strokeLinejoin: "round" as const,
  };

  const onlyRegions = [
    { name: setLabels[0], count: onlyA, x: centers[0].x, y: centers[0].y - radii[0] * 0.45 },
    { name: setLabels[1], count: onlyB, x: centers[1].x - radii[1] * 0.32, y: centers[1].y + radii[1] * 0.4 },
    { name: setLabels[2], count: onlyC, x: centers[2].x + radii[2] * 0.32, y: centers[2].y + radii[2] * 0.4 },
  ];

  const overlapRegions = [
    { count: onlyAB, x: (centers[0].x + centers[1].x) / 2 - offset * 0.08, y: (centers[0].y + centers[1].y) / 2 },
    { count: onlyAC, x: (centers[0].x + centers[2].x) / 2 + offset * 0.08, y: (centers[0].y + centers[2].y) / 2 },
    { count: onlyBC, x: cx, y: centers[1].y + radii[1] * 0.62 },
    { count: tripleABC, x: cx, y: cy + offset * 0.05 },
  ];

  return (
    <>
      {centers.map((c, i) => (
        <circle
          key={setLabels[i]}
          cx={c.x}
          cy={c.y}
          r={radii[i]}
          fill={seriesColors[i]}
          fillOpacity={0.55}
          stroke={seriesColors[i]}
          strokeWidth={2}
        />
      ))}
      {onlyRegions.map((r) => (
        <React.Fragment key={r.name}>
          <text {...textProps} x={r.x} y={r.y - 20} fontSize={20} fontWeight={600}>
            {r.name}
          </text>
          <text {...textProps} x={r.x} y={r.y + 14} fontSize={30} fontWeight={700}>
            {r.count}
          </text>
        </React.Fragment>
      ))}
      {overlapRegions.map((r, i) => (
        <text key={i} {...textProps} x={r.x} y={r.y} fontSize={22} fontWeight={600}>
          {r.count}
        </text>
      ))}
    </>
  );
}

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  const width = window.ANYPLOT_SIZE.width;
  const height = window.ANYPLOT_SIZE.height;
  const titleHeight = 76;

  return (
    <Box sx={{ width, height, display: "flex", flexDirection: "column" }}>
      <Typography
        sx={{
          height: titleHeight,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          fontWeight: 500,
          color: t.ink,
        }}
      >
        venn-basic · javascript · muix · anyplot.ai
      </Typography>
      <ChartContainer
        width={width}
        height={height - titleHeight}
        margin={{ top: 20, bottom: 20, left: 20, right: 20 }}
        series={[]}
        skipAnimation
      >
        <VennMarks />
      </ChartContainer>
    </Box>
  );
}
