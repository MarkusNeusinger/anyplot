// anyplot.ai
// line-cycle-seasonal: Cycle Plot (Seasonal Subseries)
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08

import { LineChart } from "@mui/x-charts/LineChart";

const t = window.ANYPLOT_TOKENS;

// Constants
const GAP_SLOTS = 3; // distance between the last point of one group and the first of the next, in point slots
const MEAN_OVERHANG = 0.45; // how far a mean line reaches past its group's outer points, in point slots
const X_PAD_SLOTS = 0.8; // empty space left of the first group and right of the last, in point slots
const Y_PAD_SHARE = 0.06; // share of the value range added below and above the data

// Columns: set these to your data's column names
const MONTH = "Month"; // role: season
const YEAR = "Year"; // role: cycle
const SALES = "Online retail sales ($ billion)"; // role: value

// Data: replace this block with your own records, one object per row
// Monthly online retail sales 2014–2023: about 8 % yearly growth on a holiday-peaked season.
const data = (() => {
  let s = 42;
  const rand = () => {
    s = (Math.imul(1664525, s) + 1013904223) | 0;
    return (s >>> 0) / 0x100000000;
  };
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const seasonal = [0.72, 0.75, 0.88, 0.85, 0.87, 0.82, 0.84, 0.87, 0.9, 0.95, 1.1, 1.45];
  const rows = [];
  for (let yi = 0; yi < 10; yi += 1) {
    months.forEach((month, m) => {
      const trend = 3.5 * 1.08 ** yi;
      const noise = (rand() - 0.5) * 0.64; // uniform within ±0.32
      rows.push({ [MONTH]: month, [YEAR]: 2014 + yi, [SALES]: Math.round((trend * seasonal[m] + noise) * 100) / 100 });
    });
  }
  return rows;
})();

// Plot: reads only data and the constants above
// Seasons keep their order of first appearance; each subseries is sorted by cycle.
const seasons = [...new Set(data.map((d) => d[MONTH]))];
const groups = seasons.map((season) => {
  const rows = data.filter((d) => d[MONTH] === season).sort((a, b) => a[YEAR] - b[YEAR]);
  return { season, rows, mean: rows.reduce((s, d) => s + d[SALES], 0) / rows.length };
});

// One shared linear x of point slots: a mean-only point at each group edge, the
// observations in between, and a null break so no line joins neighbouring groups.
const xs: number[] = [];
const subseries: (number | null)[] = [];
const means: (number | null)[] = [];
const tickPositions: number[] = [];
const tickLabels = new Map<number, string>();
const pointLabels = new Map<number, string>();
let cursor = 0;
groups.forEach(({ season, rows, mean }) => {
  const last = cursor + rows.length - 1;
  xs.push(cursor - MEAN_OVERHANG);
  subseries.push(null);
  means.push(mean);
  rows.forEach((d, j) => {
    xs.push(cursor + j);
    subseries.push(d[SALES]);
    means.push(mean);
    pointLabels.set(cursor + j, `${season} ${d[YEAR]}`);
  });
  xs.push(last + MEAN_OVERHANG);
  subseries.push(null);
  means.push(mean);
  xs.push(last + GAP_SLOTS / 2);
  subseries.push(null);
  means.push(null);
  tickPositions.push((cursor + last) / 2);
  tickLabels.set((cursor + last) / 2, season);
  cursor = last + GAP_SLOTS;
});
const xMin = -MEAN_OVERHANG - X_PAD_SLOTS;
const xMax = cursor - GAP_SLOTS + MEAN_OVERHANG + X_PAD_SLOTS;

const values = data.map((d) => d[SALES]);
const yLow = Math.min(...values);
const yHigh = Math.max(...values);
const yPad = (yHigh - yLow) * Y_PAD_SHARE;
const cycles = data.map((d) => d[YEAR]);
const firstCycle = Math.min(...cycles);
const lastCycle = Math.max(...cycles);
const groupMeans = groups.map((g) => g.mean);

const TITLE = "Monthly Retail Sales · line-cycle-seasonal · javascript · muix · anyplot.ai";
const SUBTITLE = `${data.length} observations in ${groups.length} ${MONTH.toLowerCase()} groups · ${YEAR} ${firstCycle}–${lastCycle} · group means ${Math.min(...groupMeans).toFixed(2)} to ${Math.max(...groupMeans).toFixed(2)}`;
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
        margin={{ top: 12, right: 40, bottom: 12, left: 24 }}
        xAxis={[
          {
            data: xs,
            scaleType: "linear",
            min: xMin,
            max: xMax,
            tickInterval: tickPositions,
            valueFormatter: (v: number, ctx: { location: string }) =>
              (ctx.location === "tick" ? tickLabels.get(v) : pointLabels.get(v)) ?? "",
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
            label: SALES,
            width: 84,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          {
            id: "subseries",
            data: subseries,
            label: `Subseries by ${YEAR.toLowerCase()}, ${firstCycle}–${lastCycle}`,
            color: t.palette[0],
            showMark: false,
            connectNulls: false,
            curve: "linear",
          },
          {
            id: "mean",
            data: means,
            label: `Mean per ${MONTH.toLowerCase()}`,
            color: t.palette[1],
            showMark: false,
            connectNulls: false,
            curve: "linear",
            valueFormatter: (v: number | null) => (v == null ? "" : v.toFixed(2)),
          },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "end" },
            sx: { fontSize: 15, color: t.inkSoft, pr: 5 },
          },
        }}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 2.25 },
          '& .MuiLineChart-line[data-series="mean"]': { strokeWidth: 4.5, strokeLinecap: "round" },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      />
    </div>
  );
}
