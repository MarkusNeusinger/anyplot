// anyplot.ai
// line-basic: Basic Line Plot
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-08-24
import { LineChart } from "@mui/x-charts/LineChart";
import { Box, Typography } from "@mui/material";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Daily average temperature across an 8-week early-spring warming trend, with
// day-to-day weather noise layered on top of the seasonal rise.
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(42);

const NUM_DAYS = 56;
const START_DATE = new Date(2026, 2, 1);
const dates = Array.from({ length: NUM_DAYS }, (_, day) => {
  const d = new Date(START_DATE);
  d.setDate(d.getDate() + day);
  return d;
});

const temperatures = dates.map((_, day) => {
  const seasonalRise = day * 0.28;
  const noise = (rand() - 0.5) * 3;
  return Math.round((8 + seasonalRise + noise) * 10) / 10;
});

const TITLE = "line-basic · javascript · muix · anyplot.ai";

// --- Chart (default-exported component — the harness mounts it) ------------
export default function Chart() {
  const size = window.ANYPLOT_SIZE;
  const padding = { top: 28, right: 48, bottom: 24, left: 40 };
  const titleBlockHeight = 56;
  const yLabelWidth = 34;
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
            Temperature (°C)
          </Typography>
        </Box>
        <LineChart
          width={chartWidth}
          height={chartHeight}
          skipAnimation
          series={[
            {
              data: temperatures,
              color: t.palette[0],
              showMark: true,
              curve: "monotoneX",
              valueFormatter: (v) => `${v}°C`,
            },
          ]}
          xAxis={[
            {
              data: dates,
              scaleType: "time",
              label: "Date",
              valueFormatter: (date) => date.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
              tickLabelStyle: { fontSize: 14 },
              labelStyle: { fontSize: 16 },
            },
          ]}
          yAxis={[
            {
              tickLabelStyle: { fontSize: 14 },
            },
          ]}
          grid={{ horizontal: true }}
          slotProps={{ legend: { hidden: true } }}
          sx={{
            "& .MuiLineElement-root": { strokeWidth: 3 },
            "& .MuiMarkElement-root": { r: 4, stroke: t.pageBg, strokeWidth: 2, fill: t.palette[0] },
            "& .MuiChartsGrid-line": { strokeDasharray: "4 3" },
          }}
        />
      </Box>
    </Box>
  );
}
