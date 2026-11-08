// anyplot.ai
// scatter-shot-chart: Basketball Shot Chart
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: pending | Created: 2026-06-21
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
// NBA half court in feet, origin at the basket center
const COURT_WIDTH = 50;
const COURT_DEPTH = 47; // baseline to half-court line
const RIM_FROM_BASELINE = 5.25;
const BACKBOARD_FROM_BASELINE = 4;
const BACKBOARD_WIDTH = 6;
const RIM_RADIUS = 0.75;
const PAINT_WIDTH = 16;
const FREE_THROW_FROM_BASELINE = 19; // 15 ft from the backboard
const FREE_THROW_CIRCLE_R = 6;
const RESTRICTED_R = 4;
const THREE_ARC_R = 23.75;
const THREE_CORNER_X = 22;
const OUTCOME_LABELS = { made: "Made", missed: "Missed" };
const MARKER_RADII = [4.5, 6, 7.5]; // px, by shot type ranked on its mean distance from the basket
const MARKER_OPACITY = 0.8;

// Columns: set these to your data's column names
const X = "Court x (ft from basket)"; // role: x
const Y = "Court y (ft from basket)"; // role: y
const MADE = "Made"; // role: made
const SHOT_TYPE = "Shot type"; // role: shot_type

// Data: replace this block with your own records, one object per row
// One player's season of 300 attempts: rim, mid-range, corner and arc threes, free throws.
let seed = 42;
const u = Array.from({ length: 2400 }, () => (seed = (Math.imul(1664525, seed) + 1013904223) >>> 0) / 4294967296);
let k = 0;
const data: Record<string, number | boolean | string>[] = [];
for (let i = 0; i < 300; i += 1) {
  const zone = u[k++];
  let x = 0;
  let y = 0; // feet from the baseline while generating
  let shotType = "2-pointer";
  if (zone < 0.2) {
    const angle = u[k++] * Math.PI;
    const dist = u[k++] * 4 + 0.5;
    x = Math.cos(angle) * dist;
    y = RIM_FROM_BASELINE + Math.sin(angle) * dist;
  } else if (zone < 0.3) {
    x = (zone < 0.25 ? -1 : 1) * (u[k++] * 2.3 + 22.2);
    y = u[k++] * 10 + 0.5;
    shotType = "3-pointer";
  } else if (zone < 0.58) {
    const angle = u[k++] * Math.PI;
    const dist = u[k++] * 8 + 9;
    x = Math.cos(angle) * dist;
    y = RIM_FROM_BASELINE + Math.sin(angle) * dist;
  } else if (zone < 0.85) {
    // the angle range shrinks with the distance, so every arc three lands inside the sidelines
    const share = u[k++];
    const dist = u[k++] * 4.5 + THREE_ARC_R;
    const edge = Math.acos(Math.min(1, (COURT_WIDTH / 2 - 0.5) / dist));
    const angle = edge + share * (Math.PI - 2 * edge);
    x = Math.cos(angle) * dist;
    y = RIM_FROM_BASELINE + Math.sin(angle) * dist;
    shotType = "3-pointer";
  } else {
    x = u[k++] * 0.8 - 0.4;
    y = FREE_THROW_FROM_BASELINE + u[k++] * 0.6 - 0.3;
    shotType = "free-throw";
  }
  const near = Math.hypot(x, y - RIM_FROM_BASELINE) < 7;
  const makePct = shotType === "free-throw" ? 0.78 : shotType === "3-pointer" ? 0.37 : near ? 0.6 : 0.41;
  data.push({
    [X]: Number(x.toFixed(2)),
    [Y]: Number((y - RIM_FROM_BASELINE).toFixed(2)),
    [MADE]: u[k++] < makePct,
    [SHOT_TYPE]: shotType,
  });
}

// Plot: reads only data and the constants above
const { width: W, height: H } = window.ANYPLOT_SIZE;
const outcomeColor = { made: t.palette[0], missed: t.palette[4] };

const types = [...new Set(data.map((d) => String(d[SHOT_TYPE])))];
const typeStats = types
  .map((type) => {
    const rows = data.filter((d) => d[SHOT_TYPE] === type);
    const meanDist = rows.reduce((s, d) => s + Math.hypot(Number(d[X]), Number(d[Y])), 0) / rows.length;
    return { type, attempts: rows.length, made: rows.filter((d) => d[MADE]).length, meanDist };
  })
  .sort((a, b) => a.meanDist - b.meanDist);
const radiusOf = new Map(typeStats.map((s, i) => [s.type, MARKER_RADII[i]]));

const shots = data.map((d, i) => ({
  id: i,
  x: Number(d[X]),
  y: Number(d[Y]),
  made: Boolean(d[MADE]),
  r: radiusOf.get(String(d[SHOT_TYPE])) as number,
}));
const missedShots = shots.filter((s) => !s.made);
const madeShots = shots.filter((s) => s.made);
const madeTotal = madeShots.length;

// Court geometry in basket-centered feet
const baselineY = -RIM_FROM_BASELINE;
const halfCourtY = COURT_DEPTH - RIM_FROM_BASELINE;
const backboardY = BACKBOARD_FROM_BASELINE - RIM_FROM_BASELINE;
const freeThrowY = FREE_THROW_FROM_BASELINE - RIM_FROM_BASELINE;
const cornerTopY = Math.sqrt(THREE_ARC_R ** 2 - THREE_CORNER_X ** 2);

// Layout: equal px per foot on both axes, court centered in the chart area
const HEADER_H = 92;
const LEGEND_H = 56;
const MIN_SIDE = 40;
const MIN_VERT = 14;
const chartH = H - HEADER_H - LEGEND_H;
const pxPerFt = Math.min((W - 2 * MIN_SIDE) / COURT_WIDTH, (chartH - 2 * MIN_VERT) / COURT_DEPTH);
const sideMargin = (W - pxPerFt * COURT_WIDTH) / 2;
const vertMargin = (chartH - pxPerFt * COURT_DEPTH) / 2;

const title = "scatter-shot-chart · javascript · muix · anyplot.ai";
const subtitle = [
  `${shots.length} attempts, ${madeTotal} made (${((100 * madeTotal) / shots.length).toFixed(1)}%)`,
  ...typeStats.map((s) => `${s.type} ${s.made}/${s.attempts} (${((100 * s.made) / s.attempts).toFixed(0)}%)`),
].join(" · ");

function Court() {
  const xs = useXScale("court-x") as (v: number) => number;
  const ys = useYScale("court-y") as (v: number) => number;
  const line = { fill: "none", stroke: t.inkSoft, strokeWidth: 2, strokeLinecap: "round" as const };
  const ftR = FREE_THROW_CIRCLE_R * pxPerFt;
  return (
    <g>
      <rect
        x={xs(-COURT_WIDTH / 2)}
        y={ys(halfCourtY)}
        width={COURT_WIDTH * pxPerFt}
        height={COURT_DEPTH * pxPerFt}
        style={{ ...line, strokeWidth: 2.5 }}
      />
      <rect
        x={xs(-PAINT_WIDTH / 2)}
        y={ys(freeThrowY)}
        width={PAINT_WIDTH * pxPerFt}
        height={(freeThrowY - baselineY) * pxPerFt}
        style={line}
      />
      <path
        d={`M ${xs(-FREE_THROW_CIRCLE_R)} ${ys(freeThrowY)} A ${ftR} ${ftR} 0 0 1 ${xs(FREE_THROW_CIRCLE_R)} ${ys(freeThrowY)}`}
        style={line}
      />
      <path
        d={`M ${xs(-FREE_THROW_CIRCLE_R)} ${ys(freeThrowY)} A ${ftR} ${ftR} 0 0 0 ${xs(FREE_THROW_CIRCLE_R)} ${ys(freeThrowY)}`}
        style={{ ...line, strokeDasharray: "8 7" }}
      />
      <path
        d={`M ${xs(-RESTRICTED_R)} ${ys(backboardY)} L ${xs(-RESTRICTED_R)} ${ys(0)} A ${RESTRICTED_R * pxPerFt} ${RESTRICTED_R * pxPerFt} 0 0 1 ${xs(RESTRICTED_R)} ${ys(0)} L ${xs(RESTRICTED_R)} ${ys(backboardY)}`}
        style={line}
      />
      <path
        d={`M ${xs(-THREE_CORNER_X)} ${ys(baselineY)} L ${xs(-THREE_CORNER_X)} ${ys(cornerTopY)} A ${THREE_ARC_R * pxPerFt} ${THREE_ARC_R * pxPerFt} 0 0 1 ${xs(THREE_CORNER_X)} ${ys(cornerTopY)} L ${xs(THREE_CORNER_X)} ${ys(baselineY)}`}
        style={line}
      />
      <line
        x1={xs(-BACKBOARD_WIDTH / 2)}
        y1={ys(backboardY)}
        x2={xs(BACKBOARD_WIDTH / 2)}
        y2={ys(backboardY)}
        style={{ ...line, strokeWidth: 4 }}
      />
      <circle cx={xs(0)} cy={ys(0)} r={RIM_RADIUS * pxPerFt} style={{ ...line, strokeWidth: 2.5 }} />
    </g>
  );
}

function ShotMarkers() {
  const xs = useXScale("court-x") as (v: number) => number;
  const ys = useYScale("court-y") as (v: number) => number;
  return (
    <g>
      {missedShots.map((s) => {
        const px = xs(s.x);
        const py = ys(s.y);
        return (
          <path
            key={s.id}
            d={`M ${px - s.r} ${py - s.r} L ${px + s.r} ${py + s.r} M ${px + s.r} ${py - s.r} L ${px - s.r} ${py + s.r}`}
            stroke={outcomeColor.missed}
            strokeWidth={s.r * 0.55}
            strokeOpacity={MARKER_OPACITY}
            strokeLinecap="round"
          />
        );
      })}
      {madeShots.map((s) => (
        <circle
          key={s.id}
          cx={xs(s.x)}
          cy={ys(s.y)}
          r={s.r}
          fill={outcomeColor.made}
          fillOpacity={MARKER_OPACITY}
        />
      ))}
    </g>
  );
}

export default function Chart() {
  const glyph = MARKER_RADII[MARKER_RADII.length - 1];
  return (
    <div style={{ width: W, height: H, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 8,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{title}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{subtitle}</div>
      </div>
      <ChartsContainer
        width={W}
        height={chartH}
        skipAnimation
        series={[]}
        margin={{ top: vertMargin, bottom: vertMargin, left: sideMargin, right: sideMargin }}
        xAxis={[{ id: "court-x", min: -COURT_WIDTH / 2, max: COURT_WIDTH / 2, position: "none" }]}
        yAxis={[{ id: "court-y", min: baselineY, max: halfCourtY, position: "none" }]}
      >
        <Court />
        <ShotMarkers />
      </ChartsContainer>
      <div
        style={{
          height: LEGEND_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 22,
          fontSize: 16,
          color: t.ink,
        }}
      >
        <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <svg width={2 * glyph + 4} height={2 * glyph + 4}>
            <circle cx={glyph + 2} cy={glyph + 2} r={glyph} fill={outcomeColor.made} fillOpacity={MARKER_OPACITY} />
          </svg>
          {OUTCOME_LABELS.made}
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <svg width={2 * glyph + 4} height={2 * glyph + 4}>
            <path
              d={`M 2 2 L ${2 * glyph + 2} ${2 * glyph + 2} M ${2 * glyph + 2} 2 L 2 ${2 * glyph + 2}`}
              stroke={outcomeColor.missed}
              strokeWidth={glyph * 0.55}
              strokeOpacity={MARKER_OPACITY}
              strokeLinecap="round"
            />
          </svg>
          {OUTCOME_LABELS.missed}
        </span>
        <span style={{ color: t.inkSoft, marginLeft: 18 }}>{SHOT_TYPE} (marker size):</span>
        {typeStats.map((s, i) => (
          <span key={s.type} style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <svg width={2 * glyph + 4} height={2 * glyph + 4}>
              <circle cx={glyph + 2} cy={glyph + 2} r={MARKER_RADII[i]} fill={t.inkSoft} fillOpacity={0.75} />
            </svg>
            {s.type}
          </span>
        ))}
      </div>
    </div>
  );
}
