// anyplot.ai
// line-stepwise: Step Line Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-09-05
import { LineChart } from "@mui/x-charts/LineChart";
import { Box, Typography } from "@mui/material";

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Smart-thermostat setpoint schedule, logged every 15 minutes over a day. The
// schedule engine issues a new setpoint at fixed hours, but the telemetry
// logger only samples on a fixed cadence — the exact moment a command took
// effect sits somewhere between two consecutive readings, so mid-point step
// alignment (`curve="step"`) represents that uncertainty honestly, unlike
// "stepAfter" (which would claim the change landed exactly on a sample).
const SAMPLES_PER_HOUR = 4;
const SCHEDULE = [
  { hours: 6, setpoint: 62 }, // overnight sleep mode
  { hours: 2, setpoint: 68 }, // morning warm-up
  { hours: 9, setpoint: 65 }, // away / eco during work hours
  { hours: 5, setpoint: 72 }, // evening comfort
  { hours: 2, setpoint: 62 }, // night wind-down
];

const hoursOfDay = [];
const setpoints = [];
let hour = 0;
for (const block of SCHEDULE) {
  const samples = block.hours * SAMPLES_PER_HOUR;
  for (let i = 0; i < samples; i += 1) {
    hoursOfDay.push(hour);
    setpoints.push(block.setpoint);
    hour += 1 / SAMPLES_PER_HOUR;
  }
}

function formatHour(h) {
  const wholeHour = Math.floor(h);
  const minutes = Math.round((h - wholeHour) * 60);
  return `${String(wholeHour).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

const TITLE = "line-stepwise · javascript · muix · anyplot.ai";

// --- Chart (default-exported component — the harness mounts it) ------------
export default function Chart() {
  const size = window.ANYPLOT_SIZE;
  const padding = { top: 28, right: 56, bottom: 24, left: 40 };
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
            Setpoint (°F)
          </Typography>
        </Box>
        <LineChart
          width={chartWidth}
          height={chartHeight}
          skipAnimation
          series={[
            {
              data: setpoints,
              color: t.palette[0],
              curve: "step",
              area: true,
              showMark: false,
              valueFormatter: (v) => `${v}°F`,
            },
          ]}
          xAxis={[
            {
              data: hoursOfDay,
              scaleType: "linear",
              label: "Time of Day",
              min: 0,
              max: 24,
              tickNumber: 8,
              valueFormatter: (h) => formatHour(h),
              tickLabelStyle: { fontSize: 14 },
              labelStyle: { fontSize: 16 },
            },
          ]}
          yAxis={[
            {
              min: 55,
              max: 78,
              tickLabelStyle: { fontSize: 14 },
            },
          ]}
          grid={{ horizontal: true }}
          slotProps={{ legend: { hidden: true } }}
          sx={{
            "& .MuiLineElement-root": { strokeWidth: 3 },
            "& .MuiAreaElement-root": { fill: t.palette[0], fillOpacity: 0.12 },
            "& .MuiChartsGrid-line": { strokeDasharray: "4 3" },
          }}
        />
      </Box>
    </Box>
  );
}
