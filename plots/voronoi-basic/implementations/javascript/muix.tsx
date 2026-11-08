// anyplot.ai
// voronoi-basic: Voronoi Diagram for Spatial Partitioning
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 85/100 | Updated: 2026-11-08
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const BOX_PAD = 0.125; // share of the seed extent added on each side of the clipping box
const CELL_OPACITY = 0.62; // cell fill opacity, so the page shows through as a soft tint
const SEED_R = 7; // seed marker radius, px
// Imprint hues the cells may take, in canonical order; the matte red slot (4)
// stays out because the style guide reserves it for bad or loss roles.
const FILL_SLOTS = [0, 1, 2, 3, 5, 6, 7];
const TITLE = "voronoi-basic · javascript · muix · anyplot.ai";
const TITLE_H = 80;
const X_AXIS_H = 72;
const Y_AXIS_W = 80;
const MARGIN = { top: 16, bottom: 16, left: 32 };

// Columns: set these to your data's column names
const X = "X coordinate (km)"; // role: x
const Y = "Y coordinate (km)"; // role: y

// Data: replace this block with your own records, one object per row
// Eighteen retail store locations scattered across a city grid.
const data = (() => {
  let seed = 42;
  const rand = () => {
    seed = (seed * 1103515245 + 12345) % 2147483648;
    return seed / 2147483648;
  };
  return Array.from({ length: 18 }, () => ({
    [X]: Math.round((10 + rand() * 80) * 100) / 100,
    [Y]: Math.round((10 + rand() * 80) * 100) / 100,
  }));
})();

// Plot: reads only data and the constants above
const sites = data.filter((d) => d[X] != null && d[Y] != null).map((d) => [d[X], d[Y]]);
const xs = sites.map((s) => s[0]);
const ys = sites.map((s) => s[1]);
// A square box in data units, centred on the seeds, so with a square drawing
// area one km spans the same number of pixels on both axes.
const span = Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)) * (1 + 2 * BOX_PAD);
const xLo = (Math.min(...xs) + Math.max(...xs) - span) / 2;
const yLo = (Math.min(...ys) + Math.max(...ys) - span) / 2;
const box = [
  [xLo, yLo],
  [xLo + span, yLo],
  [xLo + span, yLo + span],
  [xLo, yLo + span],
];

// Each cell starts as the box and is clipped (Sutherland-Hodgman) by the
// bisector half-plane towards every other seed: what is left is the region
// closer to its own seed than to any other.
const cells = sites.map(([sx, sy], i) => {
  let polygon = box;
  sites.forEach(([ox, oy], j) => {
    if (j === i || polygon.length === 0) return;
    const mx = (sx + ox) / 2;
    const my = (sy + oy) / 2;
    const side = polygon.map(([px, py]) => (px - mx) * (ox - sx) + (py - my) * (oy - sy));
    const next = [];
    polygon.forEach((curr, k) => {
      const p = (k - 1 + polygon.length) % polygon.length;
      const prev = polygon[p];
      if ((side[k] <= 0) !== (side[p] <= 0)) {
        const r = side[p] / (side[p] - side[k]);
        next.push([prev[0] + r * (curr[0] - prev[0]), prev[1] + r * (curr[1] - prev[1])]);
      }
      if (side[k] <= 0) next.push(curr);
    });
    polygon = next;
  });
  return polygon;
});

// Two cells share an edge when two vertices of one lie on the bisector of
// their seeds. Each cell, in data order, takes the first fill slot that no
// neighbour already holds, so adjacent cells always differ in color.
const tolerance = span * 1e-6;
const adjacent = cells.map((polygon, i) =>
  sites.map(
    (other, j) =>
      j !== i &&
      polygon.filter(
        ([px, py]) =>
          Math.abs(Math.hypot(px - sites[i][0], py - sites[i][1]) - Math.hypot(px - other[0], py - other[1])) < tolerance,
      ).length >= 2,
  ),
);
const colorIndex = [];
cells.forEach((_, i) => {
  const taken = new Set(colorIndex.filter((_, j) => adjacent[i][j]));
  let k = 0;
  while (taken.has(k)) k += 1;
  colorIndex.push(k);
});
const SUBTITLE = `${sites.length} seed points · cells clipped at a box ${BOX_PAD * 100} % beyond the outermost seeds · neighbouring cells differ in color`;

// The community package has no Voronoi component: a custom layer draws the
// cells and seeds through the chart's linear scales.
function VoronoiLayer() {
  const xScale = useXScale();
  const yScale = useYScale();

  return (
    <g>
      {cells.map((polygon, i) =>
        polygon.length < 3 ? null : (
          <polygon
            key={`cell-${i}`}
            points={polygon.map(([px, py]) => `${xScale(px)},${yScale(py)}`).join(" ")}
            fill={t.palette[FILL_SLOTS[colorIndex[i]]]}
            fillOpacity={CELL_OPACITY}
            stroke={t.pageBg}
            strokeWidth={3}
            strokeLinejoin="round"
          />
        ),
      )}
      {sites.map(([sx, sy], i) => (
        <circle key={`seed-${i}`} cx={xScale(sx)} cy={yScale(sy)} r={SEED_R} fill={t.ink} stroke={t.pageBg} strokeWidth={2.5} />
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  // Square drawing area: the right margin absorbs what the plot side leaves over.
  const side = height - TITLE_H - MARGIN.top - MARGIN.bottom - X_AXIS_H;
  const right = width - side - MARGIN.left - Y_AXIS_W;

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, padding: "18px 36px 0", boxSizing: "border-box", textAlign: "center" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2, marginTop: 8 }}>{SUBTITLE}</div>
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_H}
        series={[]}
        skipAnimation
        margin={{ ...MARGIN, right }}
        xAxis={[
          {
            id: "x",
            scaleType: "linear",
            min: xLo,
            max: xLo + span,
            height: X_AXIS_H,
            label: X,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "y",
            scaleType: "linear",
            min: yLo,
            max: yLo + span,
            width: Y_AXIS_W,
            label: Y,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        <VoronoiLayer />
        <ChartsXAxis axisId="x" />
        <ChartsYAxis axisId="y" />
      </ChartsContainer>
    </div>
  );
}
