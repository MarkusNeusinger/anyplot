//# anyplot-orientation: landscape
// anyplot.ai
// bar-pareto: Pareto Chart with Cumulative Line
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-20

import { ChartContainer } from "@mui/x-charts/ChartContainer";
import { BarPlot } from "@mui/x-charts/BarChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Manufacturing QC: defect frequency analysis — sorted descending
const categories = [
  "Scratches", "Dents", "Cracks", "Warping",
  "Discolor.", "Miss. Part", "Wrong Size", "Surf. Flaw",
];
const counts = [412, 298, 187, 143, 98, 76, 54, 32];
const total = counts.reduce((a, b) => a + b, 0); // 1300

// Cumulative percentages: 31.7, 54.6, 69.0, 80.0, 87.5, 93.4, 97.5, 100.0
let running = 0;
const cumPercent = counts.map((c) => {
  running += c;
  return parseFloat(((running / total) * 100).toFixed(1));
});

const COUNT_MAX = 460;       // primary y-axis max (headroom above 412)
const PCT_SCALE = COUNT_MAX / 100; // 4.6 — maps 100% → COUNT_MAX

// Cumulative values in primary-axis units (same scale as bars)
const scaledCum = cumPercent.map((p) => parseFloat((p * PCT_SCALE).toFixed(1)));
// [145.8, 251.2, 317.4, 368.0, 402.5, 429.6, 448.5, 460.0]

// 80% threshold in primary scale units (80 × 4.6 = 368)
const EIGHTY_Y = 80 * PCT_SCALE;

const MARGIN = { top: 24, right: 90, bottom: 72, left: 80 };

// Renders inside ChartContainer's SVG — uses MUI X coordinate hooks.
// useXScale()/useYScale() return values in FULL SVG coordinates (margins included),
// so NO translate is needed on the <g> element.
function CumulativeLine() {
  const xScale = useXScale();
  const yScale = useYScale("counts");

  if (!xScale || !yScale || typeof xScale.bandwidth !== "function") return null;

  const bw = xScale.bandwidth();
  const pts = scaledCum.map((v, i) => ({
    x: (xScale(categories[i]) ?? 0) + bw / 2, // center of each bar, SVG x coords
    y: yScale(v) ?? 0,                          // SVG y coords (includes margin.top)
  }));

  const pathD = pts.map(({ x, y }, i) => `${i === 0 ? "M" : "L"}${x},${y}`).join(" ");

  return (
    // No translate — scale output is already in full SVG coordinate space
    <g>
      <path
        d={pathD}
        fill="none"
        stroke={t.palette[1]}
        strokeWidth={3}
        strokeLinejoin="round"
      />
      {pts.map(({ x, y }, i) => (
        <circle
          key={i}
          cx={x}
          cy={y}
          r={7}
          fill={t.palette[1]}
          stroke={t.pageBg}
          strokeWidth={2}
        />
      ))}
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;   // 1600 CSS px (landscape)
  const H = window.ANYPLOT_SIZE.height;  // 900 CSS px
  const TITLE_H = 72;
  const LEGEND_H = 44;
  const chartH = H - TITLE_H - LEGEND_H; // 784

  return (
    <Box
      sx={{
        width: W,
        height: H,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        fontFamily: "'Roboto', 'Helvetica Neue', Arial, sans-serif",
        boxSizing: "border-box",
      }}
    >
      {/* Title */}
      <Box sx={{ height: TITLE_H, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Typography sx={{ color: t.ink, fontSize: 22, fontWeight: 600 }}>
          bar-pareto · javascript · muix · anyplot.ai
        </Typography>
      </Box>

      {/* Chart */}
      <ChartContainer
        width={W}
        height={chartH}
        series={[
          {
            type: "bar",
            id: "defect-counts",
            yAxisId: "counts",
            data: counts,
            label: "Defect Count",
            color: t.palette[0],
          },
        ]}
        xAxis={[
          {
            id: "x",
            scaleType: "band",
            data: categories,
            categoryGapRatio: 0.38,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "counts",
            min: 0,
            max: COUNT_MAX,
            tickInterval: [0, 100, 200, 300, 400],
            tickLabelStyle: { fontSize: 13, fill: t.inkSoft },
          },
          {
            // Right axis: same 0–460 range re-labelled as 0–100%
            id: "percentR",
            position: "right",
            min: 0,
            max: COUNT_MAX,
            tickInterval: [0, 92, 184, 276, 368, 460], // 0 20 40 60 80 100 %
            valueFormatter: (v) => `${Math.round(v / PCT_SCALE)}%`,
            tickLabelStyle: { fontSize: 13, fill: t.inkSoft },
          },
        ]}
        margin={MARGIN}
        skipAnimation
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft, strokeOpacity: 0.4 },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ChartsGrid horizontal />
        <BarPlot />
        <CumulativeLine />
        {/* 80% threshold: y=368 on primary scale == 80% on right-axis label */}
        <ChartsReferenceLine
          y={EIGHTY_Y}
          axisId="counts"
          label="80%"
          labelAlign="end"
          lineStyle={{ stroke: t.amber, strokeDasharray: "8 5", strokeWidth: 2.5 }}
          labelStyle={{ fill: t.amber, fontSize: 14, fontWeight: 700 }}
        />
        <ChartsXAxis axisId="x" position="bottom" label="Defect Type" labelStyle={{ fontSize: 14, fill: t.ink }} />
        <ChartsYAxis axisId="counts" position="left" label="Defect Count" labelStyle={{ fontSize: 14, fill: t.ink }} />
        <ChartsYAxis axisId="percentR" position="right" label="Cumulative %" labelStyle={{ fontSize: 14, fill: t.ink }} disableLine />
      </ChartContainer>

      {/* Legend */}
      <Box sx={{ height: LEGEND_H, display: "flex", alignItems: "center", justifyContent: "center", gap: "36px" }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Box sx={{ width: 22, height: 14, bgcolor: t.palette[0], borderRadius: "2px", flexShrink: 0 }} />
          <Typography sx={{ color: t.inkSoft, fontSize: 14 }}>Defect Count</Typography>
        </Box>
        <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Box sx={{ width: 24, height: 3, bgcolor: t.palette[1], borderRadius: "2px", flexShrink: 0 }} />
          <Typography sx={{ color: t.inkSoft, fontSize: 14 }}>Cumulative %</Typography>
        </Box>
        <Box sx={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Box sx={{ width: 24, height: 0, borderTop: `2.5px dashed ${t.amber}`, flexShrink: 0 }} />
          <Typography sx={{ color: t.inkSoft, fontSize: 14 }}>80% Threshold</Typography>
        </Box>
      </Box>
    </Box>
  );
}
