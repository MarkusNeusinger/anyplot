// anyplot.ai
// scatter-basic: Basic Scatter Plot
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 83/100 | Updated: 2026-11-08

import { ScatterChart } from "@mui/x-charts/ScatterChart";

const t = window.ANYPLOT_TOKENS;

// Constants
const PAD_SHARE = 0.05; // axis padding on each side as a share of the data span
const POINT_ALPHA = 0.7; // moderate transparency so overlapping points read darker

// Columns: set these to your data's column names
const HOURS = "Weekly study hours (h)"; // role: x
const SCORE = "Final exam score (%)"; // role: y

// Data: replace this block with your own records, one object per row
// 120 university students: self-logged weekly study hours against their final exam score.
const data = (() => {
  let seed = 42;
  const lcg = () => {
    seed = (1664525 * seed + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  const randn = () => Math.sqrt(-2 * Math.log(lcg() + 1e-15)) * Math.cos(2 * Math.PI * lcg());
  return Array.from({ length: 120 }, () => {
    const hours = 2 + lcg() * 36;
    const score = 28 + (hours / 40) * 58 + randn() * 11;
    return {
      [HOURS]: Math.round(hours * 10) / 10,
      [SCORE]: Math.min(98, Math.max(12, Math.round(score * 10) / 10)),
    };
  });
})();

// Plot: reads only data and the constants above
const xs = data.map((d) => d[HOURS]);
const ys = data.map((d) => d[SCORE]);
const xPad = (Math.max(...xs) - Math.min(...xs)) * PAD_SHARE;
const yPad = (Math.max(...ys) - Math.min(...ys)) * PAD_SHARE;

const TITLE = "scatter-basic · javascript · muix · anyplot.ai";
const HEADER_HEIGHT = 64;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          fontWeight: 600,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <ScatterChart
        width={width}
        height={height - HEADER_HEIGHT}
        skipAnimation
        hideLegend
        grid={{ horizontal: true, vertical: true }}
        margin={{ top: 16, right: 48, bottom: 16, left: 24 }}
        series={[
          {
            id: "observations",
            label: SCORE,
            color: t.palette[0],
            markerSize: 7,
            data: data.map((d, i) => ({ id: i, x: d[HOURS], y: d[SCORE] })),
            valueFormatter: (v) => (v ? `${HOURS}: ${v.x} · ${SCORE}: ${v.y}` : ""),
          },
        ]}
        xAxis={[
          {
            min: Math.min(...xs) - xPad,
            max: Math.max(...xs) + xPad,
            label: HOURS,
            tickNumber: 8,
            height: 72,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: Math.min(...ys) - yPad,
            max: Math.max(...ys) + yPad,
            label: SCORE,
            tickNumber: 6,
            width: 76,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        sx={{
          "& .MuiScatterChart-marker": { fillOpacity: POINT_ALPHA },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      />
    </div>
  );
}
