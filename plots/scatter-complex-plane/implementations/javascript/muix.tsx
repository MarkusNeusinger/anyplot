// anyplot.ai
// scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-08-26
//# anyplot-orientation: square

import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const UNIT_RADIUS = 1; // the unit circle |z| = 1
const LABEL_ROOM_SHARE = 0.4; // room beyond the outermost point for its annotation, as a share of its modulus
const TICK_TARGET = 3; // about this many ticks on each half-axis
const NICE_STEPS = [1, 2, 2.5, 5, 10]; // tick steps per power of ten
const LABEL_GAP = 22; // px between a point and its annotation
const LABEL_DIRECTIONS = 8; // candidate positions around each point on each ring
const LABEL_RINGS = [1, 2, 3]; // candidate distances as multiples of LABEL_GAP
const LABEL_CLEARANCE = 8; // px of room that counts as clear; the nearest clear ring wins
const AXIS_BAND = 28; // px beside each axis line taken by its tick labels
const MARKER_RADIUS = 9; // px

// Columns: set these to your data's column names
const LABEL = "Label"; // role: label
const REAL = "Real part"; // role: real
const IMAGINARY = "Imaginary part"; // role: imaginary
const GROUP = "Group"; // role: extra

// Data: replace this block with your own records, one object per row
// The three cube roots of unity (solutions of z³ = 1) beside three arbitrary complex numbers.
const data = [
  { [LABEL]: "z1", [REAL]: 1, [IMAGINARY]: 0, [GROUP]: "Cube roots of unity" },
  { [LABEL]: "z2", [REAL]: -0.5, [IMAGINARY]: Math.sqrt(3) / 2, [GROUP]: "Cube roots of unity" },
  { [LABEL]: "z3", [REAL]: -0.5, [IMAGINARY]: -Math.sqrt(3) / 2, [GROUP]: "Cube roots of unity" },
  { [LABEL]: "w1", [REAL]: 1.7, [IMAGINARY]: 1.0, [GROUP]: "Arbitrary points" },
  { [LABEL]: "w2", [REAL]: -1.4, [IMAGINARY]: 1.8, [GROUP]: "Arbitrary points" },
  { [LABEL]: "w3", [REAL]: 0.9, [IMAGINARY]: -1.9, [GROUP]: "Arbitrary points" },
];

// Plot: reads only data and the constants above
const groups = [...new Set(data.map((d) => d[GROUP]))];
const groupColor = Object.fromEntries(groups.map((g, i) => [g, t.palette[i]]));

// One symmetric extent on both axes keeps px per unit equal, so the unit circle stays round
const reach = Math.max(UNIT_RADIUS, ...data.map((d) => Math.max(Math.abs(d[REAL]), Math.abs(d[IMAGINARY]))));
const extent = reach * (1 + LABEL_ROOM_SHARE);
const rawStep = reach / TICK_TARGET;
const magnitude = 10 ** Math.floor(Math.log10(rawStep));
const tickStep = (NICE_STEPS.find((s) => s * magnitude >= rawStep) ?? 10) * magnitude;
const ticks = Array.from(
  { length: 2 * Math.floor(extent / tickStep) + 1 },
  (_, k) => Number(((k - Math.floor(extent / tickStep)) * tickStep).toFixed(6)),
);
const offAxisTicks = ticks.filter((v) => v !== 0);

const points = data.map((d) => {
  const re = d[REAL];
  const im = d[IMAGINARY];
  return {
    label: d[LABEL],
    group: d[GROUP],
    re,
    im,
    rect: `${d[LABEL]} = ${re.toFixed(2)} ${im < 0 ? "−" : "+"} ${Math.abs(im).toFixed(2)}i`,
    polar: `|z| = ${Math.hypot(re, im).toFixed(2)} ∠ ${((Math.atan2(im, re) * 180) / Math.PI).toFixed(0)}°`,
  };
});

// A page-coloured outline keeps text legible where it crosses the circle, grid or a vector
const halo = { stroke: t.pageBg, strokeWidth: 4, paintOrder: "stroke", strokeLinejoin: "round" } as const;

const TITLE = "scatter-complex-plane · javascript · muix · anyplot.ai";
const HEADER_HEIGHT = 64;
const LEGEND_HEIGHT = 40;
const chartWidth = window.ANYPLOT_SIZE.width;
const chartHeight = window.ANYPLOT_SIZE.height - HEADER_HEIGHT - LEGEND_HEIGHT;
const side = Math.min(chartWidth, chartHeight) - 32;
const margin = {
  top: (chartHeight - side) / 2,
  bottom: (chartHeight - side) / 2,
  left: (chartWidth - side) / 2,
  right: (chartWidth - side) / 2,
};

// Annotation placement in px from the origin: around each point, candidate text blocks on rings of
// growing distance are scored by their room to every vector and both axes, inside the plane only
const pxPerUnit = side / (2 * extent);
const annotations = points.map((p) => {
  const px = p.re * pxPerUnit;
  const py = -p.im * pxPerUnit;
  const halfWidth = Math.max(p.rect.length * 8.8, p.polar.length * 7.6) / 2;
  const candidates = LABEL_RINGS.flatMap((ring) =>
    Array.from({ length: LABEL_DIRECTIONS }, (_, k) => (2 * Math.PI * k) / LABEL_DIRECTIONS).map((a) => {
    const cos = Math.cos(a);
    const sin = Math.sin(a);
    const anchor = cos > 0.3 ? "start" : cos < -0.3 ? "end" : "middle";
    const x = px + cos * LABEL_GAP * ring;
    const y = py - sin * (LABEL_GAP * ring + 14);
    const centre = anchor === "start" ? x + halfWidth : anchor === "end" ? x - halfWidth : x;
    // Room to the nearest vector, sampled across both text rows of the block
    const samples = Array.from({ length: 9 }, (_, j) => centre - halfWidth + (j * halfWidth) / 4).flatMap((sx) => [
      [sx, y - 10],
      [sx, y + 10],
    ]);
    const vectorRoom = Math.min(
      ...samples.flatMap(([sx, sy]) =>
        points.map((q) => {
          const qx = q.re * pxPerUnit;
          const qy = -q.im * pxPerUnit;
          const s = Math.max(0, Math.min(1, (sx * qx + sy * qy) / (qx * qx + qy * qy || 1)));
          return Math.hypot(sx - s * qx, sy - s * qy) - 10;
        }),
      ),
    );
    // Axis room keeps clear of the tick labels beside each axis line; the outer ring costs a little
    const inside = Math.abs(centre) + halfWidth < side / 2 && Math.abs(y) + 20 < side / 2;
    const room = Math.min(vectorRoom, Math.abs(y) - 20 - AXIS_BAND, Math.abs(centre) - halfWidth - AXIS_BAND);
    return { x, y, anchor, ring, room: inside ? room : -Infinity };
    }),
  );
  // The nearest ring with a clear position, its roomiest position; with none clear, the roomiest overall
  const clearRing = Math.min(...candidates.filter((c) => c.room >= LABEL_CLEARANCE).map((c) => c.ring));
  const pool = Number.isFinite(clearRing) ? candidates.filter((c) => c.ring === clearRing) : candidates;
  return pool.reduce((best, c) => (c.room > best.room ? c : best));
});

function PlaneAxes() {
  const xScale = useXScale();
  const yScale = useYScale();
  const area = useDrawingArea();
  const zeroX = xScale(0);
  const zeroY = yScale(0);
  const right = area.left + area.width;
  const bottom = area.top + area.height;
  return (
    <g>
      <circle
        cx={zeroX}
        cy={zeroY}
        r={Math.abs(xScale(UNIT_RADIUS) - zeroX)}
        fill="none"
        stroke={t.inkSoft}
        strokeWidth={2}
        strokeDasharray="9 8"
      />
      <line x1={area.left} y1={zeroY} x2={right} y2={zeroY} stroke={t.ink} strokeWidth={2} />
      <line x1={zeroX} y1={area.top} x2={zeroX} y2={bottom} stroke={t.ink} strokeWidth={2} />
      {offAxisTicks.map((v) => (
        <g key={`tick-${v}`}>
          <line x1={xScale(v)} y1={zeroY - 7} x2={xScale(v)} y2={zeroY + 7} stroke={t.ink} strokeWidth={1.5} />
          <text x={xScale(v)} y={zeroY + 26} textAnchor="middle" fontSize={15} fill={t.inkSoft} {...halo}>
            {v}
          </text>
          <line x1={zeroX - 7} y1={yScale(v)} x2={zeroX + 7} y2={yScale(v)} stroke={t.ink} strokeWidth={1.5} />
          <text x={zeroX - 14} y={yScale(v)} textAnchor="end" dominantBaseline="central" fontSize={15} fill={t.inkSoft} {...halo}>
            {`${v}i`}
          </text>
        </g>
      ))}
      <text x={zeroX - 12} y={zeroY + 26} textAnchor="end" fontSize={15} fill={t.inkSoft} {...halo}>
        0
      </text>
      <text x={right - 4} y={zeroY - 14} textAnchor="end" fontSize={17} fontWeight={600} fill={t.ink}>
        {REAL}
      </text>
      <text x={zeroX + 14} y={area.top + 18} textAnchor="start" fontSize={17} fontWeight={600} fill={t.ink}>
        {IMAGINARY}
      </text>
    </g>
  );
}

function Vectors() {
  const xScale = useXScale();
  const yScale = useYScale();
  const zeroX = xScale(0);
  const zeroY = yScale(0);
  return (
    <g>
      <defs>
        {groups.map((g, i) => (
          <marker
            key={`head-${i}`}
            id={`complex-plane-head-${i}`}
            viewBox="0 0 10 10"
            refX={10}
            refY={5}
            markerWidth={14}
            markerHeight={14}
            markerUnits="userSpaceOnUse"
            orient="auto"
          >
            <path d="M0,0 L10,5 L0,10 Z" fill={groupColor[g]} />
          </marker>
        ))}
      </defs>
      {points.map((p) => {
        const px = xScale(p.re);
        const py = yScale(p.im);
        const length = Math.hypot(px - zeroX, py - zeroY);
        // The head ends at the marker's rim, so it stays visible above the point
        const tipX = px - ((px - zeroX) / length) * (MARKER_RADIUS + 1);
        const tipY = py - ((py - zeroY) / length) * (MARKER_RADIUS + 1);
        return (
          <line
            key={`vector-${p.label}`}
            x1={zeroX}
            y1={zeroY}
            x2={tipX}
            y2={tipY}
            stroke={groupColor[p.group]}
            strokeWidth={2.5}
            markerEnd={`url(#complex-plane-head-${groups.indexOf(p.group)})`}
          />
        );
      })}
    </g>
  );
}

function Annotations() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g {...halo}>
      {points.map((p, i) => {
        const { x, y, anchor } = annotations[i];
        return (
          <g key={`note-${p.label}`}>
            <text x={xScale(0) + x} y={yScale(0) + y - 10} textAnchor={anchor} dominantBaseline="central" fontSize={16} fontWeight={600} fill={t.ink}>
              {p.rect}
            </text>
            <text x={xScale(0) + x} y={yScale(0) + y + 10} textAnchor={anchor} dominantBaseline="central" fontSize={14} fill={t.inkSoft}>
              {p.polar}
            </text>
          </g>
        );
      })}
    </g>
  );
}

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
      <ChartsDataProvider
        width={chartWidth}
        height={chartHeight}
        margin={margin}
        skipAnimation
        series={groups.map((g, i) => ({
          type: "scatter" as const,
          id: `group-${i}`,
          label: g,
          color: groupColor[g],
          markerSize: MARKER_RADIUS,
          data: points.filter((p) => p.group === g).map((p) => ({ id: p.label, x: p.re, y: p.im })),
        }))}
        xAxis={[{ id: "real", scaleType: "linear", min: -extent, max: extent, tickInterval: ticks, position: "none" }]}
        yAxis={[{ id: "imaginary", scaleType: "linear", min: -extent, max: extent, tickInterval: ticks, position: "none" }]}
      >
        <ChartsWrapper legendPosition={{ vertical: "top", horizontal: "center" }} legendDirection="horizontal">
          <ChartsLegend sx={{ fontSize: 16, color: t.ink, gap: 4 }} />
          <ChartsSurface
            sx={{
              "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
              "& .MuiScatterChart-marker": { stroke: t.pageBg, strokeWidth: 2.5 },
            }}
          >
            <ChartsGrid vertical horizontal />
            <PlaneAxes />
            <Vectors />
            <ScatterPlot />
            <Annotations />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
