//# anyplot-orientation: square
// anyplot.ai
// waffle-basic: Basic Waffle Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-09

import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";

const t = window.ANYPLOT_TOKENS;
const FONT = "system-ui, -apple-system, sans-serif";
const TITLE = "waffle-basic · javascript · muix · anyplot.ai";

// Imprint's theme-adaptive "muted" anchor (other/rest) isn't part of
// ANYPLOT_TOKENS, so it's derived here the same way the style guide defines it.
const MUTED = window.ANYPLOT_THEME === "dark" ? "#A8A79F" : "#6B6A63";

// --- Data (in-memory, deterministic) ----------------------------------------
// Annual engineering-org budget allocation by department. Values sum to 100 —
// one grid square per percentage point, the canonical waffle-chart mapping.
// "Other" gets the theme-adaptive muted anchor (other/rest semantic exception)
// instead of the next ordinal palette slot.
const CATEGORIES = [
  { label: "Engineering", pct: 34, color: t.palette[0] },
  { label: "Sales", pct: 21, color: t.palette[1] },
  { label: "Marketing", pct: 17, color: t.palette[2] },
  { label: "Operations", pct: 16, color: t.palette[3] },
  { label: "Other", pct: 12, color: MUTED },
];

const GRID_SIZE = 10; // 10x10 = 100 squares, one per percentage point
const COLS = Array.from({ length: GRID_SIZE }, (_, i) => i);
const ROWS = Array.from({ length: GRID_SIZE }, (_, i) => i);

// Fill the grid row-major, left-to-right then top-to-bottom, handing each
// category a contiguous block of squares in the order above.
let cellIndex = 0;
const series = CATEGORIES.map((category) => {
  const data = [];
  for (let i = 0; i < category.pct; i += 1) {
    data.push({
      id: `cell-${cellIndex}`,
      x: cellIndex % GRID_SIZE,
      y: Math.floor(cellIndex / GRID_SIZE),
    });
    cellIndex += 1;
  }
  return {
    type: "scatter",
    id: category.label.toLowerCase(),
    data,
    label: `${category.label} — ${category.pct}%`,
  };
});
const COLORS = CATEGORIES.map((category) => category.color);

// Custom scatter mark: opaque squares tiling the band grid, colored per series
// rather than by a continuous data value — this is what turns MUI X's
// ScatterPlot into a waffle/unit-chart grid instead of a scatter of dots.
function WaffleSquares({ series: seriesData, xScale, yScale, color }) {
  const cellW = xScale.bandwidth();
  const cellH = yScale.bandwidth();
  const radius = Math.min(cellW, cellH) * 0.15;
  return (
    <g>
      {seriesData.data.map((pt) => (
        <rect
          key={pt.id}
          x={xScale(pt.x) ?? 0}
          y={yScale(pt.y) ?? 0}
          width={cellW}
          height={cellH}
          rx={radius}
          fill={color}
        />
      ))}
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;

  // Reserve space for the title (top) and the legend (right), then size the
  // waffle grid to the largest square that fits the remaining area so every
  // one of the 100 cells is a true square.
  const TITLE_SPACE = 80;
  const PAD = 28;
  const LEGEND_WIDTH = 320;

  const availW = W - PAD * 2 - LEGEND_WIDTH;
  const availH = H - TITLE_SPACE - PAD * 2;
  const grid = Math.min(availW, availH);

  // Top-align the grid right below the title (instead of centering it in the
  // full available height) so the composition doesn't carry a dead gap above
  // the squares purely because the width, not the height, is the constraint.
  const margin = {
    left: PAD + (availW - grid) / 2,
    right: W - PAD - (availW - grid) / 2 - grid,
    top: TITLE_SPACE + PAD,
    bottom: H - TITLE_SPACE - PAD - grid,
  };
  const gridCenterY = margin.top + grid / 2;

  return (
    <ChartContainer
      width={W}
      height={H}
      margin={margin}
      skipAnimation
      colors={COLORS}
      series={series}
      xAxis={[{ scaleType: "band", data: COLS, categoryGapRatio: 0.18 }]}
      yAxis={[{ scaleType: "band", data: ROWS, categoryGapRatio: 0.18 }]}
    >
      {/* Chart title */}
      <text
        x={W / 2}
        y={44}
        textAnchor="middle"
        fontSize={22}
        fontWeight="500"
        fill={t.ink}
        fontFamily={FONT}
      >
        {TITLE}
      </text>

      {/* The waffle grid — 100 squares, one per percentage point */}
      <ScatterPlot slots={{ scatter: WaffleSquares }} />

      <ChartsLegend
        position={{ horizontal: "right", vertical: "middle" }}
        direction="column"
        itemMarkWidth={26}
        itemMarkHeight={26}
        markGap={14}
        itemGap={22}
        // "middle" centers within [padding.top, H - padding.bottom] — bias the
        // padding so that band's midpoint lands on the grid's vertical center
        // instead of the full canvas center (which sits above the top-aligned grid).
        padding={{ top: 0, right: 24, bottom: Math.max(0, H - 2 * gridCenterY), left: 0 }}
        labelStyle={{ fontSize: 20, fill: t.ink, fontFamily: FONT }}
      />
    </ChartContainer>
  );
}
