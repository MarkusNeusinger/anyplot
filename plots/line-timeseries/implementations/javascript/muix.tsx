// anyplot.ai
// line-timeseries: Time Series Line Plot
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08
import { LineChart } from "@mui/x-charts/LineChart";
import { useXScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const DAY_MS = 86_400_000;
const DAY_ROW_MAX_DAYS = 14; // up to this span the ticks show times of day under a row of day labels
const MONTH_DAY_MAX_DAYS = 730; // up to this span the ticks show month and day, beyond it the year
const Y_PAD_SHARE = 0.1; // share of the value range added below and above the line

// Columns: set these to your data's column names
const TIMESTAMP = "Timestamp"; // role: date
const TEMP = "Air temperature (°F)"; // role: value

// Data: replace this block with your own records, one object per row
// Hourly rooftop sensor readings for one week: diurnal cycle, a gentle warm-up and sensor noise.
const data = (() => {
  let seed = 11;
  const rand = () => {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
  const start = new Date(2024, 5, 3, 0, 0).getTime();
  return Array.from({ length: 7 * 24 }, (_, i) => {
    const diurnal = 8 * Math.sin((((i % 24) - 9) / 24) * 2 * Math.PI);
    const warmup = Math.floor(i / 24) * 0.7;
    const noise = (rand() - 0.5) * 2.2;
    return { [TIMESTAMP]: new Date(start + i * 3_600_000), [TEMP]: Math.round((61 + diurnal + warmup + noise) * 10) / 10 };
  });
})();

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[TIMESTAMP] - b[TIMESTAMP]);
const times = rows.map((d) => d[TIMESTAMP]);
const values = rows.map((d) => d[TEMP]);
const tMin = times[0].getTime();
const tMax = times[times.length - 1].getTime();
const spanDays = (tMax - tMin) / DAY_MS;
const unit = TEMP.match(/\(([^)]+)\)/)?.[1] ?? "";

const present = values.filter((v) => v != null);
const yLow = Math.min(...present);
const yHigh = Math.max(...present);
const yPad = (yHigh - yLow) * Y_PAD_SHARE;

// Tick format adapts to the span of the data; a short span adds a row of day labels below the times
const tickFormat =
  spanDays <= DAY_ROW_MAX_DAYS
    ? { hour: "2-digit", minute: "2-digit", hourCycle: "h23" }
    : spanDays <= MONTH_DAY_MAX_DAYS
      ? { month: "short", day: "numeric" }
      : { year: "numeric" };
const days = [];
if (spanDays <= DAY_ROW_MAX_DAYS) {
  const cursor = new Date(tMin);
  cursor.setHours(0, 0, 0, 0);
  while (cursor.getTime() <= tMax) {
    const dayStart = cursor.getTime();
    cursor.setDate(cursor.getDate() + 1);
    days.push({
      start: Math.max(dayStart, tMin),
      end: Math.min(cursor.getTime(), tMax),
      label: new Date(dayStart).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" }),
    });
  }
}
const formatFull = (d: Date) =>
  d.toLocaleString("en-US", { weekday: "short", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
const formatDay = (d: Date) => d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });

const TITLE = "Rooftop Sensor Temperature · line-timeseries · javascript · muix · anyplot.ai";
const SUBTITLE = `${rows.length} readings · ${formatDay(times[0])} to ${formatDay(times[times.length - 1])} · ${yLow} to ${yHigh} ${unit}`;
const HEADER_H = 80;
const X_AXIS_H = days.length > 0 ? 112 : 72;

function DayRow() {
  const xScale = useXScale();
  const { top, height } = useDrawingArea();
  const bottom = top + height;
  return (
    <g>
      {days.map((day) => (
        <g key={day.start}>
          {/* The separator breaks at the tick row so it never crosses the "00:00" labels */}
          {day.start > tMin &&
            [
              [top, bottom],
              [bottom + 34, bottom + 62],
            ].map(([y1, y2]) => (
              <line
                key={y1}
                x1={xScale(new Date(day.start))}
                x2={xScale(new Date(day.start))}
                y1={y1}
                y2={y2}
                stroke={t.inkSoft}
                strokeOpacity={0.5}
                strokeWidth={1}
                strokeDasharray="3 3"
              />
            ))}
          <text
            x={(xScale(new Date(day.start)) + xScale(new Date(day.end))) / 2}
            y={bottom + 54}
            textAnchor="middle"
            fontSize={15}
            fontWeight={600}
            fill={t.ink}
          >
            {day.label}
          </text>
        </g>
      ))}
    </g>
  );
}

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
        height={height - HEADER_H}
        skipAnimation
        hideLegend
        grid={{ horizontal: true, vertical: true }}
        margin={{ top: 16, right: 48, bottom: 12, left: 24 }}
        xAxis={[
          {
            data: times,
            scaleType: "time",
            min: times[0],
            max: times[times.length - 1],
            tickNumber: 14,
            valueFormatter: (v: Date, context) =>
              context.location === "tick" ? v.toLocaleString("en-US", tickFormat) : formatFull(v),
            label: TIMESTAMP,
            height: X_AXIS_H,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: yLow - yPad,
            max: yHigh + yPad,
            label: TEMP,
            width: 84,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          {
            id: "value",
            data: values,
            label: TEMP,
            color: t.palette[0],
            curve: "linear",
            showMark: false,
            valueFormatter: (v: number | null) => (v == null ? "" : `${v.toFixed(1)} ${unit}`),
          },
        ]}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <DayRow />
      </LineChart>
    </div>
  );
}
