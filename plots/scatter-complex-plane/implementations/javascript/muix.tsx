// anyplot.ai
// scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08
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
const LABEL_GAP = 22; // px between a point and its annotation, outward along the point's phase
const ROW_GAP = 22; // px between the rectangular and the polar row of an annotation
const BLOCK_LIFT = 26; // px from a point's height to its annotation's centre, away from the real axis
const MARKER_RADIUS = 9; // px
const UNIT_TICK_NUDGE = 14; // px a tick label on the unit circle moves outward along its axis, off the circle
const ZERO_OFFSET = [14, 20]; // px from the origin to the "0" label, across and along the real axis
const MINUS = "−"; // one minus sign for every number on the plot

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
const tickStep = NICE_STEPS.find((s) => s * magnitude >= rawStep) * magnitude;
const ticks = Array.from(
  { length: 2 * Math.floor(extent / tickStep) + 1 },
  (_, k) => Number(((k - Math.floor(extent / tickStep)) * tickStep).toFixed(6)),
);
// A tick label on the unit circle moves outward along its axis, so the circle does not run through it
const offAxisTicks = ticks
  .filter((v) => v !== 0)
  .map((v) => ({ v, text: `${v}`.replace("-", MINUS), nudge: Math.abs(v) === UNIT_RADIUS ? Math.sign(v) * UNIT_TICK_NUDGE : 0 }));

const points = data.map((d) => {
  const re = d[REAL];
  const im = d[IMAGINARY];
  return {
    label: d[LABEL],
    group: d[GROUP],
    re,
    im,
    rect: `${d[LABEL]} = ${re.toFixed(2).replace("-", MINUS)} ${im < 0 ? MINUS : "+"} ${Math.abs(im).toFixed(2)}i`,
    polar: `|z| = ${Math.hypot(re, im).toFixed(2)} ∠ ${((Math.atan2(im, re) * 180) / Math.PI).toFixed(0).replace("-", MINUS)}°`,
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

// Annotation placement in px from the origin: each block sits just beyond its point along the point's
// phase, on the side facing away from the origin, so it clears its own vector and the unit circle
const pxPerUnit = side / (2 * extent);
const annotations = points.map((p) => {
  const theta = Math.atan2(p.im, p.re);
  const cos = Math.cos(theta);
  const sin = Math.sin(theta);
  const r = Math.hypot(p.re, p.im) * pxPerUnit + LABEL_GAP;
  const anchor = cos > 0.3 ? "start" : cos < -0.3 ? "end" : "middle";
  const dir = anchor === "start" ? 1 : anchor === "end" ? -1 : 0;
  const x = cos * r;
  const y = -sin * r + (sin < 0 ? BLOCK_LIFT : -BLOCK_LIFT);
  // A neighbouring vector that would run through the block, on the side the text extends to, pushes the block past it
  const crossings = points
    .filter((q) => q !== p && q.im !== 0)
    .flatMap((q) => [y - BLOCK_LIFT, y + BLOCK_LIFT].map((ry) => ({ s: ry / (-q.im * pxPerUnit), ry, q })))
    .filter(({ s }) => s > 0 && s <= 1)
    .map(({ s, q }) => s * q.re * pxPerUnit)
    .filter((cx) => dir !== 0 && (cx - x) * dir > 0);
  const pushed = crossings.length ? (dir > 0 ? Math.max(...crossings) : Math.min(...crossings)) + dir * LABEL_GAP : x;
  return { x: pushed, y, anchor };
});

// The origin's "0" goes into the quadrant whose bisector lies furthest in angle from every vector
const angleGap = (a: number, b: number) => Math.abs(((a - b + 3 * Math.PI) % (2 * Math.PI)) - Math.PI);
const zeroQuadrant = [
  [1, 1],
  [-1, 1],
  [-1, -1],
  [1, -1],
]
  .map(([sx, sy]) => ({ sx, sy, room: Math.min(...points.map((q) => angleGap(Math.atan2(sy, sx), Math.atan2(q.im, q.re)))) }))
  .reduce((best, q) => (q.room > best.room ? q : best));

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
      {offAxisTicks.map(({ v }) => (
        <g key={`tick-${v}`}>
          <line x1={xScale(v)} y1={zeroY - 7} x2={xScale(v)} y2={zeroY + 7} stroke={t.ink} strokeWidth={1.5} />
          <line x1={zeroX - 7} y1={yScale(v)} x2={zeroX + 7} y2={yScale(v)} stroke={t.ink} strokeWidth={1.5} />
        </g>
      ))}
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

// Tick labels sit above the vectors, so their halo keeps them legible where a vector passes
function TickLabels() {
  const xScale = useXScale();
  const yScale = useYScale();
  const zeroX = xScale(0);
  const zeroY = yScale(0);
  return (
    <g {...halo}>
      {offAxisTicks.map(({ v, text, nudge }) => (
        <g key={`tick-label-${v}`}>
          <text x={xScale(v) + nudge} y={zeroY + 28} textAnchor="middle" fontSize={17} fill={t.inkSoft}>
            {text}
          </text>
          <text x={zeroX - 14} y={yScale(v) - nudge} textAnchor="end" dominantBaseline="central" fontSize={17} fill={t.inkSoft}>
            {`${text}i`}
          </text>
        </g>
      ))}
      <text
        x={zeroX + zeroQuadrant.sx * ZERO_OFFSET[0]}
        y={zeroY - zeroQuadrant.sy * ZERO_OFFSET[1]}
        textAnchor={zeroQuadrant.sx > 0 ? "start" : "end"}
        dominantBaseline="central"
        fontSize={17}
        fill={t.inkSoft}
      >
        0
      </text>
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
            <text x={xScale(0) + x} y={yScale(0) + y - ROW_GAP / 2} textAnchor={anchor} dominantBaseline="central" fontSize={18} fontWeight={600} fill={t.ink}>
              {p.rect}
            </text>
            <text x={xScale(0) + x} y={yScale(0) + y + ROW_GAP / 2} textAnchor={anchor} dominantBaseline="central" fontSize={17} fill={t.inkSoft}>
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
            <TickLabels />
            <ScatterPlot />
            <Annotations />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
