// anyplot.ai
// swarm-basic: Basic Swarm Plot
// Library: muix 9.17.0 | JavaScript 22.23.1
// Quality: 90/100 | Created: 2026-07-26
import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const PAD_SHARE = 0.06; // room above and below the outermost scores
const SLOT_PAD = 0.5; // half a category slot of room beside the outer swarms
const MARKER_R = 8; // point radius (px)
const MARKER_GAP = 1.5; // clear space between two neighbouring points (px)
const MEDIAN_HALF = 0.3; // half-width of the median marker as a share of a category slot
const HEADER_H = 78;
const MARGIN = { top: 16, right: 40, bottom: 16, left: 24 };
const X_AXIS_H = 64;
const Y_AXIS_W = 80;

// Columns: set these to your data's column names
const DEPARTMENT = "Department"; // role: category
const SCORE = "Performance score"; // role: value

// Data: replace this block with your own records, one object per row
// Quarterly performance review scores of 40 employees in each of four departments
const data = (() => {
  let seed = 42;
  const uniform = () => {
    seed = (seed * 1664525 + 1013904223) % 4294967296;
    return seed / 4294967296;
  };
  const departments = [
    { name: "Engineering", mean: 78, sd: 8 },
    { name: "Sales", mean: 70, sd: 12 },
    { name: "Marketing", mean: 74, sd: 9 },
    { name: "Support", mean: 83, sd: 6 },
  ];
  return departments.flatMap((dep) =>
    Array.from({ length: 40 }, () => {
      const u1 = Math.max(uniform(), 1e-9);
      const u2 = uniform();
      const normal = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
      return { [DEPARTMENT]: dep.name, [SCORE]: Number(Math.min(99, Math.max(45, dep.mean + normal * dep.sd)).toFixed(1)) };
    }),
  );
})();

// Plot: reads only data and the constants above
const rows = data.filter((d) => Number.isFinite(d[SCORE]));
const categories = [...new Set(rows.map((d) => d[DEPARTMENT]))];
const scoreMin = Math.min(...rows.map((d) => d[SCORE]));
const scoreMax = Math.max(...rows.map((d) => d[SCORE]));
const yLo = scoreMin - (scoreMax - scoreMin) * PAD_SHARE;
const yHi = scoreMax + (scoreMax - scoreMin) * PAD_SHARE;

// Beeswarm layout in screen px: each point keeps its score and moves sideways only
// to the offset nearest the category centre that clears every point placed before it
const { width: W, height: H } = window.ANYPLOT_SIZE;
const plotW = W - MARGIN.left - MARGIN.right - Y_AXIS_W;
const plotH = H - HEADER_H - MARGIN.top - MARGIN.bottom - X_AXIS_H;
const pxPerScore = plotH / (yHi - yLo);
const pxPerSlot = plotW / (categories.length - 1 + 2 * SLOT_PAD);
const clearance = 2 * MARKER_R + MARKER_GAP;
const swarm = categories.flatMap((category, ci) => {
  const placed: { v: number; off: number }[] = [];
  rows
    .filter((d) => d[DEPARTMENT] === category)
    .map((d) => d[SCORE])
    .sort((a, b) => a - b)
    .forEach((v) => {
      const blocked = placed
        .filter((p) => Math.abs(v - p.v) * pxPerScore < clearance)
        .map((p) => {
          const half = Math.sqrt(clearance ** 2 - ((v - p.v) * pxPerScore) ** 2);
          return [p.off - half, p.off + half];
        });
      const candidates = [0, ...blocked.flat()].sort((a, b) => Math.abs(a) - Math.abs(b));
      const off = candidates.find((c) => blocked.every(([lo, hi]) => c <= lo + 1e-6 || c >= hi - 1e-6)) ?? 0;
      placed.push({ v, off });
    });
  return placed.map((p, j) => ({ id: `${ci}-${j}`, x: ci + p.off / pxPerSlot, y: p.v }));
});

// Median score per category, drawn as a short bar across its swarm
const medians = categories.map((category) => {
  const sorted = rows
    .filter((d) => d[DEPARTMENT] === category)
    .map((d) => d[SCORE])
    .sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid];
});

const TITLE = "swarm-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${rows.length} scores across ${categories.length} ${DEPARTMENT.toLowerCase()}s · bar = median`;

function MedianLayer() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {medians.map((m, i) => (
        <line
          key={categories[i]}
          x1={xScale(i - MEDIAN_HALF)}
          x2={xScale(i + MEDIAN_HALF)}
          y1={yScale(m)}
          y2={yScale(m)}
          stroke={t.inkSoft}
          strokeWidth={3}
          strokeLinecap="round"
        />
      ))}
    </g>
  );
}

export default function Chart() {
  return (
    <Box sx={{ width: W, height: H, bgcolor: t.pageBg, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <Box sx={{ height: HEADER_H, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "6px", pt: "8px" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2 }}>{SUBTITLE}</Typography>
      </Box>
      <ScatterChart
        width={W}
        height={H - HEADER_H}
        skipAnimation
        hideLegend
        grid={{ horizontal: true }}
        margin={MARGIN}
        series={[{ id: "scores", label: SCORE, data: swarm, color: t.palette[0], markerSize: MARKER_R }]}
        xAxis={[
          {
            min: -SLOT_PAD,
            max: categories.length - 1 + SLOT_PAD,
            tickInterval: categories.map((_, i) => i),
            valueFormatter: (v: number) => categories[Math.round(v)] ?? "",
            disableTicks: true,
            label: DEPARTMENT,
            height: X_AXIS_H,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: yLo,
            max: yHi,
            label: SCORE,
            width: Y_AXIS_W,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <MedianLayer />
      </ScatterChart>
    </Box>
  );
}
