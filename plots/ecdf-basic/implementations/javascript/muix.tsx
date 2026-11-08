// anyplot.ai
// ecdf-basic: Basic ECDF Plot
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 88/100 | Created: 2026-06-25
import { LineChart } from "@mui/x-charts/LineChart";

const t = window.ANYPLOT_TOKENS;

// Constants
const X_PAD = 0.03; // share of the value range added on both sides of the outermost steps
const TITLE = "ecdf-basic · javascript · muix · anyplot.ai";
const HEADER_H = 84;

// Columns: set these to your data's column names
const SCORE = "Exam score (points)"; // role: values

// Data: replace this block with your own records, one object per row
// Final exam scores of 80 students taught with traditional instruction (normal, mean 72, sd 12)
const data = (() => {
  let seed = 42;
  const rand = () => {
    seed = (Math.imul(1664525, seed) + 1013904223) | 0;
    return (seed >>> 0) / 4294967296;
  };
  return Array.from({ length: 80 }, () => {
    const u = Math.max(rand(), 1e-10);
    const z = Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rand());
    return { [SCORE]: Math.round((72 + 12 * z) * 10) / 10 };
  });
})();

// Plot: reads only data and the constants above
const values = data.map((d) => d[SCORE]).filter((v) => Number.isFinite(v)).sort((a, b) => a - b);
const n = values.length;
const lo = values[0];
const hi = values[n - 1];
const pad = (hi - lo) * X_PAD;

// Step function: 0 left of the smallest value, then +1/n at every observation (ties stack)
const xs = [lo - pad, ...values, hi + pad];
const ecdf = [0, ...values.map((_, i) => (i + 1) / n), 1];
const subtitle = `n = ${n} · range ${lo.toFixed(1)} to ${hi.toFixed(1)} · each step adds 1/${n}`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: HEADER_H, padding: "22px 40px 0", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, marginTop: 6 }}>{subtitle}</div>
      </div>
      <LineChart
        width={width}
        height={height - HEADER_H}
        skipAnimation
        hideLegend
        grid={{ horizontal: true, vertical: true }}
        margin={{ top: 20, right: 48, bottom: 16, left: 24 }}
        xAxis={[
          {
            data: xs,
            scaleType: "linear",
            min: lo - pad,
            max: hi + pad,
            label: SCORE,
            height: 68,
            tickNumber: 10,
            valueFormatter: (v) => v.toFixed(0),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 0,
            max: 1,
            label: "Cumulative proportion",
            width: 84,
            tickNumber: 10,
            valueFormatter: (v) => v.toFixed(1),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          {
            id: "ecdf",
            data: ecdf,
            label: "Cumulative proportion",
            color: t.palette[0],
            curve: "stepAfter",
            showMark: false,
          },
        ]}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      />
    </div>
  );
}
