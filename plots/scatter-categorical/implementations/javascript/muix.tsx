// anyplot.ai
// scatter-categorical: Categorical Scatter Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-05

import { ScatterChart } from "@mui/x-charts/ScatterChart";

const t = window.ANYPLOT_TOKENS;

// Constants
const PAD_SHARE = 0.08; // axis padding on each side as a share of the data span
const POINT_ALPHA = 0.82; // translucent fill plus a page-coloured edge keeps overlapping groups apart

// Columns: set these to your data's column names
const FLIPPER = "Flipper length (mm)"; // role: x
const MASS = "Body mass (kg)"; // role: y
const SPECIES = "Species"; // role: category

// Data: replace this block with your own records, one object per row
// Penguin body measurements: three overlapping but separable species clusters.
const data = (() => {
  let seed = 42;
  const rng = () => {
    seed = (1664525 * seed + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  const randn = () => Math.sqrt(-2 * Math.log(Math.max(rng(), 1e-9))) * Math.cos(2 * Math.PI * rng());
  const species = [
    { name: "Adelie", flipperMean: 190, flipperSd: 6.5, massMean: 3700, massSd: 460, n: 40 },
    { name: "Chinstrap", flipperMean: 196, flipperSd: 7.2, massMean: 3730, massSd: 380, n: 34 },
    { name: "Gentoo", flipperMean: 217, flipperSd: 6.5, massMean: 5090, massSd: 500, n: 38 },
  ];
  return species.flatMap((sp) =>
    Array.from({ length: sp.n }, () => ({
      [FLIPPER]: Math.round(sp.flipperMean + randn() * sp.flipperSd),
      [MASS]: Math.round(sp.massMean + randn() * sp.massSd) / 1000,
      [SPECIES]: sp.name,
    })),
  );
})();

// Plot: reads only data and the constants above
const groups = [...new Set(data.map((d) => d[SPECIES]))];
const xs = data.map((d) => d[FLIPPER]);
const ys = data.map((d) => d[MASS]);
const xPad = (Math.max(...xs) - Math.min(...xs)) * PAD_SHARE;
const yPad = (Math.max(...ys) - Math.min(...ys)) * PAD_SHARE;

const TITLE = "scatter-categorical · javascript · muix · anyplot.ai";
const HEADER_HEIGHT = 64;
const LEGEND_WIDTH = 170;

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
        width={width - LEGEND_WIDTH}
        height={height - HEADER_HEIGHT}
        skipAnimation
        grid={{ vertical: true, horizontal: true }}
        margin={{ top: 16, right: 32, bottom: 16, left: 24 }}
        series={groups.map((group, i) => ({
          id: `species-${i}`,
          label: group,
          color: t.palette[i],
          markerSize: 7,
          highlightScope: { highlight: "series", fade: "global" },
          data: data
            .map((d, j) => ({ id: j, x: d[FLIPPER], y: d[MASS], group: d[SPECIES] }))
            .filter((p) => p.group === group),
        }))}
        xAxis={[
          {
            min: Math.min(...xs) - xPad,
            max: Math.max(...xs) + xPad,
            label: FLIPPER,
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
            label: MASS,
            tickNumber: 6,
            width: 72,
            valueFormatter: (v: number) => v.toFixed(1),
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        slotProps={{
          legend: {
            direction: "vertical",
            position: { vertical: "middle", horizontal: "end" },
            sx: { fontSize: 16, color: t.ink, gap: 2, pl: 3 },
          },
        }}
        sx={{
          "& .MuiScatterChart-marker": { stroke: t.pageBg, strokeWidth: 1.5, fillOpacity: POINT_ALPHA },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      />
    </div>
  );
}
