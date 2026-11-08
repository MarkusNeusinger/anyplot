// anyplot.ai
// contour-3d: 3D Contour Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-10

import { useRef, useState } from "react";
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import { useDrawingArea, useZColorScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const DEG = Math.PI / 180;
const AZIMUTH_DEG = 40; // opening turn of the base plane about the vertical axis
const ELEVATION_DEG = 30; // opening view angle above the base plane
const ELEVATION_RANGE = [8, 75]; // dragging keeps the elevation inside this range, in degrees
const DRAG_DEG_PER_PX = 0.4; // rotation per dragged pixel
const BOX = [1, 1, 0.62]; // half-extents of the drawn box along x, y and z
const LEVEL_COUNT = 10; // at most about this many contour intervals over the z range
const TICK_COUNT = 6; // about this many ticks per axis
const NICE_STEPS = [1, 2, 2.5, 5, 10]; // round step multipliers per power of ten
const FLOOR_SHARE = 0.25; // gap between the lowest surface point and the base plane, as a share of the z range
const SURFACE_ALPHA = 0.5; // opacity of the surface sheet, so what lies behind it shows faded
const TICK_PX = 8; // tick mark length
const TICK_LABEL_PX = 16; // gap between an axis and its tick labels
const AXIS_TITLE_PX = 58; // gap between an axis and its title
const TITLE = "contour-3d · javascript · muix · anyplot.ai";
const HEADER_H = 84;
const LEGEND_W = 200;
const MARGIN = { top: 24, right: 64, bottom: 92, left: 120 };

// Columns: set these to your data's column names
const TEMPERATURE = "Temperature (°C)"; // role: x
const PRESSURE = "Pressure (bar)"; // role: y
const YIELD = "Yield (%)"; // role: z

// Data: replace this block with your own records, one object per grid point
// Chemical-process yield over reactor temperature and pressure on a 34 × 34 grid: a second-order
// response-surface model (linear, quadratic and interaction terms) with a mild ripple, so the
// optimum sits off the centre of the design space and the level curves are not plain ellipses.
const data = (() => {
  const rows = [];
  for (let i = 0; i < 34; i += 1) {
    for (let j = 0; j < 34; j += 1) {
      const temperature = 150 + (100 * i) / 33;
      const pressure = 10 + (40 * j) / 33;
      const u = (temperature - 200) / 50;
      const v = (pressure - 30) / 20;
      const yieldPct = 90 - 15 * u * u - 20 * v * v + 8 * u * v + 3 * Math.sin(3 * u) * Math.cos(2 * v);
      rows.push({
        [TEMPERATURE]: Math.round(temperature * 100) / 100,
        [PRESSURE]: Math.round(pressure * 100) / 100,
        [YIELD]: Math.round(yieldPct * 100) / 100,
      });
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
const rows = data.filter((d) => [TEMPERATURE, PRESSURE, YIELD].every((c) => Number.isFinite(d[c])));
const xs = [...new Set(rows.map((d) => d[TEMPERATURE]))].sort((a, b) => a - b);
const ys = [...new Set(rows.map((d) => d[PRESSURE]))].sort((a, b) => a - b);
const zAt = new Map(rows.map((d) => [`${d[TEMPERATURE]}|${d[PRESSURE]}`, d[YIELD]]));
// grid[j][i] is the height at xs[i], ys[j]; a missing grid point stays null and its cells are skipped
const grid = ys.map((y) => xs.map((x) => zAt.get(`${x}|${y}`) ?? null));
const zLo = Math.min(...rows.map((d) => d[YIELD]));
const zHi = Math.max(...rows.map((d) => d[YIELD]));
const peak = rows.reduce((best, d) => (d[YIELD] > best[YIELD] ? d : best), rows[0]);

// Contour levels: the multiples of a round step that lie strictly inside the z range
const levelRaw = (zHi - zLo) / LEVEL_COUNT;
const levelMagnitude = 10 ** Math.floor(Math.log10(levelRaw));
const levelStep = NICE_STEPS.map((m) => m * levelMagnitude).find((s) => s >= levelRaw);
const firstLevel = Math.floor(zLo / levelStep) + 1;
const levels = Array.from({ length: Math.ceil(zHi / levelStep) - firstLevel }, (_, k) =>
  Number(((firstLevel + k) * levelStep).toFixed(10)),
);

// Box extents per axis: the grid's x and y range, and z from the base plane, set below the
// lowest point, to the highest point; round ticks inside each extent
const axes = [
  { name: TEMPERATURE, lo: xs[0], hi: xs[xs.length - 1] },
  { name: PRESSURE, lo: ys[0], hi: ys[ys.length - 1] },
  { name: YIELD, lo: zLo - FLOOR_SHARE * (zHi - zLo), hi: zHi },
].map((axis) => {
  const raw = (axis.hi - axis.lo) / TICK_COUNT;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  const step = NICE_STEPS.map((m) => m * magnitude).find((s) => s >= raw);
  const first = Math.ceil(axis.lo / step - 1e-9);
  const last = Math.floor(axis.hi / step + 1e-9);
  return { ...axis, ticks: Array.from({ length: last - first + 1 }, (_, k) => Number(((first + k) * step).toFixed(10))) };
});

// Surface cells and level curves by marching triangles: each grid cell splits into four triangles
// around its centre, which settles the saddle cases; a level crossing a triangle leaves one segment
const cells = [];
const contours = levels.map((level) => ({ level, segments: [] }));
for (let j = 0; j < ys.length - 1; j += 1) {
  for (let i = 0; i < xs.length - 1; i += 1) {
    const corners = [
      [i, j],
      [i + 1, j],
      [i + 1, j + 1],
      [i, j + 1],
    ].map(([a, b]) => ({ x: xs[a], y: ys[b], z: grid[b][a] }));
    if (corners.some((p) => p.z == null)) continue;
    cells.push(corners);
    const center = {
      x: (xs[i] + xs[i + 1]) / 2,
      y: (ys[j] + ys[j + 1]) / 2,
      z: corners.reduce((s, p) => s + p.z, 0) / 4,
    };
    contours.forEach(({ level, segments }) => {
      corners.forEach((p, m) => {
        const triangle = [p, corners[(m + 1) % 4], center];
        const cuts = [];
        triangle.forEach((a, n) => {
          const b = triangle[(n + 1) % 3];
          if ((a.z >= level) !== (b.z >= level)) {
            const r = (level - a.z) / (b.z - a.z);
            cuts.push({ x: a.x + r * (b.x - a.x), y: a.y + r * (b.y - a.y) });
          }
        });
        if (cuts.length === 2) segments.push(cuts);
      });
    });
  }
}
// The outer edge of the grid, drawn as the rim of the surface sheet
const rim = [
  ...xs.map((_, i) => [i, 0]),
  ...ys.map((_, j) => [xs.length - 1, j]),
  ...xs.map((_, i) => [xs.length - 1 - i, ys.length - 1]),
  ...ys.map((_, j) => [0, ys.length - 1 - j]),
].map(([i, j]) => ({ x: xs[i], y: ys[j], z: grid[j][i] }));

// The opening view fixes the layout: the chart takes the width the box needs at that view, so the
// colour bar sits beside it; a turned view shrinks to fit the same area
const openAz = AZIMUTH_DEG * DEG;
const openEl = ELEVATION_DEG * DEG;
const boxAspect =
  (BOX[0] * Math.abs(Math.cos(openAz)) + BOX[1] * Math.abs(Math.sin(openAz))) /
  ((BOX[0] * Math.abs(Math.sin(openAz)) + BOX[1] * Math.abs(Math.cos(openAz))) * Math.sin(openEl) + BOX[2] * Math.cos(openEl));

const SUBTITLE = `${xs.length} × ${ys.length} grid · ${levels.length} level curves every ${levelStep} from ${levels[0]} to ${levels[levels.length - 1]}, lifted to their height and projected onto the base plane`;

// The community package has no 3D chart: this layer turns the box, the surface sheet and the
// level curves into screen coordinates for the current view, with one scale for both screen axes,
// and colours every curve through the z axis colour map that the colour bar shows.
function ContourLayer({ azimuth, elevation }: { azimuth: number; elevation: number }) {
  const { left, top, width, height } = useDrawingArea();
  const colorOf = useZColorScale("level");
  const ca = Math.cos(azimuth);
  const sa = Math.sin(azimuth);
  const ce = Math.cos(elevation);
  const se = Math.sin(elevation);
  // A data point in box coordinates (-1 to 1 per axis), then seen from the view: screen x,
  // screen y (up) and depth (away from the viewer)
  const view = (x: number, y: number, z: number) => {
    const [bx, by, bz] = [x, y, z].map((v, k) => ((2 * (v - axes[k].lo)) / (axes[k].hi - axes[k].lo) - 1) * BOX[k]);
    const ahead = bx * sa + by * ca;
    return [bx * ca - by * sa, ahead * se + bz * ce, ahead * ce - bz * se];
  };

  const [xLo, xHi] = [axes[0].lo, axes[0].hi];
  const [yLo, yHi] = [axes[1].lo, axes[1].hi];
  const [zBase, zTop] = [axes[2].lo, axes[2].hi];
  const baseCorners = [
    [xLo, yLo],
    [xHi, yLo],
    [xHi, yHi],
    [xLo, yHi],
  ].map(([x, y]) => ({ x, y, bottom: view(x, y, zBase), top: view(x, y, zTop) }));
  const frame = baseCorners.flatMap((c) => [c.bottom, c.top]);
  const sxLo = Math.min(...frame.map((p) => p[0]));
  const sxHi = Math.max(...frame.map((p) => p[0]));
  const syLo = Math.min(...frame.map((p) => p[1]));
  const syHi = Math.max(...frame.map((p) => p[1]));
  const k = Math.min(width / (sxHi - sxLo), height / (syHi - syLo));
  const ox = left + width / 2 - ((sxLo + sxHi) / 2) * k;
  const oy = top + height / 2 + ((syLo + syHi) / 2) * k;
  const px = (p: number[]) => ({ x: ox + p[0] * k, y: oy - p[1] * k });
  const pts = (ps: number[][]) => ps.map((p) => `${px(p).x.toFixed(1)},${px(p).y.toFixed(1)}`).join(" ");
  // One level's segments as a path at height z
  const segPath = (segments: { x: number; y: number }[][], z: number) =>
    segments
      .map(([from, to]) => {
        const a = px(view(from.x, from.y, z));
        const b = px(view(to.x, to.y, z));
        return `M${a.x.toFixed(1)},${a.y.toFixed(1)}L${b.x.toFixed(1)},${b.y.toFixed(1)}`;
      })
      .join("");

  // The base corner nearest the viewer joins the x and y axes; the two back walls meet at the
  // farthest corner; the z axis rises at the leftmost of the two side corners
  const byDepth = [...baseCorners].sort((p, q) => p.bottom[2] - q.bottom[2]);
  const near = byDepth[0];
  const far = byDepth[3];
  const [leftSide, rightSide] = [byDepth[1], byDepth[2]].sort((p, q) => p.bottom[0] - q.bottom[0]);
  const floorMid = px(view((xLo + xHi) / 2, (yLo + yHi) / 2, zBase));

  // Outward unit vector on screen for an axis drawn from a to b, turned away from the floor centre
  const outward = (a: { x: number; y: number }, b: { x: number; y: number }) => {
    const len = Math.hypot(b.x - a.x, b.y - a.y);
    const flip = ((a.x + b.x) / 2 - floorMid.x) * (a.y - b.y) + ((a.y + b.y) / 2 - floorMid.y) * (b.x - a.x) < 0 ? -1 : 1;
    return { ux: (flip * (a.y - b.y)) / len, uy: (flip * (b.x - a.x)) / len };
  };
  const anchor = (u: number) => (u > 0.3 ? "start" : u < -0.3 ? "end" : "middle");
  const baseline = (u: number) => (u > 0.3 ? "hanging" : u < -0.3 ? "auto" : "central");

  const groundArms = [
    { axis: axes[0], at: (v: number) => view(v, near.y, zBase), from: view(xLo, near.y, zBase), to: view(xHi, near.y, zBase) },
    { axis: axes[1], at: (v: number) => view(near.x, v, zBase), from: view(near.x, yLo, zBase), to: view(near.x, yHi, zBase) },
  ].map((arm) => {
    const a = px(arm.from);
    const b = px(arm.to);
    const out = outward(a, b);
    let angle = (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI;
    if (angle > 90) angle -= 180;
    if (angle < -90) angle += 180;
    const mid = { x: (a.x + b.x) / 2 + out.ux * AXIS_TITLE_PX, y: (a.y + b.y) / 2 + out.uy * AXIS_TITLE_PX };
    return { ...arm, a, b, out, angle, mid, ticks: arm.axis.ticks.map((v) => ({ v, p: px(arm.at(v)) })) };
  });
  const zFoot = px(leftSide.bottom);
  const zHead = px(leftSide.top);
  const zTicks = axes[2].ticks.map((v) => ({ v, p: px(view(leftSide.x, leftSide.y, v)) }));
  const zTitle = { x: zFoot.x - AXIS_TITLE_PX, y: (zFoot.y + zHead.y) / 2 };

  const peakTop = px(view(peak[TEMPERATURE], peak[PRESSURE], peak[YIELD]));
  const peakFoot = px(view(peak[TEMPERATURE], peak[PRESSURE], zBase));

  return (
    <g>
      {/* Base plane and the two back walls, with grid lines at the ticks */}
      <polygon points={pts(baseCorners.map((c) => c.bottom))} fill={t.elevatedBg} stroke={t.grid} strokeWidth={1.2} />
      {[leftSide, rightSide].map((side) => (
        <g key={`wall-${side.x}-${side.y}`}>
          <polygon points={pts([side.bottom, far.bottom, far.top, side.top])} fill={t.elevatedBg} stroke={t.grid} strokeWidth={1.2} />
          {axes[2].ticks.map((v) => (
            <polyline key={v} points={pts([view(side.x, side.y, v), view(far.x, far.y, v)])} stroke={t.grid} strokeWidth={1} fill="none" />
          ))}
        </g>
      ))}
      {axes[0].ticks.map((v) => (
        <polyline key={`gx-${v}`} points={pts([view(v, yLo, zBase), view(v, yHi, zBase)])} stroke={t.grid} strokeWidth={1} fill="none" />
      ))}
      {axes[1].ticks.map((v) => (
        <polyline key={`gy-${v}`} points={pts([view(xLo, v, zBase), view(xHi, v, zBase)])} stroke={t.grid} strokeWidth={1} fill="none" />
      ))}

      {/* Level curves projected onto the base plane, at the same levels and colours */}
      {contours.map(({ level, segments }) => (
        <path
          key={`floor-${level}`}
          d={segPath(segments, zBase)}
          stroke={colorOf(level)}
          strokeWidth={1.6}
          strokeLinecap="round"
          fill="none"
        />
      ))}

      {/* Drop line from the highest grid point to the base plane, under the surface sheet */}
      <line x1={peakFoot.x} y1={peakFoot.y} x2={peakTop.x} y2={peakTop.y} stroke={t.inkSoft} strokeWidth={1.5} strokeDasharray="5 4" />
      <circle cx={peakFoot.x} cy={peakFoot.y} r={4} fill={t.inkSoft} />

      {/* Translucent surface sheet: what lies below it shows through, faded */}
      {cells.map((corners, idx) => (
        <polygon
          key={idx}
          points={pts(corners.map((c) => view(c.x, c.y, c.z)))}
          fill={t.elevatedBg}
          fillOpacity={SURFACE_ALPHA}
          stroke={t.grid}
          strokeWidth={0.8}
        />
      ))}

      <path
        d={rim
          .map((p, m) => {
            if (p.z == null) return "";
            const q = px(view(p.x, p.y, p.z));
            return `${m === 0 || rim[m - 1].z == null ? "M" : "L"}${q.x.toFixed(1)},${q.y.toFixed(1)}`;
          })
          .join("")}
        stroke={t.inkSoft}
        strokeWidth={1.2}
        strokeLinejoin="round"
        fill="none"
      />

      {/* Level curves lifted to their height */}
      {contours.map(({ level, segments }) => (
        <path
          key={`lifted-${level}`}
          d={segPath(segments, level)}
          stroke={colorOf(level)}
          strokeWidth={2.8}
          strokeLinecap="round"
          fill="none"
        />
      ))}

      {/* Axes on the edges that face the viewer */}
      {groundArms.map((arm) => (
        <g key={arm.axis.name}>
          <line x1={arm.a.x} y1={arm.a.y} x2={arm.b.x} y2={arm.b.y} stroke={t.inkSoft} strokeWidth={1.5} />
          {arm.ticks.map(({ v, p }) => (
            <g key={v}>
              <line x1={p.x} y1={p.y} x2={p.x + arm.out.ux * TICK_PX} y2={p.y + arm.out.uy * TICK_PX} stroke={t.inkSoft} strokeWidth={1.5} />
              <text
                x={p.x + arm.out.ux * TICK_LABEL_PX}
                y={p.y + arm.out.uy * TICK_LABEL_PX}
                textAnchor={anchor(arm.out.ux)}
                dominantBaseline={baseline(arm.out.uy)}
                fontSize={14}
                fill={t.inkSoft}
              >
                {v}
              </text>
            </g>
          ))}
          <text
            x={arm.mid.x}
            y={arm.mid.y}
            transform={`rotate(${arm.angle.toFixed(1)} ${arm.mid.x.toFixed(1)} ${arm.mid.y.toFixed(1)})`}
            textAnchor="middle"
            dominantBaseline="central"
            fontSize={16}
            fontWeight={600}
            fill={t.ink}
          >
            {arm.axis.name}
          </text>
        </g>
      ))}
      <line x1={zFoot.x} y1={zFoot.y} x2={zHead.x} y2={zHead.y} stroke={t.inkSoft} strokeWidth={1.5} />
      {zTicks.map(({ v, p }) => (
        <g key={v}>
          <line x1={p.x} y1={p.y} x2={p.x - TICK_PX} y2={p.y} stroke={t.inkSoft} strokeWidth={1.5} />
          <text x={p.x - TICK_LABEL_PX} y={p.y} textAnchor="end" dominantBaseline="central" fontSize={14} fill={t.inkSoft}>
            {v}
          </text>
        </g>
      ))}
      <text
        x={zTitle.x}
        y={zTitle.y}
        transform={`rotate(-90 ${zTitle.x.toFixed(1)} ${zTitle.y.toFixed(1)})`}
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={16}
        fontWeight={600}
        fill={t.ink}
      >
        {YIELD}
      </text>

      {/* The highest grid point */}
      <circle cx={peakTop.x} cy={peakTop.y} r={6} fill={t.ink} stroke={t.pageBg} strokeWidth={2} />
      <text
        x={peakTop.x + 14}
        y={peakTop.y - 20}
        fontSize={15}
        fontWeight={600}
        fill={t.ink}
        stroke={t.pageBg}
        strokeWidth={4}
        paintOrder="stroke"
      >
        {`Maximum ${peak[YIELD]}`}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  // Dragging turns the surface (horizontal drag) and tilts it (vertical drag)
  const [viewDeg, setViewDeg] = useState({ azimuth: AZIMUTH_DEG, elevation: ELEVATION_DEG });
  const drag = useRef<{ x: number; y: number } | null>(null);
  const chartH = height - HEADER_H;
  const chartW = Math.min(width - LEGEND_W, MARGIN.left + MARGIN.right + (chartH - MARGIN.top - MARGIN.bottom) * boxAspect);

  const onPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    drag.current = { x: e.clientX, y: e.clientY };
    e.currentTarget.setPointerCapture(e.pointerId);
  };
  const onPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!drag.current) return;
    const dx = e.clientX - drag.current.x;
    const dy = e.clientY - drag.current.y;
    drag.current = { x: e.clientX, y: e.clientY };
    setViewDeg((v) => ({
      azimuth: v.azimuth - dx * DRAG_DEG_PER_PX,
      elevation: Math.min(ELEVATION_RANGE[1], Math.max(ELEVATION_RANGE[0], v.elevation + dy * DRAG_DEG_PER_PX)),
    }));
  };
  const onPointerUp = () => {
    drag.current = null;
  };

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <div style={{ height: HEADER_H, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6 }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
      </div>
      <ChartsDataProvider
        width={chartW}
        height={chartH}
        series={[]}
        skipAnimation
        margin={MARGIN}
        zAxis={[
          {
            id: "level",
            min: levels[0],
            max: levels[levels.length - 1],
            colorMap: { type: "continuous", min: levels[0], max: levels[levels.length - 1], color: [t.seq[0], t.seq[1]] },
          },
        ]}
      >
        <ChartsWrapper
          legendPosition={{ vertical: "middle", horizontal: "end" }}
          legendDirection="vertical"
          sx={{ width: chartW + LEGEND_W, height: chartH }}
        >
          <div style={{ gridArea: "legend", width: LEGEND_W, height: chartH * 0.6, display: "flex", flexDirection: "column", alignItems: "center" }}>
            <div style={{ fontSize: 16, fontWeight: 600, color: t.ink, marginBottom: 12 }}>{YIELD}</div>
            <ContinuousColorLegend
              axisDirection="z"
              axisId="level"
              direction="vertical"
              thickness={18}
              labelPosition="end"
              sx={{ flex: 1, fontSize: 14, color: t.inkSoft }}
            />
          </div>
          <div
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerCancel={onPointerUp}
            style={{ gridArea: "chart", cursor: "grab", touchAction: "none" }}
          >
            <ChartsSurface>
              <ContourLayer azimuth={viewDeg.azimuth * DEG} elevation={viewDeg.elevation * DEG} />
            </ChartsSurface>
          </div>
        </ChartsWrapper>
      </ChartsDataProvider>
    </div>
  );
}
