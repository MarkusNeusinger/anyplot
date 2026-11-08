// anyplot.ai
// andrews-curves: Andrews Curves for Multivariate Data
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-09-02
import { LineChart } from "@mui/x-charts/LineChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "andrews-curves · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const LEGEND_H = 44;
const T_MIN = -Math.PI; // the Fourier parameter covers one full period
const T_MAX = Math.PI;
const T_COUNT = 121; // samples along t, dense enough that no corners show
const T_TICKS = [-Math.PI, -Math.PI / 2, 0, Math.PI / 2, Math.PI];
const T_TICK_LABELS = ["−π", "−π/2", "0", "π/2", "π"];
const X_LABEL = "Fourier parameter t";
const Y_LABEL = "Andrews function f(t)";
const CURVE_OPACITY = 0.4; // single observations stay translucent so bundles read darker

// Columns: set these to your data's column names
const SPECIES = "Species"; // role: category
const VARIABLES = [
  "Sepal length (cm)",
  "Sepal width (cm)",
  "Petal length (cm)",
  "Petal width (cm)",
]; // role: variable

// Data: replace this block with your own records, one object per row
// Iris-like flower measurements, 20 per species: means and spreads follow the
// classic Iris species, drawn with a fixed-seed LCG (the browser has no seeded RNG)
const data = [
  { name: "Setosa", seed: 11, means: [5.0, 3.4, 1.5, 0.25], spreads: [0.35, 0.38, 0.17, 0.11] },
  { name: "Versicolor", seed: 23, means: [5.9, 2.8, 4.3, 1.33], spreads: [0.52, 0.31, 0.47, 0.2] },
  { name: "Virginica", seed: 37, means: [6.6, 3.0, 5.55, 2.03], spreads: [0.64, 0.32, 0.55, 0.27] },
].flatMap(({ name, seed, means, spreads }) => {
  let state = seed;
  const rand = () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
  return Array.from({ length: 20 }, () => ({
    [SPECIES]: name,
    ...Object.fromEntries(
      VARIABLES.map((col, j) => {
        const u1 = Math.max(rand(), 1e-9);
        const u2 = rand();
        const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
        return [col, Number((means[j] + z * spreads[j]).toFixed(2))];
      }),
    ),
  }));
});

// Plot: reads only data and the constants above
const speciesList = [...new Set(data.map((d) => d[SPECIES]))];

// z-score every variable over the whole table so no single measurement dominates
const varMeans = VARIABLES.map((col) => data.reduce((s, d) => s + d[col], 0) / data.length);
const varSds = VARIABLES.map((col, j) =>
  Math.sqrt(data.reduce((s, d) => s + (d[col] - varMeans[j]) ** 2, 0) / (data.length - 1)),
);

// f(t) = x1/√2 + x2·sin(t) + x3·cos(t) + x4·sin(2t) + x5·cos(2t) + …
const tGrid = Array.from({ length: T_COUNT }, (_, k) => T_MIN + (k * (T_MAX - T_MIN)) / (T_COUNT - 1));
const curves = data.map((d) =>
  tGrid.map((tv) =>
    VARIABLES.reduce((sum, col, j) => {
      const z = (d[col] - varMeans[j]) / (varSds[j] || 1);
      const harmonic = Math.ceil(j / 2);
      const basis = j === 0 ? Math.SQRT1_2 : j % 2 === 1 ? Math.sin(harmonic * tv) : Math.cos(harmonic * tv);
      return sum + z * basis;
    }, 0),
  ),
);

// Pointwise mean curve per species, drawn bold on top of its translucent bundle
const meanCurves = speciesList.map((sp) => {
  const members = curves.filter((_, i) => data[i][SPECIES] === sp);
  return tGrid.map((_, k) => members.reduce((s, c) => s + c[k], 0) / members.length);
});

const SUBTITLE = `${data.length} observations · ${VARIABLES.length} variables, z-scored · bold line: mean curve per ${SPECIES.toLowerCase()}`;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: TITLE_H, px: "40px", pt: "18px", boxSizing: "border-box" }}>
        <Typography sx={{ color: t.ink, fontSize: "22px", fontWeight: 600, lineHeight: 1.2 }}>
          {TITLE}
        </Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: "15px", lineHeight: 1.2, mt: "8px" }}>
          {SUBTITLE}
        </Typography>
      </Box>
      <LineChart
        width={width}
        height={height - TITLE_H - LEGEND_H}
        skipAnimation
        grid={{ horizontal: true }}
        axisHighlight={{ x: "line", y: "none" }}
        xAxis={[
          {
            data: tGrid,
            scaleType: "linear",
            min: T_MIN,
            max: T_MAX,
            tickInterval: T_TICKS,
            valueFormatter: (v: number, ctx: { location: string }) =>
              ctx.location === "tick" ? T_TICK_LABELS[T_TICKS.indexOf(v)] : `t = ${v.toFixed(2)}`,
            label: X_LABEL,
            height: 64,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            label: Y_LABEL,
            width: 76,
            valueFormatter: (v: number) => v.toFixed(1),
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={[
          ...data.map((d, i) => ({
            id: `obs-${i}`,
            data: curves[i],
            color: t.palette[speciesList.indexOf(d[SPECIES])],
            curve: "natural" as const,
            showMark: false,
          })),
          ...speciesList.map((sp, g) => ({
            id: `mean-${g}`,
            data: meanCurves[g],
            color: t.palette[g],
            label: sp,
            curve: "natural" as const,
            showMark: false,
          })),
        ]}
        margin={{ top: 12, right: 40, bottom: 8, left: 24 }}
        slotProps={{
          legend: {
            position: { vertical: "bottom", horizontal: "center" },
            sx: { fontSize: 15, color: t.ink },
          },
        }}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 1.75 },
          '& .MuiLineChart-line[data-series^="obs-"]': { strokeOpacity: CURVE_OPACITY },
          '& .MuiLineChart-line[data-series^="mean-"]': { strokeWidth: 3.5 },
          "& .MuiChartsAxisHighlight-root": { stroke: t.inkSoft, strokeDasharray: "4 3" },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      />
    </Box>
  );
}
