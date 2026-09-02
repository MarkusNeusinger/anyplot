// anyplot.ai
// area-stacked-percent: 100% Stacked Area Chart
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-09-02
import { LineChart } from "@mui/x-charts/LineChart";
import { Box, Typography } from "@mui/material";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Illustrative global electricity generation mix, 2010-2024 (TWh per source).
// Solar and wind grow quadratically (falling technology cost curve), hydro and
// nuclear stay roughly flat, fossil declines linearly — the energy-transition
// story the 100% stacking is meant to surface.
const YEARS = Array.from({ length: 15 }, (_, i) => 2010 + i);

const solarTWh = YEARS.map((_, i) => 4 + Math.round(i * i * 1.6));
const windTWh = YEARS.map((_, i) => 15 + Math.round(i * i * 0.9));
const hydroTWh = YEARS.map((_, i) => 150 + i * 3);
const nuclearTWh = YEARS.map((_, i) => 260 - i * 2);
const fossilTWh = YEARS.map((_, i) => 680 - i * 18);

const totalByYear = YEARS.map(
  (_, i) => solarTWh[i] + windTWh[i] + hydroTWh[i] + nuclearTWh[i] + fossilTWh[i],
);

const shareValueFormatter = (value, { dataIndex }) =>
  `${Math.round((value / totalByYear[dataIndex]) * 100)}% · ${value.toLocaleString()} TWh`;

const TITLE = "area-stacked-percent · javascript · muix · anyplot.ai";

// --- Chart (default-exported component — the harness mounts it) ------------
export default function Chart() {
  const size = window.ANYPLOT_SIZE;
  const padding = { top: 28, right: 40, bottom: 24, left: 40 };
  const titleBlockHeight = 56;
  // Hand-rotated axis label in its own flex column avoids MUI X's y-axis
  // `label` offset (tuned for a fixed guessed tick width) colliding with the
  // 3-character percent tick labels.
  const yLabelWidth = 32;
  const chartWidth = size.width - padding.left - padding.right - yLabelWidth;
  const chartHeight = size.height - padding.top - padding.bottom - titleBlockHeight;

  return (
    <Box
      sx={{
        width: size.width,
        height: size.height,
        boxSizing: "border-box",
        padding: `${padding.top}px ${padding.right}px ${padding.bottom}px ${padding.left}px`,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Typography sx={{ fontSize: 22, fontWeight: 600, color: "text.primary", mb: "20px", lineHeight: 1 }}>
        {TITLE}
      </Typography>
      <Box sx={{ display: "flex", flexDirection: "row", height: chartHeight }}>
        <Box sx={{ width: yLabelWidth, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Typography
            sx={{
              fontSize: 16,
              color: "text.secondary",
              whiteSpace: "nowrap",
              transform: "rotate(-90deg)",
            }}
          >
            Share of generation
          </Typography>
        </Box>
        <LineChart
          width={chartWidth}
          height={chartHeight}
          skipAnimation
          margin={{ bottom: 90 }}
          series={[
            {
              id: "solar",
              label: "Solar",
              data: solarTWh,
              stack: "mix",
              stackOffset: "expand",
              area: true,
              showMark: false,
              color: t.palette[0],
              valueFormatter: shareValueFormatter,
            },
            {
              id: "wind",
              label: "Wind",
              data: windTWh,
              stack: "mix",
              stackOffset: "expand",
              area: true,
              showMark: false,
              color: t.palette[1],
              valueFormatter: shareValueFormatter,
            },
            {
              id: "hydro",
              label: "Hydro",
              data: hydroTWh,
              stack: "mix",
              stackOffset: "expand",
              area: true,
              showMark: false,
              color: t.palette[2],
              valueFormatter: shareValueFormatter,
            },
            {
              id: "nuclear",
              label: "Nuclear",
              data: nuclearTWh,
              stack: "mix",
              stackOffset: "expand",
              area: true,
              showMark: false,
              color: t.palette[3],
              valueFormatter: shareValueFormatter,
            },
            {
              id: "fossil",
              label: "Fossil",
              data: fossilTWh,
              stack: "mix",
              stackOffset: "expand",
              area: true,
              showMark: false,
              color: t.palette[4],
              valueFormatter: shareValueFormatter,
            },
          ]}
          xAxis={[
            {
              data: YEARS,
              scaleType: "point",
              valueFormatter: (year) => `${year}`,
              tickLabelStyle: { fontSize: 14 },
            },
          ]}
          yAxis={[
            {
              min: 0,
              max: 1,
              valueFormatter: (value) => `${Math.round(value * 100)}%`,
              tickLabelStyle: { fontSize: 14 },
            },
          ]}
          grid={{ horizontal: true }}
          slotProps={{
            legend: {
              direction: "row",
              position: { vertical: "bottom", horizontal: "center" },
              labelStyle: { fontSize: 14 },
              itemMarkWidth: 18,
              itemMarkHeight: 10,
              markGap: 8,
            },
          }}
          sx={{
            "& .MuiLineElement-root": { strokeWidth: 1.5 },
            "& .MuiAreaElement-root": { fillOpacity: 0.9 },
            "& .MuiChartsGrid-line": { strokeDasharray: "4 3" },
          }}
        />
      </Box>
    </Box>
  );
}
