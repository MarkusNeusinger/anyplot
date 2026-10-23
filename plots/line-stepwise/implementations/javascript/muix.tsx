// anyplot.ai
// line-stepwise: Step Line Plot
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 84/100 | Updated: 2026-10-23

import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { Box, Typography } from "@mui/material";

const t = window.ANYPLOT_TOKENS;

// Columns: set these to your data's column names
const X = "Time of Day"; // role: x
const Y = "Setpoint (°F)"; // role: y

// Data: replace this block with your own records, one object per row
// Smart-thermostat setpoint schedule, logged every 15 minutes over a day.
const data = (() => {
  const samplesPerHour = 4;
  const schedule = [
    { hours: 6, setpoint: 62 }, // overnight sleep mode
    { hours: 2, setpoint: 68 }, // morning warm-up
    { hours: 9, setpoint: 65 }, // away / eco during work hours
    { hours: 5, setpoint: 72 }, // evening comfort
    { hours: 2, setpoint: 62 }, // night wind-down
  ];

  const rows: { [X]: number; [Y]: number }[] = [];
  let hour = 0;
  for (const block of schedule) {
    const samples = block.hours * samplesPerHour;
    for (let i = 0; i < samples; i += 1) {
      rows.push({ [X]: hour, [Y]: block.setpoint });
      hour += 1 / samplesPerHour;
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
const hoursOfDay = data.map((d) => d[X]);
const setpoints = data.map((d) => d[Y]);

// Unit from the y column's name, e.g. "Setpoint (°F)" -> "°F"
const Y_UNIT = Y.match(/\(([^)]*)\)\s*$/)?.[1] ?? "";
const formatY = (v: number) =>
  Y_UNIT.startsWith("°") || Y_UNIT === "%" ? `${v}${Y_UNIT}` : `${v} ${Y_UNIT}`.trim();

function formatHour(h: number) {
  const wholeHour = Math.floor(h);
  const minutes = Math.round((h - wholeHour) * 60);
  return `${String(wholeHour).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

const TITLE = "line-stepwise · javascript · muix · anyplot.ai";
const TITLE_H = 56;
const AREA_GRADIENT_ID = "stepAreaFillGradient";

const X_MIN = Math.floor(Math.min(...hoursOfDay));
const X_MAX = Math.ceil(Math.max(...hoursOfDay));
const MIN_SETPOINT = Math.min(...setpoints);
const PEAK_SETPOINT = Math.max(...setpoints);
const Y_SPAN = PEAK_SETPOINT - MIN_SETPOINT || 1;
const Y_MIN = Math.floor(MIN_SETPOINT - 0.7 * Y_SPAN);
const Y_MAX = Math.ceil(PEAK_SETPOINT + 0.6 * Y_SPAN);

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, px: "40px", pt: "14px", lineHeight: 1.2 }}>
        {TITLE}
      </Typography>
      <LineChart
        width={width}
        height={height - TITLE_H}
        skipAnimation
        disableHitArea
        hideLegend
        series={[
          {
            data: setpoints,
            label: Y,
            color: t.palette[0],
            curve: "step",
            area: true,
            showMark: false,
            valueFormatter: (v) => (v == null ? "" : formatY(v)),
          },
        ]}
        xAxis={[
          {
            height: 64,
            data: hoursOfDay,
            scaleType: "linear",
            label: X,
            min: X_MIN,
            max: X_MAX,
            tickNumber: 8,
            valueFormatter: (h) => formatHour(h),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            width: 76,
            min: Y_MIN,
            max: Y_MAX,
            label: Y,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        margin={{ top: 20, right: 56, bottom: 24, left: 40 }}
        grid={{ horizontal: true }}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiLineChart-area": { fill: `url(#${AREA_GRADIENT_ID})` },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        <defs>
          <linearGradient id={AREA_GRADIENT_ID} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={t.palette[0]} stopOpacity={0.35} />
            <stop offset="100%" stopColor={t.palette[0]} stopOpacity={0.03} />
          </linearGradient>
        </defs>
        <ChartsReferenceLine
          y={PEAK_SETPOINT}
          label={`Peak ${formatY(PEAK_SETPOINT)}`}
          labelAlign="start"
          lineStyle={{ stroke: t.ink, strokeDasharray: "6 4", strokeOpacity: 0.5 }}
          labelStyle={{ fill: t.inkSoft, fontSize: 13 }}
        />
      </LineChart>
    </Box>
  );
}
