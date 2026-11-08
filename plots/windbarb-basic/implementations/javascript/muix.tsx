// anyplot.ai
// windbarb-basic: Wind Barb Plot for Meteorological Data
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 91/100 | Created: 2026-09-02
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
// Standard barb notation, counted in knots: a half barb is 5 kt, a full barb
// 10 kt, a pennant 50 kt; below 2.5 kt the wind is calm.
const KNOTS = "kt";
const CALM_KT = 2.5;
const HALF_KT = 5;
const FULL_KT = 10;
const PENNANT_KT = 50;
const KEY_SPEEDS = [0, HALF_KT, 2 * FULL_KT + HALF_KT, PENNANT_KT]; // key glyphs, wind from the north
// Feather direction, turned clockwise on screen from the staff's outward
// direction: Northern Hemisphere feathers point toward low pressure, on the
// staff's left seen downwind (east for a north wind), and lean out to the tip.
const BARB_ANGLE_DEG = 68;
const STAFF_PX = 46;
const FEATHER_PX = 16;
const FEATHER_GAP_PX = 8;
const LONE_HALF_GAPS = 1.5; // a lone half barb sits this many gaps in from the tip, so it is not read as a full barb
const PENNANT_BASE_PX = 12;
const CALM_R = 5.5;
const POS_PAD = 0.125; // share of the station extent added on every side
const TICK_PX = 130; // target spacing between axis ticks, the same on both axes
const BRAND = t.palette[0];
const TITLE = "windbarb-basic · javascript · muix · anyplot.ai";
const TITLE_H = 80;
const KEY_W = 200;
const X_AXIS_H = 72;
const Y_AXIS_W = 88;
const MARGIN = { top: 24, right: 24, bottom: 12, left: 24 };

// Columns: set these to your data's column names
const X = "Distance east (km)"; // role: x
const Y = "Distance north (km)"; // role: y
const U = "Eastward wind u (kt)"; // role: u
const V = "Northward wind v (kt)"; // role: v

// Data: replace this block with your own records, one object per row
// Surface wind observations around a low-pressure system: a 6 × 5 station
// grid plus one station in the calm eye, from a Rankine-like vortex (58 kt
// peak at 180 km) with 22° of cross-isobar inflow.
const data = (() => {
  const cx = 400;
  const cy = 300;
  const inflow = (22 * Math.PI) / 180;
  const points = [];
  for (let x = 0; x <= 800; x += 160) for (let y = 0; y <= 600; y += 150) points.push([x, y]);
  points.push([cx + 2 * Math.cos((35 * Math.PI) / 180), cy + 2 * Math.sin((35 * Math.PI) / 180)]);
  return points.map(([x, y]) => {
    const r = Math.hypot(x - cx, y - cy);
    const dirE = Math.cos(inflow) * (-(y - cy) / r) + Math.sin(inflow) * (-(x - cx) / r);
    const dirN = Math.cos(inflow) * ((x - cx) / r) + Math.sin(inflow) * (-(y - cy) / r);
    const speed = 58 * (r / 180) * Math.exp(1 - r / 180);
    return {
      [X]: Math.round(x * 10) / 10,
      [Y]: Math.round(y * 10) / 10,
      [U]: Math.round(speed * dirE * 100) / 100,
      [V]: Math.round(speed * dirN * 100) / 100,
    };
  });
})();

// Plot: reads only data and the constants above
const stations = data.filter((d) => d[X] != null && d[Y] != null && d[U] != null && d[V] != null);
const xs = stations.map((d) => d[X]);
const ys = stations.map((d) => d[Y]);
const xMid = (Math.min(...xs) + Math.max(...xs)) / 2;
const yMid = (Math.min(...ys) + Math.max(...ys)) / 2;
const xNeed = (Math.max(...xs) - Math.min(...xs)) * (1 + 2 * POS_PAD);
const yNeed = (Math.max(...ys) - Math.min(...ys)) * (1 + 2 * POS_PAD);

// Glyph geometry in px around the station: the staff points into the wind,
// and the speed, rounded to the nearest half barb, is spent from the tip
// inward on pennants, then full barbs, then at most one half barb.
const featherAngle = (BARB_ANGLE_DEG * Math.PI) / 180;
const glyphs = [...stations.map((d) => [d[U], d[V]]), ...KEY_SPEEDS.map((s) => [0, -s])].map(([u, v]) => {
  const speed = Math.hypot(u, v);
  if (speed < CALM_KT) return null;
  const ox = -u / speed;
  const oy = v / speed;
  const fx = ox * Math.cos(featherAngle) - oy * Math.sin(featherAngle);
  const fy = ox * Math.sin(featherAngle) + oy * Math.cos(featherAngle);
  const tipX = ox * STAFF_PX;
  const tipY = oy * STAFF_PX;
  const rounded = Math.round(speed / HALF_KT) * HALF_KT;
  const pennantCount = Math.floor(rounded / PENNANT_KT);
  const fullCount = Math.floor((rounded - pennantCount * PENNANT_KT) / FULL_KT);
  const hasHalf = rounded - pennantCount * PENNANT_KT - fullCount * FULL_KT >= HALF_KT;
  const pennants = Array.from({ length: pennantCount }, (_, p) => {
    const ax = tipX - ox * p * PENNANT_BASE_PX;
    const ay = tipY - oy * p * PENNANT_BASE_PX;
    const bx = tipX - ox * (p + 1) * PENNANT_BASE_PX;
    const by = tipY - oy * (p + 1) * PENNANT_BASE_PX;
    return `${ax},${ay} ${bx},${by} ${(ax + bx) / 2 + fx * FEATHER_PX},${(ay + by) / 2 + fy * FEATHER_PX}`;
  });
  const firstGap = pennantCount > 0 ? 0.5 : fullCount === 0 ? LONE_HALF_GAPS : 0;
  const feathers = Array.from({ length: fullCount + (hasHalf ? 1 : 0) }, (_, k) => {
    const along = pennantCount * PENNANT_BASE_PX + (k + firstGap) * FEATHER_GAP_PX;
    const sx = tipX - ox * along;
    const sy = tipY - oy * along;
    const len = k < fullCount ? FEATHER_PX : FEATHER_PX / 2;
    return [sx, sy, sx + fx * len, sy + fy * len];
  });
  return { tipX, tipY, pennants, feathers };
});
// One drawing per glyph, centered on (0, 0): the station layer and the key
// both place these.
const glyphMarks = glyphs.map((g, i) =>
  g == null ? (
    <circle key={i} r={CALM_R} fill="none" stroke={BRAND} strokeWidth={2.5} />
  ) : (
    <g key={i}>
      <circle r={2.2} fill={BRAND} />
      <line x2={g.tipX} y2={g.tipY} stroke={BRAND} strokeWidth={3} strokeLinecap="round" />
      {g.pennants.map((points, k) => (
        <polygon key={`p${k}`} points={points} fill={BRAND} />
      ))}
      {g.feathers.map(([x1, y1, x2, y2], k) => (
        <line key={`f${k}`} x1={x1} y1={y1} x2={x2} y2={y2} stroke={BRAND} strokeWidth={3.2} strokeLinecap="round" />
      ))}
    </g>
  ),
);
const keyLabels = KEY_SPEEDS.map((s) => (s < CALM_KT ? `Calm (< ${CALM_KT} ${KNOTS})` : `${s} ${KNOTS}`));
const SUBTITLE = `${stations.length} stations · each staff points to where the wind blows from · speed rounded to ${HALF_KT} ${KNOTS}`;

// The community package has no barb glyph: a custom layer places each one at
// its station through the chart's linear scales.
function WindBarbLayer() {
  const xScale = useXScale();
  const yScale = useYScale();

  return (
    <g>
      {stations.map((d, i) => (
        <g key={i} transform={`translate(${xScale(d[X])},${yScale(d[Y])})`}>
          {glyphMarks[i]}
        </g>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  // Equal km per pixel on both axes, so distances and directions keep their
  // shape: the binding axis fills its room, the other one shrinks to the
  // stations' extent, and the chart and key sit centred on the page
  const roomW = width - KEY_W - MARGIN.left - MARGIN.right - Y_AXIS_W;
  const roomH = height - TITLE_H - MARGIN.top - MARGIN.bottom - X_AXIS_H;
  const kmPerPx = Math.max(xNeed / roomW, yNeed / roomH);
  const drawW = Math.floor(xNeed / kmPerPx);
  const drawH = Math.floor(yNeed / kmPerPx);
  const chartW = drawW + MARGIN.left + MARGIN.right + Y_AXIS_W;
  const chartH = drawH + MARGIN.top + MARGIN.bottom + X_AXIS_H;

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, padding: "18px 36px 0", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2, marginTop: 8 }}>{SUBTITLE}</div>
      </div>
      <div style={{ display: "flex", justifyContent: "center" }}>
        <ChartsContainer
          width={chartW}
          height={chartH}
          series={[]}
          skipAnimation
          margin={MARGIN}
          xAxis={[
            {
              id: "x",
              scaleType: "linear",
              min: xMid - (kmPerPx * drawW) / 2,
              max: xMid + (kmPerPx * drawW) / 2,
              tickNumber: Math.ceil(drawW / TICK_PX),
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
              min: yMid - (kmPerPx * drawH) / 2,
              max: yMid + (kmPerPx * drawH) / 2,
              tickNumber: Math.ceil(drawH / TICK_PX),
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
          <WindBarbLayer />
          <ChartsXAxis axisId="x" />
          <ChartsYAxis axisId="y" />
        </ChartsContainer>
        <div style={{ width: KEY_W, paddingTop: MARGIN.top, display: "flex", flexDirection: "column", gap: 14 }}>
          <span style={{ fontSize: 16, fontWeight: 600, color: t.ink }}>Wind speed</span>
          {keyLabels.map((label, j) => (
            <div key={label} style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <svg width={44} height={56} style={{ overflow: "visible" }}>
                <g transform={`translate(30,${glyphs[stations.length + j] == null ? 28 : 50})`}>{glyphMarks[stations.length + j]}</g>
              </svg>
              <span style={{ fontSize: 15, color: t.inkSoft }}>{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
