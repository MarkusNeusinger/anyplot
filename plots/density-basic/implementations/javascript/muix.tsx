// anyplot.ai
// density-basic: Basic Density Plot
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 86/100 | Updated: 2026-11-08
import { LineChart } from "@mui/x-charts/LineChart";

const t = window.ANYPLOT_TOKENS;

// Constants
const SILVERMAN = 1.06; // rule-of-thumb factor: bandwidth = 1.06 · sd · n^(-1/5)
const KDE_CUT = 2; // the curve extends this many bandwidths past the smallest and largest observation
const GRID_POINTS = 240;
const TITLE = "density-basic · javascript · muix · anyplot.ai";
const TITLE_H = 76;

// Columns: set these to your data's column names
const FINISH_TIME = "Marathon finish time (minutes)"; // role: values

// Data: replace this block with your own records, one object per row
// 400 finish times of a city marathon, log-normal around a 230-minute median (right-skewed by slower runners)
const data = (() => {
  let state = 42;
  const rand = () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
  return Array.from({ length: 400 }, () => {
    const u1 = Math.max(rand(), 1e-9);
    const u2 = rand();
    const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    return { [FINISH_TIME]: Math.round(Math.exp(Math.log(230) + 0.18 * z) * 10) / 10 };
  });
})();

// Plot: reads only data and the constants above
const values = data.map((d) => d[FINISH_TIME]).filter((v) => Number.isFinite(v));
const n = values.length;
const mean = values.reduce((sum, v) => sum + v, 0) / n;
const sd = Math.sqrt(values.reduce((sum, v) => sum + (v - mean) ** 2, 0) / (n - 1));
const bandwidth = SILVERMAN * sd * n ** (-1 / 5);

// Gaussian kernel density on an even grid; the area under the curve is 1
const gridStart = Math.min(...values) - KDE_CUT * bandwidth;
const gridEnd = Math.max(...values) + KDE_CUT * bandwidth;
const grid = Array.from({ length: GRID_POINTS }, (_, i) => gridStart + ((gridEnd - gridStart) * i) / (GRID_POINTS - 1));
const density = grid.map(
  (x) =>
    values.reduce((sum, v) => sum + Math.exp(-0.5 * ((x - v) / bandwidth) ** 2), 0) /
    (n * bandwidth * Math.sqrt(2 * Math.PI)),
);

const unit = FINISH_TIME.match(/\(([^)]+)\)/)?.[1] ?? "";
const subtitle = `n = ${n} · Gaussian kernel, bandwidth ${bandwidth.toFixed(1)} ${unit} (Silverman's rule)`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, padding: "22px 40px 0", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, marginTop: 6 }}>{subtitle}</div>
      </div>
      <LineChart
        width={width}
        height={height - TITLE_H}
        skipAnimation
        hideLegend
        grid={{ horizontal: true }}
        margin={{ top: 20, right: 48, bottom: 16, left: 24 }}
        xAxis={[
          {
            data: grid,
            scaleType: "linear",
            min: gridStart,
            max: gridEnd,
            label: FINISH_TIME,
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
            label: "Probability density",
            width: 92,
            tickNumber: 6,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          {
            id: "density",
            data: density,
            label: "Probability density",
            color: t.palette[0],
            area: true,
            curve: "monotoneX",
            showMark: false,
          },
        ]}
        sx={{
          "& .MuiLineChart-area": { fillOpacity: 0.3 },
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      />
    </div>
  );
}
