// anyplot.ai
// line-basic: Basic Line Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-08-24
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
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
const avgTemperature = Math.round((temperatures.reduce((sum, v) => sum + v, 0) / temperatures.length) * 10) / 10;

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
              area: true,
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
            "& .MuiMarkElement-root": { r: 6, stroke: t.pageBg, strokeWidth: 2, fill: t.palette[0] },
            "& .MuiAreaElement-root": { fill: t.palette[0], fillOpacity: 0.12 },
            "& .MuiChartsGrid-line": { strokeDasharray: "4 3" },
          }}
        >
          <ChartsReferenceLine
            y={avgTemperature}
            label={`Avg ${avgTemperature}°C`}
            labelAlign="end"
            lineStyle={{ stroke: t.inkSoft, strokeDasharray: "6 4", strokeWidth: 1.5 }}
            labelStyle={{ fontSize: 13, fill: t.inkSoft }}
          />
        </LineChart>
      </Box>
    </Box>
  );
}
