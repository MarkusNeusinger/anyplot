// anyplot.ai
// scatter-pitch-events: Soccer Pitch Event Map
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: pending | Created: 2026-06-21

import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
// FIFA pitch geometry in metres
const PITCH_LENGTH = 105;
const PITCH_WIDTH = 68;
const CENTRE_CIRCLE_RADIUS = 9.15;
const PENALTY_AREA_DEPTH = 16.5;
const PENALTY_AREA_WIDTH = 40.32;
const GOAL_AREA_DEPTH = 5.5;
const GOAL_AREA_WIDTH = 18.32;
const PENALTY_SPOT_DISTANCE = 11;
const GOAL_WIDTH = 7.32;
const GOAL_DEPTH = 2;
const CORNER_ARC_RADIUS = 1;
const RUN_OFF = 3; // metres shown around the pitch, room for the goals
// One shape per event type, by order of first appearance (unit radius, centred on the origin)
const MARKER_SHAPES = [
  "M -1 0 A 1 1 0 1 0 1 0 A 1 1 0 1 0 -1 0 Z",
  `M ${Array.from({ length: 10 }, (_, i) => {
    const a = (i * Math.PI) / 5 - Math.PI / 2;
    const r = i % 2 === 0 ? 1.25 : 0.5;
    return `${(r * Math.cos(a)).toFixed(3)} ${(r * Math.sin(a)).toFixed(3)}`;
  }).join(" L ")} Z`,
  "M 0 -1.15 L 1 0.6 L -1 0.6 Z",
  "M 0 -1.2 L 0.85 0 L 0 1.2 L -0.85 0 Z",
  "M -0.9 -0.9 L 0.9 -0.9 L 0.9 0.9 L -0.9 0.9 Z",
  "M 0 1.15 L 1 -0.6 L -1 -0.6 Z",
];
const FILLED_OUTCOME = "Successful"; // the spec's outcome levels: this one is drawn filled, any other hollow
const MARKER_RADIUS = 8; // px
// The spec asks for a white pitch with contrasting lines in both themes, so the pitch keeps the
// light theme's elevated surface and soft ink in either theme instead of flipping with the page
const PITCH_SURFACE = "#FFFDF6";
const PITCH_INK = "#4A4A44";
const RUN_OFF_TINT = 0.15; // opacity of the ink wash that sets the run-off apart from the pitch

// Columns: set these to your data's column names
const X = "x (m)"; // role: x
const Y = "y (m)"; // role: y
const EVENT = "Event type"; // role: event_type
const OUTCOME = "Outcome"; // role: outcome
const END_X = "End x (m)"; // role: end_x
const END_Y = "End y (m)"; // role: end_y

// Data: replace this block with your own records, one object per row
// Synthetic match segment: passes and shots carry an end position, tackles and
// interceptions do not.
const data = (() => {
  let s = 42;
  const rng = () => {
    s = (Math.imul(1664525, s) + 1013904223) >>> 0;
    return s / 4294967296;
  };
  const rows = [];
  const event = (type, x, y, ok, endX = null, endY = null) =>
    rows.push({
      [X]: Number(x.toFixed(1)),
      [Y]: Number(y.toFixed(1)),
      [EVENT]: type,
      [OUTCOME]: ok ? "Successful" : "Unsuccessful",
      [END_X]: endX === null ? null : Number(endX.toFixed(1)),
      [END_Y]: endY === null ? null : Number(endY.toFixed(1)),
    });
  for (let i = 0; i < 48; i += 1) {
    const x = rng() * 100 + 2.5;
    const y = rng() * 63 + 2.5;
    const dx = (rng() - 0.2) * 22;
    const dy = (rng() - 0.5) * 16;
    const endX = Math.max(2, Math.min(103, x + dx));
    const endY = Math.max(2, Math.min(66, y + dy));
    event("Pass", x, y, rng() > 0.22, endX, endY);
  }
  for (let i = 0; i < 10; i += 1) {
    const x = 70 + rng() * 30;
    const y = 17 + rng() * 34;
    const endX = 102 + rng() * 3;
    const endY = 30.34 + rng() * 7.32;
    event("Shot", x, y, rng() > 0.75, endX, endY);
  }
  for (let i = 0; i < 22; i += 1) {
    const x = rng() * 105;
    const y = rng() * 68;
    event("Tackle", x, y, rng() > 0.35);
  }
  for (let i = 0; i < 18; i += 1) {
    const x = rng() * 105;
    const y = rng() * 68;
    event("Interception", x, y, rng() > 0.12);
  }
  return rows;
})();

// Plot: reads only data and the constants above
const types = [...new Set(data.map((d) => d[EVENT]))];
const outcomes = [...new Set(data.map((d) => d[OUTCOME]))];
const events = data.map((d, i) => {
  const k = types.indexOf(d[EVENT]);
  return {
    id: `event-${i}`,
    x: d[X],
    y: d[Y],
    endX: d[END_X],
    endY: d[END_Y],
    color: t.palette[k],
    shape: MARKER_SHAPES[k],
    typeIndex: k,
    filled: d[OUTCOME] === FILLED_OUTCOME,
  };
});
// Arrows go wherever a row carries an end position
const arrows = events.filter((e) => e.endX !== null && e.endY !== null);
const arrowTypes = types.filter((_, k) => arrows.some((a) => a.typeIndex === k));

const penaltyArcHalf = Math.sqrt(CENTRE_CIRCLE_RADIUS ** 2 - (PENALTY_AREA_DEPTH - PENALTY_SPOT_DISTANCE) ** 2);
const corners = [
  [0, 0, 1, 1],
  [PITCH_LENGTH, 0, -1, 1],
  [0, PITCH_WIDTH, 1, -1],
  [PITCH_LENGTH, PITCH_WIDTH, -1, -1],
]; // corner x, corner y, and the inward direction along each touchline

const TITLE = "scatter-pitch-events · javascript · muix · anyplot.ai";
const SUBTITLE = `${data.length} events · ${PITCH_LENGTH} m × ${PITCH_WIDTH} m pitch · arrows run to the end position of ${arrowTypes.map((s) => s.toLowerCase()).join(" and ")} events`;
const HEADER_HEIGHT = 72;
const LEGEND_HEIGHT = 48;
const chartWidth = window.ANYPLOT_SIZE.width;
const chartHeight = window.ANYPLOT_SIZE.height - HEADER_HEIGHT - LEGEND_HEIGHT;

// Equal px per metre on both axes keeps the centre circle round and the pitch at 105:68
const domainLength = PITCH_LENGTH + 2 * RUN_OFF;
const domainWidth = PITCH_WIDTH + 2 * RUN_OFF;
const areaHeight = Math.min(chartHeight - 16, ((chartWidth - 48) * domainWidth) / domainLength);
const areaWidth = (areaHeight * domainLength) / domainWidth;
const marginX = (chartWidth - areaWidth) / 2;
const marginY = (chartHeight - areaHeight) / 2;

const line = { fill: "none", stroke: PITCH_INK, strokeWidth: 2 };

function PitchMarkings() {
  const { left, top, width, height } = useDrawingArea();
  const xs = useXScale();
  const ys = useYScale();
  const k = xs(1) - xs(0); // px per metre
  const midY = PITCH_WIDTH / 2;
  return (
    <g>
      <rect x={left} y={top} width={width} height={height} fill={PITCH_SURFACE} />
      <rect x={left} y={top} width={width} height={height} fill={PITCH_INK} fillOpacity={RUN_OFF_TINT} />
      <rect x={xs(0)} y={ys(PITCH_WIDTH)} width={PITCH_LENGTH * k} height={PITCH_WIDTH * k} fill={PITCH_SURFACE} />
      <rect {...line} x={xs(0)} y={ys(PITCH_WIDTH)} width={PITCH_LENGTH * k} height={PITCH_WIDTH * k} />
      <line {...line} x1={xs(PITCH_LENGTH / 2)} y1={ys(0)} x2={xs(PITCH_LENGTH / 2)} y2={ys(PITCH_WIDTH)} />
      <circle {...line} cx={xs(PITCH_LENGTH / 2)} cy={ys(midY)} r={CENTRE_CIRCLE_RADIUS * k} />
      <circle cx={xs(PITCH_LENGTH / 2)} cy={ys(midY)} r={3.5} fill={PITCH_INK} />
      {[0, PITCH_LENGTH].map((goalLine) => {
        const inward = goalLine === 0 ? 1 : -1;
        const spotX = goalLine + inward * PENALTY_SPOT_DISTANCE;
        const boxX = goalLine + inward * PENALTY_AREA_DEPTH;
        return (
          <g key={`end-${goalLine}`}>
            <rect
              {...line}
              x={xs(Math.min(goalLine, boxX))}
              y={ys(midY + PENALTY_AREA_WIDTH / 2)}
              width={PENALTY_AREA_DEPTH * k}
              height={PENALTY_AREA_WIDTH * k}
            />
            <rect
              {...line}
              x={xs(Math.min(goalLine, goalLine + inward * GOAL_AREA_DEPTH))}
              y={ys(midY + GOAL_AREA_WIDTH / 2)}
              width={GOAL_AREA_DEPTH * k}
              height={GOAL_AREA_WIDTH * k}
            />
            <rect
              {...line}
              strokeWidth={3}
              x={xs(Math.min(goalLine, goalLine - inward * GOAL_DEPTH))}
              y={ys(midY + GOAL_WIDTH / 2)}
              width={GOAL_DEPTH * k}
              height={GOAL_WIDTH * k}
            />
            <circle cx={xs(spotX)} cy={ys(midY)} r={3} fill={PITCH_INK} />
            {/* Penalty arc: the part of the 9.15 m circle around the spot that lies outside the box */}
            <path
              {...line}
              d={`M ${xs(boxX)} ${ys(midY + penaltyArcHalf)} A ${CENTRE_CIRCLE_RADIUS * k} ${CENTRE_CIRCLE_RADIUS * k} 0 0 ${goalLine === 0 ? 1 : 0} ${xs(boxX)} ${ys(midY - penaltyArcHalf)}`}
            />
          </g>
        );
      })}
      {corners.map(([cx, cy, dx, dy]) => (
        <path
          key={`corner-${cx}-${cy}`}
          {...line}
          d={`M ${xs(cx + dx * CORNER_ARC_RADIUS)} ${ys(cy)} A ${CORNER_ARC_RADIUS * k} ${CORNER_ARC_RADIUS * k} 0 0 ${-dx * dy > 0 ? 1 : 0} ${xs(cx)} ${ys(cy + dy * CORNER_ARC_RADIUS)}`}
        />
      ))}
    </g>
  );
}

function EventLayer() {
  const xs = useXScale();
  const ys = useYScale();
  return (
    <g>
      <defs>
        {types.map((type, k) => (
          <marker
            key={`head-${type}`}
            id={`pitch-head-${k}`}
            viewBox="0 0 10 10"
            refX={9}
            refY={5}
            markerWidth={11}
            markerHeight={11}
            markerUnits="userSpaceOnUse"
            orient="auto"
          >
            <path d="M 0 0 L 10 5 L 0 10 Z" fill={t.palette[k]} />
          </marker>
        ))}
      </defs>
      {arrows.map((a) => (
        <line
          key={`arrow-${a.id}`}
          x1={xs(a.x)}
          y1={ys(a.y)}
          x2={xs(a.endX)}
          y2={ys(a.endY)}
          stroke={a.color}
          strokeOpacity={a.filled ? 0.8 : 0.55}
          strokeWidth={a.filled ? 1.8 : 1.4}
          strokeDasharray={a.filled ? undefined : "5 4"}
          markerEnd={`url(#pitch-head-${a.typeIndex})`}
        />
      ))}
      {events.map((e) => (
        <path
          key={e.id}
          d={e.shape}
          transform={`translate(${xs(e.x)} ${ys(e.y)}) scale(${MARKER_RADIUS})`}
          vectorEffect="non-scaling-stroke"
          fill={e.filled ? e.color : PITCH_SURFACE}
          stroke={e.filled ? PITCH_SURFACE : e.color}
          strokeWidth={e.filled ? 1 : 2.2}
        />
      ))}
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
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>
      <ChartsDataProvider
        width={chartWidth}
        height={chartHeight}
        margin={{ top: marginY, bottom: marginY, left: marginX, right: marginX }}
        skipAnimation
        xAxis={[{ id: "x", scaleType: "linear", min: -RUN_OFF, max: PITCH_LENGTH + RUN_OFF, position: "none" }]}
        yAxis={[{ id: "y", scaleType: "linear", min: -RUN_OFF, max: PITCH_WIDTH + RUN_OFF, position: "none" }]}
      >
        <ChartsSurface>
          <PitchMarkings />
          <EventLayer />
        </ChartsSurface>
      </ChartsDataProvider>
      <div
        style={{
          height: LEGEND_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 26,
          fontSize: 16,
          color: t.ink,
        }}
      >
        {types.map((type, k) => (
          <span key={`legend-${type}`} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <svg width={24} height={24}>
              <path d={MARKER_SHAPES[k]} transform={`translate(12 12) scale(${MARKER_RADIUS})`} fill={t.palette[k]} />
            </svg>
            {type}
          </span>
        ))}
        <span style={{ width: 1, height: 24, background: t.grid }} />
        {outcomes.map((outcome) => (
          <span key={`legend-${outcome}`} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <svg width={24} height={24}>
              <path
                d={MARKER_SHAPES[0]}
                transform={`translate(12 12) scale(${MARKER_RADIUS})`}
                vectorEffect="non-scaling-stroke"
                fill={outcome === FILLED_OUTCOME ? t.inkSoft : "none"}
                stroke={t.inkSoft}
                strokeWidth={2}
              />
            </svg>
            {outcome}
          </span>
        ))}
      </div>
    </div>
  );
}
