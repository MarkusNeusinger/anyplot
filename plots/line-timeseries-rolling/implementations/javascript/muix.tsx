// anyplot.ai
// line-timeseries-rolling: Time Series with Rolling Average Overlay
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 86/100 | Updated: 2026-11-08
import { LineChart } from "@mui/x-charts/LineChart";

const t = window.ANYPLOT_TOKENS;

// Constants
const DAY_MS = 86_400_000;
const Y_PAD_SHARE = 0.06; // share of the value range added below and above the lines

// Columns: set these to your data's column names
const DATE = "Date"; // role: date
const VISITORS = "Unique visitors"; // role: value
const ROLLING = "Rolling average"; // role: rolling_avg

// Data: replace this block with your own records, one object per row
// Daily unique visitors to a blog over 120 days: weekend dips, a slow climb, a two-week surge
// after a viral post, day-to-day noise, and the trailing 7-day mean (empty until the window is full).
const data = (() => {
  let seed = 42;
  const rand = () => {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
  const WINDOW_DAYS = 7;
  const visitors = Array.from({ length: 120 }, (_, day) => {
    const date = new Date(2026, 0, 1 + day);
    const weekendDip = date.getDay() === 0 || date.getDay() === 6 ? 0.62 : 1;
    const surge = day >= 58 && day <= 74 ? 1 + 0.5 * Math.sin(((day - 58) / 16) * Math.PI) : 1;
    const noise = 1 + (rand() - 0.5) * 0.22;
    return { date, value: Math.max(300, Math.round(2200 * weekendDip * (1 + day * 0.004) * surge * noise)) };
  });
  return visitors.map((v, i) => ({
    [DATE]: v.date,
    [VISITORS]: v.value,
    [ROLLING]:
      i < WINDOW_DAYS - 1
        ? null
        : Math.round(visitors.slice(i - WINDOW_DAYS + 1, i + 1).reduce((s, w) => s + w.value, 0) / WINDOW_DAYS),
  }));
})();

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[DATE] - b[DATE]);
const dates = rows.map((d) => d[DATE]);
const raw = rows.map((d) => d[VISITORS]);
const rolling = rows.map((d) => d[ROLLING]);

// The trailing window is as long as the run of observations before the first rolling value, plus one
const firstRolling = rolling.findIndex((v) => v != null);
const windowSize = firstRolling + 1;
const stepDays = Math.round((dates[1] - dates[0]) / DAY_MS);
const windowLabel = stepDays === 1 ? `${windowSize}-day` : `${windowSize}-point`;

const values = [...raw, ...rolling].filter((v) => v != null);
const yLow = Math.min(...values);
const yHigh = Math.max(...values);
const yPad = (yHigh - yLow) * Y_PAD_SHARE;
const formatDay = (d: Date) => d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
const formatCount = (v: number | null) => (v == null ? "" : v.toLocaleString("en-US"));

const TITLE = "Daily Unique Visitors · line-timeseries-rolling · javascript · muix · anyplot.ai";
const SUBTITLE = `${rows.length} observations · ${formatDay(dates[0])} to ${formatDay(dates[dates.length - 1])} · trailing ${windowLabel} mean from ${formatDay(dates[firstRolling])}`;
const HEADER_H = 80;
const LEGEND_H = 44;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: HEADER_H, padding: "16px 40px 0 112px", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.25 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, marginTop: 6 }}>{SUBTITLE}</div>
      </div>
      <LineChart
        width={width}
        height={height - HEADER_H - LEGEND_H}
        skipAnimation
        grid={{ horizontal: true, vertical: true }}
        margin={{ top: 12, right: 48, bottom: 16, left: 24 }}
        xAxis={[
          {
            data: dates,
            scaleType: "time",
            tickNumber: 10,
            valueFormatter: (v: Date, context) =>
              context.location === "tick" ? v.toLocaleDateString("en-US", { month: "short", day: "numeric" }) : formatDay(v),
            label: DATE,
            height: 64,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: yLow - yPad,
            max: yHigh + yPad,
            tickNumber: 8,
            label: VISITORS,
            width: 84,
            valueFormatter: (v: number) => v.toLocaleString("en-US"),
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          {
            id: "raw",
            data: raw,
            label: `Raw data · ${VISITORS}`,
            color: t.palette[0],
            curve: "linear",
            showMark: false,
            valueFormatter: formatCount,
          },
          {
            id: "rolling",
            data: rolling,
            label: `${ROLLING} (${windowLabel})`,
            color: t.palette[1],
            curve: "monotoneX",
            showMark: false,
            valueFormatter: formatCount,
          },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "end" },
            sx: { fontSize: 16, color: t.ink, columnGap: 3, pr: 5 },
          },
        }}
        sx={{
          '& .MuiLineChart-line[data-series="raw"]': { strokeWidth: 1.75, strokeOpacity: 0.65 },
          '& .MuiLineChart-line[data-series="rolling"]': { strokeWidth: 4 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      />
    </div>
  );
}
