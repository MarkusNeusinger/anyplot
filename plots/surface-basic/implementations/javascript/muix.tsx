// anyplot.ai
// surface-basic: Basic 3D Surface Plot
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 86/100 | Updated: 2026-11-08
import { useMemo, useRef, useState } from "react";
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import { useXScale, useYScale, useZColorScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const DEG = Math.PI / 180;
const VIEW_ANGLE = 25 * DEG; // initial tilt of the ground plane's axes below the horizontal
const AZIMUTH = 45 * DEG; // initial turn of the ground about the vertical axis
const TILT_RANGE = [10 * DEG, 60 * DEG]; // dragging keeps the tilt inside this range
const DRAG_SPEED = 0.4 * DEG; // rotation per dragged pixel
const HEIGHT_SHARE = 0.5; // full z range drawn as this share of the ground's side
const TICK_COUNT = 6; // about this many ticks per axis
const TICK_PX = 7; // tick mark length (px)
const TICK_LABEL_PX = 14; // gap between an axis and its tick labels (px)
const AXIS_TITLE_PX = 48; // gap between an axis and its title (px)
const HEADER_H = 84;
const LEGEND_W = 150;
const MARGIN = { top: 56, right: 64, bottom: 80, left: 120 };

// Data: replace these with your own grid, z[row][col] being the height at x[col], y[row]
// Terrain elevation over a 12 × 12 km survey area, two hills and two basins on
// rolling ground, sampled on a 30 × 30 grid
const X_NAME = "Easting (km)";
const Y_NAME = "Northing (km)";
const Z_NAME = "Elevation (m)";
const GRID_N = 30;
const x = Array.from({ length: GRID_N }, (_, i) => (12 * i) / (GRID_N - 1)); // role: x
const y = Array.from({ length: GRID_N }, (_, i) => (12 * i) / (GRID_N - 1)); // role: y
const z = y.map((yv) => x.map((xv) => Number((420 + 80 * Math.sin((xv - 6) / 2) * Math.cos((yv - 6) / 2)).toFixed(1)))); // role: z

// Plot: reads only the grid and the constants above
// The ground is the unit square (gx along x, gy along y), the height gz runs 0 to
// HEIGHT_SHARE; the ground turns by the azimuth about its centre and an oblique
// projection maps (gx, gy, gz) to the plane, with depth b growing towards the viewer
const xMin = Math.min(...x);
const xMax = Math.max(...x);
const yMin = Math.min(...y);
const yMax = Math.max(...y);
const zMin = Math.min(...z.flat());
const zMax = Math.max(...z.flat());
const gxOf = x.map((v) => (v - xMin) / (xMax - xMin));
const gyOf = y.map((v) => (v - yMin) / (yMax - yMin));
const gzOf = (v: number) => ((v - zMin) / (zMax - zMin)) * HEIGHT_SHARE;

// Round tick values inside each axis' extent
const [xTicks, yTicks, zTicks] = [
  [xMin, xMax],
  [yMin, yMax],
  [zMin, zMax],
].map(([lo, hi]) => {
  const raw = (hi - lo) / TICK_COUNT;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * magnitude).find((s) => s >= raw) ?? raw;
  const first = Math.ceil(lo / step - 1e-9);
  const last = Math.floor(hi / step + 1e-9);
  return Array.from({ length: last - first + 1 }, (_, i) => Number(((first + i) * step).toFixed(10)));
});

type Point = { px: number; py: number };

function buildScene(azimuth: number, tilt: number) {
  const cosA = Math.cos(azimuth);
  const sinA = Math.sin(azimuth);
  const across = Math.SQRT2 * Math.cos(VIEW_ANGLE);
  const deep = Math.SQRT2 * Math.sin(tilt);
  const lift = Math.cos(tilt) / Math.cos(VIEW_ANGLE);
  const depthOf = (gx: number, gy: number) => (gx - 0.5) * sinA + (gy - 0.5) * cosA;
  const project = (gx: number, gy: number, gz: number): Point => ({
    px: across * ((gx - 0.5) * cosA - (gy - 0.5) * sinA),
    py: gz * lift - deep * depthOf(gx, gy),
  });
  // screen direction (y down) of a ground vector, used to push tick labels outwards
  const outward = (dx: number, dy: number) => {
    const ux = across * (dx * cosA - dy * sinA);
    const uy = deep * (dx * sinA + dy * cosA);
    const len = Math.hypot(ux, uy) || 1;
    return { ux: ux / len, uy: uy / len };
  };

  const vertices = z.map((row, r) => row.map((v, c) => project(gxOf[c], gyOf[r], gzOf(v))));
  // One quad per grid cell, colored by its mean height and painted back to front
  const quads = vertices
    .slice(0, -1)
    .flatMap((row, r) =>
      row.slice(0, -1).map((_, c) => ({
        id: `${r}-${c}`,
        depth: depthOf((gxOf[c] + gxOf[c + 1]) / 2, (gyOf[r] + gyOf[r + 1]) / 2),
        corners: [vertices[r][c], vertices[r][c + 1], vertices[r + 1][c + 1], vertices[r + 1][c]],
        height: (z[r][c] + z[r][c + 1] + z[r + 1][c + 1] + z[r + 1][c]) / 4,
      })),
    )
    .sort((a, b) => a.depth - b.depth);

  // The x ticks sit on the nearer of the two y edges, the y ticks on the nearer x edge,
  // and the z axis rises from the leftmost base corner
  const xEdgeGy = cosA >= 0 ? 1 : 0;
  const yEdgeGx = sinA >= 0 ? 1 : 0;
  const xOut = outward(0, xEdgeGy ? 1 : -1);
  const yOut = outward(yEdgeGx ? 1 : -1, 0);
  const corners = [
    [0, 0],
    [1, 0],
    [1, 1],
    [0, 1],
  ];
  const base = corners.map(([gx, gy]) => project(gx, gy, 0));
  const [zGx, zGy] = [...corners].sort(
    ([ax, ay], [bx, by]) => project(ax, ay, 0).px - project(bx, by, 0).px || depthOf(bx, by) - depthOf(ax, ay),
  )[0];

  const frame = {
    base,
    xEdge: [project(0, xEdgeGy, 0), project(1, xEdgeGy, 0)],
    yEdge: [project(yEdgeGx, 0, 0), project(yEdgeGx, 1, 0)],
    zBase: project(zGx, zGy, 0),
    zTop: project(zGx, zGy, HEIGHT_SHARE),
    xTicks: xTicks.map((v) => ({ value: v, ...project((v - xMin) / (xMax - xMin), xEdgeGy, 0) })),
    yTicks: yTicks.map((v) => ({ value: v, ...project(yEdgeGx, (v - yMin) / (yMax - yMin), 0) })),
    zTicks: zTicks.map((v) => ({ value: v, ...project(zGx, zGy, gzOf(v)) })),
    xTitle: project(0.5, xEdgeGy, 0),
    yTitle: project(yEdgeGx, 0.5, 0),
    xOut,
    yOut,
  };

  const allPoints = [...vertices.flat(), ...base, frame.zTop];
  const bounds = {
    pxLo: Math.min(...allPoints.map((p) => p.px)),
    pxHi: Math.max(...allPoints.map((p) => p.px)),
    pyLo: Math.min(...allPoints.map((p) => p.py)),
    pyHi: Math.max(...allPoints.map((p) => p.py)),
  };
  return { quads, frame, bounds };
}

type Scene = ReturnType<typeof buildScene>;
const initialScene = buildScene(AZIMUTH, VIEW_ANGLE);

const tickFormat = (v: number) => Number(v.toFixed(2)).toString();
const anchorOf = (u: number) => (u > 0.2 ? "start" : u < -0.2 ? "end" : "middle");
const baselineOf = (u: number) => (u > 0.2 ? "hanging" : u < -0.2 ? "auto" : "central");

const TITLE = "surface-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${x.length} × ${y.length} grid · ${Z_NAME} from ${tickFormat(zMin)} to ${tickFormat(zMax)}`;
const textSx = { fontSize: 14, fill: t.inkSoft };
const titleText = { fontSize: 16, fontWeight: 600, fill: t.ink };

function SurfaceLayer({ scene }: { scene: Scene }) {
  const xScale = useXScale("iso-x");
  const yScale = useYScale("iso-y");
  const colorOf = useZColorScale("height");
  const { quads, frame } = scene;
  const sx = (p: Point) => xScale(p.px) ?? 0;
  const sy = (p: Point) => yScale(p.py) ?? 0;
  const edge = ([a, b]: Point[]) => <line x1={sx(a)} y1={sy(a)} x2={sx(b)} y2={sy(b)} />;
  const groundTicks = (ticks: (Point & { value: number })[], out: { ux: number; uy: number }, prefix: string) =>
    ticks.map((a) => (
      <g key={`${prefix}-${a.value}`}>
        <line x1={sx(a)} y1={sy(a)} x2={sx(a) + TICK_PX * out.ux} y2={sy(a) + TICK_PX * out.uy} stroke={t.inkSoft} strokeWidth={1.5} />
        <text
          x={sx(a) + TICK_LABEL_PX * out.ux}
          y={sy(a) + TICK_LABEL_PX * out.uy}
          textAnchor={anchorOf(out.ux)}
          dominantBaseline={baselineOf(out.uy)}
          {...textSx}
        >
          {tickFormat(a.value)}
        </text>
      </g>
    ));

  return (
    <g>
      <polygon points={frame.base.map((p) => `${sx(p)},${sy(p)}`).join(" ")} fill="none" stroke={t.grid} strokeWidth={1.5} />
      {quads.map((q) => (
        <polygon
          key={q.id}
          points={q.corners.map((p) => `${sx(p)},${sy(p)}`).join(" ")}
          fill={colorOf?.(q.height) ?? t.seq[0]}
          stroke={t.pageBg}
          strokeOpacity={0.35}
          strokeWidth={0.6}
        />
      ))}
      <g stroke={t.inkSoft} strokeWidth={1.5}>
        {edge(frame.xEdge)}
        {edge(frame.yEdge)}
        {edge([frame.zBase, frame.zTop])}
      </g>
      {groundTicks(frame.xTicks, frame.xOut, "x")}
      {groundTicks(frame.yTicks, frame.yOut, "y")}
      {frame.zTicks.map((a) => (
        <g key={`z-${a.value}`}>
          <line x1={sx(a)} y1={sy(a)} x2={sx(a) - TICK_PX} y2={sy(a)} stroke={t.inkSoft} strokeWidth={1.5} />
          <text x={sx(a) - TICK_LABEL_PX} y={sy(a)} textAnchor="end" dominantBaseline="central" {...textSx}>
            {tickFormat(a.value)}
          </text>
        </g>
      ))}
      <text
        x={sx(frame.xTitle) + AXIS_TITLE_PX * frame.xOut.ux}
        y={sy(frame.xTitle) + AXIS_TITLE_PX * frame.xOut.uy}
        textAnchor={anchorOf(frame.xOut.ux)}
        dominantBaseline={baselineOf(frame.xOut.uy)}
        {...titleText}
      >
        {X_NAME}
      </text>
      <text
        x={sx(frame.yTitle) + AXIS_TITLE_PX * frame.yOut.ux}
        y={sy(frame.yTitle) + AXIS_TITLE_PX * frame.yOut.uy}
        textAnchor={anchorOf(frame.yOut.ux)}
        dominantBaseline={baselineOf(frame.yOut.uy)}
        {...titleText}
      >
        {Y_NAME}
      </text>
      <text x={sx(frame.zTop)} y={sy(frame.zTop) - 18} textAnchor="middle" {...titleText}>
        {Z_NAME}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  // dragging the surface turns it (horizontal drag) and tilts it (vertical drag)
  const [view, setView] = useState({ azimuth: AZIMUTH, tilt: VIEW_ANGLE });
  const drag = useRef<{ x: number; y: number } | null>(null);
  const scene = useMemo(() => buildScene(view.azimuth, view.tilt), [view]);

  const chartW = width - LEGEND_W;
  const chartH = height - HEADER_H;
  const fit = ({ pxLo, pxHi, pyLo, pyHi }: Scene["bounds"]) =>
    Math.min((chartW - MARGIN.left - MARGIN.right) / (pxHi - pxLo), (chartH - MARGIN.top - MARGIN.bottom) / (pyHi - pyLo));
  // the opening view fixes the layout: equal px per unit on both axes keeps the
  // projection's angles true, and the chart takes only the width the surface needs,
  // so the colour bar sits right beside it; a turned view shrinks to fit, never grows
  const k0 = fit(initialScene.bounds);
  const drawW = k0 * (initialScene.bounds.pxHi - initialScene.bounds.pxLo);
  const drawH = chartH - MARGIN.top - MARGIN.bottom;
  const plotW = drawW + MARGIN.left + MARGIN.right;
  const { pxLo, pxHi, pyLo, pyHi } = scene.bounds;
  const k = Math.min(k0, drawW / (pxHi - pxLo), drawH / (pyHi - pyLo));
  const pxMid = (pxLo + pxHi) / 2;
  const pyMid = (pyLo + pyHi) / 2;

  const onPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    drag.current = { x: e.clientX, y: e.clientY };
    e.currentTarget.setPointerCapture(e.pointerId);
  };
  const onPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!drag.current) return;
    const dx = e.clientX - drag.current.x;
    const dy = e.clientY - drag.current.y;
    drag.current = { x: e.clientX, y: e.clientY };
    setView((v) => ({
      azimuth: v.azimuth - dx * DRAG_SPEED,
      tilt: Math.min(TILT_RANGE[1], Math.max(TILT_RANGE[0], v.tilt + dy * DRAG_SPEED)),
    }));
  };
  const onPointerUp = () => {
    drag.current = null;
  };

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <Box sx={{ height: HEADER_H, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "6px", pt: "8px" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2 }}>{SUBTITLE}</Typography>
      </Box>
      <ChartsDataProvider
        width={plotW}
        height={chartH}
        series={[]}
        skipAnimation
        margin={MARGIN}
        xAxis={[{ id: "iso-x", scaleType: "linear", min: pxMid - drawW / (2 * k), max: pxMid + drawW / (2 * k), position: "none" }]}
        yAxis={[{ id: "iso-y", scaleType: "linear", min: pyMid - drawH / (2 * k), max: pyMid + drawH / (2 * k), position: "none" }]}
        zAxis={[{ id: "height", min: zMin, max: zMax, colorMap: { type: "continuous", min: zMin, max: zMax, color: [t.seq[0], t.seq[1]] } }]}
      >
        <ChartsWrapper legendPosition={{ vertical: "middle", horizontal: "end" }} legendDirection="vertical" sx={{ width: plotW + LEGEND_W, height: chartH }}>
          <Box sx={{ gridArea: "legend", width: LEGEND_W, height: chartH * 0.55, display: "flex", flexDirection: "column", alignItems: "center" }}>
            <Typography sx={{ color: t.ink, fontSize: 15, fontWeight: 600, mb: "10px" }}>{Z_NAME}</Typography>
            <ContinuousColorLegend
              axisDirection="z"
              axisId="height"
              direction="vertical"
              thickness={18}
              labelPosition="end"
              minLabel={({ value }) => tickFormat(Number(value))}
              maxLabel={({ value }) => tickFormat(Number(value))}
              sx={{ flex: 1, color: t.inkSoft, fontSize: 14 }}
            />
          </Box>
          <Box
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerCancel={onPointerUp}
            sx={{ gridArea: "chart", cursor: "grab", touchAction: "none", "&:active": { cursor: "grabbing" } }}
          >
            <ChartsSurface>
              <SurfaceLayer scene={scene} />
            </ChartsSurface>
          </Box>
        </ChartsWrapper>
      </ChartsDataProvider>
    </Box>
  );
}
