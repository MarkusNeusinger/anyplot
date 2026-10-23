// anyplot.ai
// violin-basic: Basic Violin Plot
// Library: muix 9.16.0 | JavaScript 22.23.3
// Quality: 84/100 | Updated: 2026-10-23
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;
const TITLE = "violin-basic · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 56;

// Constants
const GRID_N = 140; // KDE evaluation points per violin
const TAIL_BANDWIDTHS = 1.5; // the density falls below ~4 % of its peak this far past the data

// Columns: set these to your data's column names
const CLASS_GROUP = "Class group"; // role: category
const SCORE = "Exam score (%)"; // role: value

// Data: replace this block with your own records, one object per row
// Exam scores for four class groups, each shaped differently so the density
// carries what a box plot would hide: unimodal, narrow, bimodal, skewed.
let seed = 42;
const rand = () => (seed = (seed * 1664525 + 1013904223) % 4294967296) / 4294967296;
const normal = (mean, sd) => mean + sd * Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-9))) * Math.cos(2 * Math.PI * rand());
const groupShapes = [
  ["Group A", () => normal(74, 8)],
  ["Group B", () => normal(88, 3.5)],
  ["Group C", () => (rand() < 0.45 ? normal(62, 5) : normal(82, 4))],
  ["Group D", () => 90 - 28 * Math.pow(rand(), 2.4) + normal(0, 2)],
];
const data = groupShapes.flatMap(([group, draw]) =>
  Array.from({ length: 220 }, () => {
    let score = draw();
    while (score < 50 || score > 99) score = draw(); // redraw out-of-range scores
    return { [CLASS_GROUP]: group, [SCORE]: Math.round(score * 10) / 10 };
  }),
);

// Plot: reads only data and the constants above
const categories = [...new Set(data.map((d) => d[CLASS_GROUP]))];

// Per group: Tukey box stats and a Gaussian KDE (Silverman bandwidth) normalized
// to its own peak. The grid ends a short way past the data, where the density
// is nearly zero, and the outline closes to a point there, so each violin
// tapers just beyond its data instead of being cut flat.
const violins = categories.map((cat) => {
  const values = data
    .filter((d) => d[CLASS_GROUP] === cat && d[SCORE] != null)
    .map((d) => d[SCORE])
    .sort((a, b) => a - b);
  const n = values.length;
  const quantile = (q) => {
    const pos = (n - 1) * q;
    const base = Math.floor(pos);
    return values[base] + (pos - base) * ((values[base + 1] ?? values[base]) - values[base]);
  };
  const [q1, median, q3] = [0.25, 0.5, 0.75].map(quantile);
  const inliers = values.filter((v) => v >= q1 - 1.5 * (q3 - q1) && v <= q3 + 1.5 * (q3 - q1));

  const mean = values.reduce((a, b) => a + b, 0) / n;
  const sd = Math.sqrt(values.reduce((a, b) => a + (b - mean) ** 2, 0) / (n - 1));
  const bandwidth = 0.9 * sd * Math.pow(n, -0.2);
  const lo = values[0] - TAIL_BANDWIDTHS * bandwidth;
  const hi = values[n - 1] + TAIL_BANDWIDTHS * bandwidth;
  const grid = Array.from({ length: GRID_N }, (_, k) => lo + (k * (hi - lo)) / (GRID_N - 1));
  const raw = grid.map((gy) => values.reduce((sum, v) => sum + Math.exp(-0.5 * ((gy - v) / bandwidth) ** 2), 0));
  const peak = Math.max(...raw);

  return {
    cat,
    q1,
    median,
    q3,
    whiskerLow: inliers[0],
    whiskerHigh: inliers[inliers.length - 1],
    grid,
    density: raw.map((v) => v / peak),
  };
});

const gridMin = Math.min(...violins.map((v) => v.grid[0]));
const gridMax = Math.max(...violins.map((v) => v.grid[GRID_N - 1]));
const yPad = (gridMax - gridMin) * 0.03;

// The community package has no violin component: a custom SVG layer placed
// through the chart's own band/linear scales draws one inside ChartsContainer.
function Violins() {
  const xScale = useXScale();
  const yScale = useYScale();
  const band = xScale.bandwidth();
  const violinHalfWidth = band * 0.44;
  const boxHalfWidth = Math.min(16, band * 0.09);

  return (
    <g>
      {violins.map(({ cat, grid, density, q1, median, q3, whiskerLow, whiskerHigh }, i) => {
        const color = t.palette[i];
        const center = xScale(cat) + band / 2;
        const leftSide = grid.map((gy, k) => `${center - density[k] * violinHalfWidth},${yScale(gy)}`);
        const rightSide = grid.map((gy, k) => `${center + density[k] * violinHalfWidth},${yScale(gy)}`).reverse();
        const bottomTip = `${center},${yScale(grid[0])}`;
        const topTip = `${center},${yScale(grid[GRID_N - 1])}`;
        const violinPath = `M${bottomTip} L${leftSide.join(" L")} L${topTip} L${rightSide.join(" L")} Z`;

        return (
          <g key={cat}>
            <path
              d={violinPath}
              fill={color}
              fillOpacity={0.5}
              stroke={color}
              strokeWidth={1.75}
              strokeLinejoin="round"
            />
            <line x1={center} x2={center} y1={yScale(whiskerLow)} y2={yScale(whiskerHigh)} stroke={t.ink} strokeWidth={1.5} />
            <rect
              x={center - boxHalfWidth}
              y={yScale(q3)}
              width={boxHalfWidth * 2}
              height={Math.max(1, yScale(q1) - yScale(q3))}
              fill={t.ink}
              rx={3}
            />
            <line
              x1={center - boxHalfWidth}
              x2={center + boxHalfWidth}
              y1={yScale(median)}
              y2={yScale(median)}
              stroke={t.pageBg}
              strokeWidth={2.5}
            />
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const chartHeight = window.ANYPLOT_SIZE.height - TITLE_HEIGHT;

  return (
    <div style={{ width: window.ANYPLOT_SIZE.width, height: window.ANYPLOT_SIZE.height }}>
      <div
        style={{
          height: TITLE_HEIGHT,
          lineHeight: `${TITLE_HEIGHT}px`,
          paddingLeft: 24,
          fontSize: 22,
          fontWeight: 500,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <ChartsContainer
        width={window.ANYPLOT_SIZE.width}
        height={chartHeight}
        series={[]}
        skipAnimation
        margin={{ top: 32, right: 50, bottom: 16, left: 24 }}
        xAxis={[
          {
            id: "groups",
            data: categories,
            scaleType: "band",
            height: 76,
            label: CLASS_GROUP,
            labelStyle: { fontSize: 16 },
            tickLabelStyle: { fontSize: 16 },
          },
        ]}
        yAxis={[
          {
            id: "scores",
            min: gridMin - yPad,
            max: gridMax + yPad,
            width: 84,
            label: SCORE,
            labelStyle: { fontSize: 16 },
            tickLabelStyle: { fontSize: 14 },
          },
        ]}
      >
        <ChartsGrid
          horizontal
          sx={{
            "& .MuiChartsGrid-line": {
              stroke: t.grid,
              opacity: 0.2,
            },
          }}
        />
        <Violins />
        <ChartsXAxis axisId="groups" disableTicks />
        <ChartsYAxis axisId="scores" />
      </ChartsContainer>
    </div>
  );
}
