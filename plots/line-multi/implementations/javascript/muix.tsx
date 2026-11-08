// anyplot.ai
// line-multi: Multi-Line Comparison Plot
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 84/100 | Updated: 2026-11-08

import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";

const t = window.ANYPLOT_TOKENS;

// Constants
const X_PAD_SHARE = 0.03; // share of the x range added on both sides so the end markers stay whole
const Y_PAD_SHARE = 0.06; // share of the value range added below and above the data

// Columns: set these to your data's column names
const MONTH = "Month"; // role: x
const CITY = "City"; // role: series
const TEMP = "Average temperature (°C)"; // role: y

// Data: replace this block with your own records, one object per row
// Monthly mean temperatures of four cities in distinct climate zones.
const data = Object.entries({
  Reykjavik: [0, 1, 2, 5, 8, 11, 13, 13, 10, 6, 3, 1],
  Berlin: [1, 2, 6, 11, 16, 19, 21, 21, 16, 11, 6, 2],
  Dubai: [19, 20, 24, 29, 34, 36, 38, 38, 35, 31, 25, 21],
  Singapore: [27, 27, 28, 28, 28, 28, 28, 28, 27, 27, 27, 27],
}).flatMap(([city, temps]) =>
  ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].map((month, i) => ({
    [MONTH]: month,
    [CITY]: city,
    [TEMP]: temps[i],
  })),
);

// Plot: reads only data and the constants above
// Months keep their order of appearance and sit on an index axis, so crossings can fall between them.
const months = [...new Set(data.map((d) => d[MONTH]))];
const cities = [...new Set(data.map((d) => d[CITY]))];
const xs = months.map((_, i) => i);
const lines = cities.map((city, i) => ({
  id: `city-${i}`,
  label: city,
  color: t.palette[i],
  values: months.map((m) => data.find((d) => d[CITY] === city && d[MONTH] === m)?.[TEMP] ?? null),
}));

// Crossovers: every sign change of the gap between two series, at the linearly interpolated position
const crossings: { x: number; label: string }[] = [];
lines.forEach((a, i) =>
  lines.slice(i + 1).forEach((b) => {
    for (let k = 0; k < xs.length - 1; k += 1) {
      const pair = [a.values[k], b.values[k], a.values[k + 1], b.values[k + 1]];
      if (pair.some((v) => v == null)) continue;
      const before = pair[0] - pair[1];
      const after = pair[2] - pair[3];
      if (before * after < 0) crossings.push({ x: k + before / (before - after), label: `${a.label} and ${b.label} cross` });
    }
  }),
);

const temps = data.map((d) => d[TEMP]);
const yLow = Math.min(...temps);
const yHigh = Math.max(...temps);
const yPad = (yHigh - yLow) * Y_PAD_SHARE;
const xPad = (xs.length - 1) * X_PAD_SHARE;
const unit = TEMP.match(/\(([^)]+)\)/)?.[1] ?? "";

const TITLE = "line-multi · javascript · muix · anyplot.ai";
const SUBTITLE = `${cities.length} series × ${months.length} ${MONTH.toLowerCase()}s · range ${yLow} to ${yHigh} ${unit} · ${crossings.length} crossovers`;
const HEADER_H = 80;
const LEGEND_H = 44;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: HEADER_H, padding: "16px 40px 0 104px", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.25 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, marginTop: 6 }}>{SUBTITLE}</div>
      </div>
      <LineChart
        width={width}
        height={height - HEADER_H - LEGEND_H}
        skipAnimation
        grid={{ horizontal: true }}
        margin={{ top: 12, right: 48, bottom: 16, left: 24 }}
        xAxis={[
          {
            data: xs,
            scaleType: "linear",
            min: -xPad,
            max: xs.length - 1 + xPad,
            tickInterval: xs,
            valueFormatter: (v: number) => months[v] ?? "",
            label: MONTH,
            height: 64,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: yLow - yPad,
            max: yHigh + yPad,
            label: TEMP,
            width: 76,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={lines.map((line) => ({
          id: line.id,
          data: line.values,
          label: line.label,
          color: line.color,
          curve: "monotoneX",
          showMark: true,
          labelMarkType: "line+mark",
          valueFormatter: (v: number | null) => (v == null ? "" : `${v} ${unit}`),
        }))}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "end" },
            sx: { fontSize: 16, color: t.ink, columnGap: 3, pr: 5, "& .MuiChartsLegend-mark": { width: 24, height: 24 } },
          },
        }}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiLineChart-mark": { strokeWidth: 2.5 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        {crossings.map((c) => (
          <ChartsReferenceLine
            key={`${c.label}-${c.x}`}
            x={c.x}
            label={c.label}
            labelAlign="start"
            spacing={{ x: 8, y: 8 }}
            labelStyle={{ fontSize: 14, fill: t.inkSoft }}
            lineStyle={{ stroke: t.inkSoft, strokeDasharray: "4 4", strokeWidth: 1.5 }}
          />
        ))}
      </LineChart>
    </div>
  );
}
