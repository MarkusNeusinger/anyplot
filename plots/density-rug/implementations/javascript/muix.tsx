// anyplot.ai
// density-rug: Density Plot with Rug Marks
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-02
import { LineChart } from "@mui/x-charts/LineChart";
import { useXScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const SILVERMAN = 0.9; // robust rule of thumb: bandwidth = 0.9 · min(sd, IQR / 1.34) · n^(-1/5)
const KDE_CUT = 2; // the curve extends this many bandwidths past the outermost observations
const GRID_POINTS = 240;
const RUG_LEN = 26; // px, one tick per observation at the foot of the curve
const RUG_OPACITY = 0.7;
const TITLE = "density-rug · javascript · muix · anyplot.ai";
const TITLE_H = 76;

// Columns: set these to your data's column names
const PETAL_LENGTH = "Petal length (cm)"; // role: values

// Data: replace this block with your own records, one object per row
// Petal lengths of 140 wildflowers from two populations surveyed in the same meadow, merged into one sample
const data = (() => {
  let state = 42;
  const rand = () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
  const normal = (mean, sd) => {
    const u1 = Math.max(rand(), 1e-9);
    const u2 = rand();
    return mean + sd * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  };
  return [
    ...Array.from({ length: 75 }, () => normal(4.2, 0.4)),
    ...Array.from({ length: 65 }, () => normal(6.6, 0.5)),
  ].map((v) => ({ [PETAL_LENGTH]: Math.round(v * 100) / 100 }));
})();

// Plot: reads only data and the constants above
const values = data.map((d) => d[PETAL_LENGTH]).filter((v) => Number.isFinite(v));
const sorted = [...values].sort((a, b) => a - b);
const n = values.length;
const mean = values.reduce((sum, v) => sum + v, 0) / n;
const sd = Math.sqrt(values.reduce((sum, v) => sum + (v - mean) ** 2, 0) / (n - 1));
// Linear-interpolated quartiles for the IQR term of the bandwidth rule
const q1Pos = (n - 1) * 0.25;
const q3Pos = (n - 1) * 0.75;
const q1 = sorted[Math.floor(q1Pos)] + (sorted[Math.ceil(q1Pos)] - sorted[Math.floor(q1Pos)]) * (q1Pos % 1);
const q3 = sorted[Math.floor(q3Pos)] + (sorted[Math.ceil(q3Pos)] - sorted[Math.floor(q3Pos)]) * (q3Pos % 1);
const bandwidth = SILVERMAN * Math.min(sd, (q3 - q1) / 1.34) * n ** (-1 / 5);

// Gaussian kernel density on an even grid; the area under the curve is 1
const gridStart = sorted[0] - KDE_CUT * bandwidth;
const gridEnd = sorted[n - 1] + KDE_CUT * bandwidth;
const grid = Array.from({ length: GRID_POINTS }, (_, i) => gridStart + ((gridEnd - gridStart) * i) / (GRID_POINTS - 1));
const density = grid.map(
  (x) =>
    values.reduce((sum, v) => sum + Math.exp(-0.5 * ((x - v) / bandwidth) ** 2), 0) /
    (n * bandwidth * Math.sqrt(2 * Math.PI)),
);

const unit = PETAL_LENGTH.match(/\(([^)]+)\)/)?.[1] ?? "";
const subtitle = `n = ${n} · Gaussian kernel, bandwidth ${bandwidth.toFixed(2)} ${unit} (Silverman's robust rule) · one rug tick per observation`;

function RugMarks() {
  const xScale = useXScale();
  const { top, height } = useDrawingArea();
  const foot = top + height;
  return (
    <g>
      {values.map((v, i) => (
        <line
          key={i}
          x1={xScale(v)}
          x2={xScale(v)}
          y1={foot}
          y2={foot - RUG_LEN}
          stroke={t.palette[0]}
          strokeWidth={2}
          strokeOpacity={RUG_OPACITY}
        />
      ))}
    </g>
  );
}

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
            label: PETAL_LENGTH,
            height: 68,
            tickNumber: 10,
            valueFormatter: (v) => v.toFixed(1),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: 0,
            label: "Probability density",
            width: 84,
            tickNumber: 6,
            valueFormatter: (v) => v.toFixed(2),
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
          "& .MuiLineChart-area": { fillOpacity: 0.2 },
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <RugMarks />
      </LineChart>
    </div>
  );
}
