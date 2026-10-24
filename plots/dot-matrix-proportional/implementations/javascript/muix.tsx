// anyplot.ai
// dot-matrix-proportional: Dot Matrix Chart for Proportional Counts
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 83/100 | Updated: 2026-10-24
//# anyplot-orientation: square

import * as React from "react";
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;
const MUTED = window.ANYPLOT_THEME === "dark" ? "#A8A79F" : "#6B6A63";

// Constants
const FONT = "system-ui, -apple-system, sans-serif";
const TITLE = "dot-matrix-proportional · javascript · muix · anyplot.ai";
const SEMANTIC_COLORS: Record<string, string> = {
  Agreed: t.palette[0],
  Disagreed: t.palette[4],
  "No opinion": MUTED,
};
const REMAINDER_LABEL = "Remainder";
const MARKER_CELL_SHARE = 0.38;
const TITLE_HEIGHT = 76;
const LEGEND_HEIGHT = 84;

// Columns: set these to your data's column names
const CATEGORY = "Response category"; // role: category
const COUNT = "Respondent count"; // role: count
const TOTAL = "Total population"; // role: total

// Data: replace this block with your own records
const data = [
  { [CATEGORY]: "Agreed", [COUNT]: 47, [TOTAL]: 100 },
  { [CATEGORY]: "Disagreed", [COUNT]: 35, [TOTAL]: 100 },
  { [CATEGORY]: "No opinion", [COUNT]: 18, [TOTAL]: 100 },
];

// Plot: reads only data and the constants above
const listedSum = data.reduce((acc, r) => acc + Number(r[COUNT]), 0);
const declaredTotal = Math.max(...data.map((r) => Number(r[TOTAL])), listedSum);
const remainderCount = Math.max(0, declaredTotal - listedSum);

const gridCols = Math.ceil(Math.sqrt(declaredTotal));
const gridRows = Math.ceil(declaredTotal / gridCols);

const usedPalette = new Set(Object.values(SEMANTIC_COLORS));
const availablePalette = t.palette.filter((c: string) => !usedPalette.has(c));
let fallbackIdx = 0;

const categories = data.map((r) => {
  const label = String(r[CATEGORY]);
  const count = Number(r[COUNT]);
  let color = SEMANTIC_COLORS[label];
  if (!color) {
    color = availablePalette[fallbackIdx];
    fallbackIdx += 1;
  }
  return { label, count, color };
});

if (remainderCount > 0) {
  categories.push({
    label: REMAINDER_LABEL,
    count: remainderCount,
    color: t.grid,
  });
}

let dotIndex = 0;
const seriesDataByCategory = categories.map((cat) => {
  const pts: { x: number; y: number; id: number }[] = [];
  for (let n = 0; n < cat.count; n += 1) {
    const row = Math.floor(dotIndex / gridCols);
    const col = dotIndex % gridCols;
    pts.push({ x: col, y: gridRows - 1 - row, id: dotIndex });
    dotIndex += 1;
  }
  return {
    ...cat,
    points: pts,
  };
});

export default function Chart() {
  const width = window.ANYPLOT_SIZE.width;
  const height = window.ANYPLOT_SIZE.height;

  const availW = width - 48;
  const availH = height - TITLE_HEIGHT - LEGEND_HEIGHT;
  const cellSize = Math.min(availW / gridCols, availH / gridRows);
  const gridWidth = cellSize * gridCols;
  const gridHeight = cellSize * gridRows;
  const markerSize = cellSize * MARKER_CELL_SHARE;

  return (
    <Box
      sx={{
        width,
        height,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <Box
        sx={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 600, fontFamily: FONT }}>
          {TITLE}
        </Typography>
      </Box>

      <Box sx={{ position: "relative", width: gridWidth, height: gridHeight, flexShrink: 0 }}>
        <ChartsContainer
          width={gridWidth}
          height={gridHeight}
          margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
          skipAnimation
          series={seriesDataByCategory.map((cat) => ({
            type: "scatter" as const,
            id: cat.label,
            label: cat.label,
            color: cat.color,
            markerSize,
            data: cat.points,
          }))}
          xAxis={[
            {
              scaleType: "linear",
              min: -0.5,
              max: gridCols - 0.5,
              position: "none",
              domainLimit: "strict",
            },
          ]}
          yAxis={[
            {
              scaleType: "linear",
              min: -0.5,
              max: gridRows - 0.5,
              position: "none",
              domainLimit: "strict",
            },
          ]}
        >
          <ScatterPlot />
        </ChartsContainer>
      </Box>

      <Box
        sx={{
          height: LEGEND_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "40px",
          flexShrink: 0,
        }}
      >
        {seriesDataByCategory.map((category) => (
          <Box key={category.label} sx={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <Box
              sx={{
                width: 20,
                height: 20,
                borderRadius: "50%",
                backgroundColor: category.color,
                flexShrink: 0,
              }}
            />
            <Typography sx={{ color: t.ink, fontSize: 16, fontFamily: FONT }}>
              {category.label} — {category.count} ({Math.round((category.count / declaredTotal) * 100)}%)
            </Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
}
