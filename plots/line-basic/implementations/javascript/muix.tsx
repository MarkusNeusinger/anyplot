// anyplot.ai
// line-basic: Basic Line Plot
// Library: muix 9.17.0 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-08-24
import { LineChart } from "@mui/x-charts/LineChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const Y_PAD_SHARE = 0.08; // share of the value range added above and below the line
const X_PAD_SHARE = 0.015; // share of the time span added before the first and after the last reading

// Columns: set these to your data's column names
const DATE = "Date"; // role: x
const TEMPERATURE = "Daily mean temperature (°C)"; // role: y

// Data: replace this block with your own records, one object per reading
// Daily mean temperature over eight weeks of early spring from 1 Mar 2026: a seasonal rise
// of about 0.28 °C per day with day-to-day weather noise.
const data = (() => {
  let state = 42;
  const rand = () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
  return Array.from({ length: 56 }, (_, day) => ({
    [DATE]: new Date(Date.UTC(2026, 2, 1 + day)).toISOString().slice(0, 10),
    [TEMPERATURE]: Math.round((8 + day * 0.28 + (rand() - 0.5) * 3) * 10) / 10,
  }));
})();

// Plot: reads only data and the constants above
// ISO dates are read as local midnight, the frame the time axis places its ticks in
const rows = [...data].sort((a, b) => Date.parse(a[DATE]) - Date.parse(b[DATE]));
const n = rows.length;
const dates = rows.map((d) => new Date(`${d[DATE]}T00:00:00`));
const values = rows.map((d) => d[TEMPERATURE] ?? null);
const present = values.filter((v) => v != null);
const yLow = Math.min(...present);
const yHigh = Math.max(...present);
const yPad = (yHigh - yLow) * Y_PAD_SHARE;
const xPadMs = (dates[n - 1].getTime() - dates[0].getTime()) * X_PAD_SHARE;
const unit = TEMPERATURE.match(/\(([^)]+)\)/)?.[1];

const dayFormat = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" });
const fullFormat = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric" });

const TITLE = "line-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${n} readings, ${fullFormat.format(dates[0])} – ${fullFormat.format(dates[n - 1])}`;
const HEADER_H = 84;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <Box sx={{ height: HEADER_H, pt: "14px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.3 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.6 }}>{SUBTITLE}</Typography>
      </Box>
      <LineChart
        width={width}
        height={height - HEADER_H}
        skipAnimation
        hideLegend
        grid={{ horizontal: true }}
        margin={{ top: 16, right: 48, bottom: 16, left: 20 }}
        series={[
          {
            id: "temperature",
            data: values,
            label: TEMPERATURE,
            color: t.palette[0],
            curve: "linear",
            showMark: true,
            shape: "circle",
            valueFormatter: (v) => (v == null ? "" : unit ? `${v} ${unit}` : String(v)),
          },
        ]}
        xAxis={[
          {
            data: dates,
            scaleType: "time",
            min: new Date(dates[0].getTime() - xPadMs),
            max: new Date(dates[n - 1].getTime() + xPadMs),
            tickNumber: 9,
            valueFormatter: (v: Date, context) =>
              context.location === "tick" ? dayFormat.format(v) : fullFormat.format(v),
            label: DATE,
            height: 64,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: yLow - yPad,
            max: yHigh + yPad,
            width: 72,
            label: TEMPERATURE,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiLineChart-mark": { r: 4, strokeWidth: 2, fill: t.pageBg },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      />
    </Box>
  );
}
