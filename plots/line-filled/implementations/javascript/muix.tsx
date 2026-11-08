// anyplot.ai
// line-filled: Filled Line Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-05
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";

const t = window.ANYPLOT_TOKENS;

// Constants
const BASELINE = 0; // the fill runs down to zero, so the filled height stays proportional to the value
const FILL_TOP_OPACITY = 0.5; // semi-transparent fill, alpha 0.3–0.5, lighter towards the baseline
const FILL_BOTTOM_OPACITY = 0.3;

// Columns: set these to your data's column names
const DATE = "Date"; // role: x
const VISITORS = "Unique visitors"; // role: y

// Data: replace this block with your own records, one object per row
// Daily unique visitors over 60 days of a content-marketing push, with weekend dips.
const data = (() => {
  let seed = 11;
  const rand = () => {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
  const start = new Date(2026, 0, 5);
  return Array.from({ length: 60 }, (_, i) => {
    const date = new Date(start);
    date.setDate(start.getDate() + i);
    const weekendDip = date.getDay() === 0 || date.getDay() === 6 ? 0.7 : 1;
    const noise = 1 + (rand() - 0.5) * 0.16;
    return { [DATE]: date, [VISITORS]: Math.round(3200 * (1 + i * 0.013) * weekendDip * noise) };
  });
})();

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => a[DATE] - b[DATE]);
const dates = rows.map((d) => d[DATE]);
const values = rows.map((d) => d[VISITORS]);
const mean = Math.round(values.reduce((s, v) => s + v, 0) / values.length);
const formatValue = (v: number) => v.toLocaleString("en-US");
const formatDate = (d: Date) => d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });

const TITLE = "Website Traffic Growth · line-filled · javascript · muix · anyplot.ai";
const SUBTITLE = `${values.length} observations · ${formatDate(dates[0])} – ${formatDate(dates[dates.length - 1])} · range ${formatValue(Math.min(...values))} to ${formatValue(Math.max(...values))}`;
const HEADER_H = 80;
const FILL_ID = "lineFilledGradient";

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: HEADER_H, padding: "16px 40px 0 108px", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.25 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, marginTop: 6 }}>{SUBTITLE}</div>
      </div>
      <LineChart
        width={width}
        height={height - HEADER_H}
        skipAnimation
        hideLegend
        margin={{ top: 16, right: 48, bottom: 16, left: 24 }}
        xAxis={[
          {
            data: dates,
            scaleType: "time",
            label: DATE,
            height: 64,
            tickNumber: 9,
            valueFormatter: (d: Date) => d.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: BASELINE,
            label: VISITORS,
            width: 88,
            valueFormatter: formatValue,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          {
            id: "values",
            data: values,
            label: VISITORS,
            color: t.palette[0],
            area: true,
            baseline: BASELINE,
            showMark: false,
            curve: "monotoneX",
            valueFormatter: (v: number | null) => (v == null ? "" : formatValue(v)),
          },
        ]}
        sx={{
          "& .MuiLineChart-area": { fill: `url(#${FILL_ID})` },
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <defs>
          <linearGradient id={FILL_ID} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={t.palette[0]} stopOpacity={FILL_TOP_OPACITY} />
            <stop offset="100%" stopColor={t.palette[0]} stopOpacity={FILL_BOTTOM_OPACITY} />
          </linearGradient>
        </defs>
        {/* Gridlines drawn after the fill so they stay visible through it */}
        <ChartsGrid horizontal />
        <ChartsReferenceLine
          y={mean}
          label={`Mean ${formatValue(mean)}`}
          labelAlign="start"
          spacing={{ x: 12, y: 8 }}
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "6 4", strokeWidth: 1.5 }}
          labelStyle={{ fontSize: 14, fill: t.inkSoft }}
        />
      </LineChart>
    </div>
  );
}
