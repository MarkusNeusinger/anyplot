// anyplot.ai
// scatter-matrix: Scatter Plot Matrix
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08
//# anyplot-orientation: square
import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { BarChart } from "@mui/x-charts/BarChart";

const t = window.ANYPLOT_TOKENS;
// The muted anchor (other / all-groups role) for the diagonal distributions
const MUTED = window.ANYPLOT_THEME === "dark" ? "#A8A79F" : "#6B6A63";

// Constants
const HIST_BINS = 12; // histogram bins per diagonal cell, spanning the variable's padded domain
const EXTENT_PAD_SHARE = 0.08; // room beyond each variable's extreme values, as a share of its span
const EDGE_TICK_COUNT = 4; // about this many tick labels per edge axis, so neighbouring cells stay apart
const POINT_OPACITY = 0.7;
const HISTOGRAM_OPACITY = 0.5; // diagonal distributions stay quieter than the scatter cells

// Columns: set these to your data's column names
const VARIABLES = ["Sepal length (cm)", "Sepal width (cm)", "Petal length (cm)", "Petal width (cm)"]; // role: variables
const SPECIES = "Species"; // role: extra

// Data: replace this block with your own records, one object per row
// Iris-shaped measurements: four flower dimensions for three species, drawn from
// each species' approximate summary statistics, with petal width tracking petal
// length within each species.
const data = (() => {
  let state = 20260909;
  const uniform = () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
  const normal = (mean, std) =>
    mean + std * Math.sqrt(-2 * Math.log(Math.max(uniform(), 1e-9))) * Math.cos(2 * Math.PI * uniform());
  const [sepalLength, sepalWidth, petalLength, petalWidth] = VARIABLES;
  const species = [
    { name: "Setosa", sl: [5.0, 0.35], sw: [3.42, 0.38], pl: [1.46, 0.17], pw: [0.24, 0.15, 0.08] },
    { name: "Versicolor", sl: [5.94, 0.52], sw: [2.77, 0.31], pl: [4.26, 0.47], pw: [1.33, 0.36, 0.14] },
    { name: "Virginica", sl: [6.59, 0.64], sw: [2.97, 0.32], pl: [5.55, 0.55], pw: [2.03, 0.28, 0.16] },
  ];
  return species.flatMap((s) =>
    Array.from({ length: 50 }, () => {
      const sl = normal(...s.sl);
      const sw = normal(...s.sw);
      const pl = Math.max(0.1, normal(...s.pl));
      const pw = Math.max(0.05, s.pw[0] + s.pw[1] * (pl - s.pl[0]) + normal(0, s.pw[2]));
      return {
        [SPECIES]: s.name,
        [sepalLength]: Number(sl.toFixed(2)),
        [sepalWidth]: Number(sw.toFixed(2)),
        [petalLength]: Number(pl.toFixed(2)),
        [petalWidth]: Number(pw.toFixed(2)),
      };
    }),
  );
})();

// Plot: reads only data and the constants above
const groups = [...new Set(data.map((d) => d[SPECIES]))];
const groupRows = groups.map((g) => data.filter((d) => d[SPECIES] === g));
const nVars = VARIABLES.length;

// One padded domain per variable, shared by its whole row and column, and its diagonal histogram
const domains = VARIABLES.map((v) => {
  const values = data.map((d) => d[v]);
  const pad = (Math.max(...values) - Math.min(...values)) * EXTENT_PAD_SHARE;
  return [Math.min(...values) - pad, Math.max(...values) + pad];
});
const histograms = VARIABLES.map((v, k) => {
  const [lo, hi] = domains[k];
  const binWidth = (hi - lo) / HIST_BINS;
  const counts = new Array(HIST_BINS).fill(0);
  data.forEach((d) => {
    counts[Math.min(HIST_BINS - 1, Math.floor((d[v] - lo) / binWidth))] += 1;
  });
  return { counts, bins: counts.map((_, i) => (lo + (i + 0.5) * binWidth).toFixed(2)) };
});

// Focal pair: the two variables with the strongest linear correlation, outlined in both triangles
const pairs = VARIABLES.flatMap((a, i) =>
  VARIABLES.slice(i + 1).map((b, k) => {
    const j = i + 1 + k;
    const ma = data.reduce((s, d) => s + d[a], 0) / data.length;
    const mb = data.reduce((s, d) => s + d[b], 0) / data.length;
    const cov = data.reduce((s, d) => s + (d[a] - ma) * (d[b] - mb), 0);
    const sa = Math.sqrt(data.reduce((s, d) => s + (d[a] - ma) ** 2, 0));
    const sb = Math.sqrt(data.reduce((s, d) => s + (d[b] - mb) ** 2, 0));
    return { i, j, r: cov / (sa * sb) };
  }),
);
const strongest = pairs.reduce((best, p) => (Math.abs(p.r) > Math.abs(best.r) ? p : best));

// Layout: every cell has the same drawing area; the left column and the bottom row
// are widened by their axis band, so ranges line up across each row and column
const TITLE = "scatter-matrix · javascript · muix · anyplot.ai";
const SUBTITLE = `n = ${data.length} · outlined: strongest correlation, r = ${strongest.r.toFixed(2)} (${VARIABLES[strongest.i]} × ${VARIABLES[strongest.j]})`;
const HEADER_HEIGHT = 112;
const GAP = 10;
const CELL_MARGIN = 6;
const cellMargin = { top: CELL_MARGIN, right: CELL_MARGIN, bottom: CELL_MARGIN, left: CELL_MARGIN };
const Y_BAND = 76;
const X_BAND = 64;
const { width, height } = window.ANYPLOT_SIZE;
const cell = Math.floor(
  Math.min(
    width - 32 - Y_BAND - (nVars - 1) * GAP,
    height - HEADER_HEIGHT - 16 - X_BAND - (nVars - 1) * GAP,
  ) / nVars,
);
const edgeAxisStyle = {
  tickNumber: EDGE_TICK_COUNT,
  tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
  labelStyle: { fontSize: 16, fill: t.ink },
};
const chartSx = {
  "& .MuiChartsAxis-line": { stroke: t.inkSoft },
  "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
  "& .MuiScatterChart-marker": { fillOpacity: POINT_OPACITY },
  "& .MuiBarChart-element": { fillOpacity: HISTOGRAM_OPACITY, stroke: t.pageBg, strokeWidth: 1 },
};

export default function Chart() {
  const cells = [];
  for (let row = 0; row < nVars; row += 1) {
    for (let col = 0; col < nVars; col += 1) {
      const leftEdge = col === 0;
      const bottomEdge = row === nVars - 1;
      const focal =
        (row === strongest.i && col === strongest.j) || (row === strongest.j && col === strongest.i);
      const cellWidth = cell + (leftEdge ? Y_BAND : 0);
      const cellHeight = cell + (bottomEdge ? X_BAND : 0);
      // Edge axes carry the row's and the column's variable; inner cells hide theirs
      const xEdge = bottomEdge
        ? { position: "bottom", height: X_BAND, label: VARIABLES[col], ...edgeAxisStyle }
        : { position: "none" };
      const yEdge = leftEdge
        ? { position: "left", width: Y_BAND, label: VARIABLES[row], ...edgeAxisStyle }
        : { position: "none" };

      const chart =
        row === col ? (
          <BarChart
            width={cellWidth}
            height={cellHeight}
            margin={cellMargin}
            skipAnimation
            hideLegend
            xAxis={[
              { id: "bins", scaleType: "band", data: histograms[col].bins, categoryGapRatio: 0, position: "none" },
              { id: "edge-x", scaleType: "linear", min: domains[col][0], max: domains[col][1], ...xEdge },
            ]}
            yAxis={[
              { id: "counts", min: 0, position: "none" },
              { id: "edge-y", scaleType: "linear", min: domains[row][0], max: domains[row][1], ...yEdge },
            ]}
            series={[
              { id: "counts", data: histograms[col].counts, color: MUTED, xAxisId: "bins", yAxisId: "counts" },
            ]}
            sx={chartSx}
          />
        ) : (
          <ScatterChart
            width={cellWidth}
            height={cellHeight}
            margin={cellMargin}
            skipAnimation
            hideLegend
            xAxis={[{ id: "x", min: domains[col][0], max: domains[col][1], ...xEdge }]}
            yAxis={[{ id: "y", min: domains[row][0], max: domains[row][1], ...yEdge }]}
            series={groups.map((g, i) => ({
              id: `group-${i}`,
              label: g,
              color: t.palette[i],
              markerSize: focal ? 4 : 3,
              data: groupRows[i].map((d, k) => ({ id: `${i}-${k}`, x: d[VARIABLES[col]], y: d[VARIABLES[row]] })),
            }))}
            sx={chartSx}
          />
        );

      cells.push(
        <div key={`${row}-${col}`} style={{ position: "relative", width: cellWidth, height: cellHeight }}>
          <div
            style={{
              position: "absolute",
              left: (leftEdge ? Y_BAND : 0) + CELL_MARGIN - 3,
              top: CELL_MARGIN - 3,
              width: cell - 2 * CELL_MARGIN + 6,
              height: cell - 2 * CELL_MARGIN + 6,
              border: focal ? `2px solid ${t.inkSoft}` : `1px solid ${t.grid}`,
              boxSizing: "border-box",
              pointerEvents: "none",
            }}
          />
          {chart}
        </div>,
      );
    }
  }

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <div
        style={{
          height: HEADER_HEIGHT,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
        <div style={{ display: "flex", gap: 24, fontSize: 16, color: t.ink }}>
          {groups.map((g, i) => (
            <span key={g} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ width: 13, height: 13, borderRadius: "50%", background: t.palette[i] }} />
              {g}
            </span>
          ))}
        </div>
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: `${cell + Y_BAND}px repeat(${nVars - 1}, ${cell}px)`,
          gridTemplateRows: `repeat(${nVars - 1}, ${cell}px) ${cell + X_BAND}px`,
          gap: GAP,
        }}
      >
        {cells}
      </div>
    </div>
  );
}
