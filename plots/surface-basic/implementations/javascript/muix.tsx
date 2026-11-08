// anyplot.ai
// surface-basic: Basic 3D Surface Plot
// Library: muix 9.17.0 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-09-10
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import { useXScale, useYScale, useZColorScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const VIEW_ANGLE = (25 * Math.PI) / 180; // tilt of the ground plane's axes below the horizontal
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
// HEIGHT_SHARE; an oblique projection maps (gx, gy, gz) to the plane, with the
// x = min, y = min corner at the back and the x = max, y = max corner in front
const COS = Math.cos(VIEW_ANGLE);
const SIN = Math.sin(VIEW_ANGLE);
const xMin = Math.min(...x);
const xMax = Math.max(...x);
const yMin = Math.min(...y);
const yMax = Math.max(...y);
const zMin = Math.min(...z.flat());
const zMax = Math.max(...z.flat());
const gxOf = x.map((v) => (v - xMin) / (xMax - xMin));
const gyOf = y.map((v) => (v - yMin) / (yMax - yMin));
const vertices = z.map((row, r) =>
  row.map((v, c) => ({
    px: (gxOf[c] - gyOf[r]) * COS,
    py: ((v - zMin) / (zMax - zMin)) * HEIGHT_SHARE - (gxOf[c] + gyOf[r]) * SIN,
  })),
);

// One quad per grid cell, colored by its mean height and painted back to front
const quads = vertices
  .slice(0, -1)
  .flatMap((row, r) =>
    row.slice(0, -1).map((_, c) => ({
      id: `${r}-${c}`,
      depth: gxOf[c] + gyOf[r],
      corners: [vertices[r][c], vertices[r][c + 1], vertices[r + 1][c + 1], vertices[r + 1][c]],
      height: (z[r][c] + z[r][c + 1] + z[r + 1][c + 1] + z[r + 1][c]) / 4,
    })),
  )
  .sort((a, b) => a.depth - b.depth);

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

// Frame anchors in ground coordinates: base corners, ticks on the two front edges and the
// z axis at the left corner, and the axis titles
const anchors = [
  ...[
    [0, 0],
    [1, 0],
    [1, 1],
    [0, 1],
  ].map(([gx, gy], i) => ({ kind: "base", key: `base-${i}`, value: 0, g: [gx, gy, 0] })),
  ...xTicks.map((v) => ({ kind: "x", key: `x-${v}`, value: v, g: [(v - xMin) / (xMax - xMin), 1, 0] })),
  ...yTicks.map((v) => ({ kind: "y", key: `y-${v}`, value: v, g: [1, (v - yMin) / (yMax - yMin), 0] })),
  ...zTicks.map((v) => ({ kind: "z", key: `z-${v}`, value: v, g: [0, 1, ((v - zMin) / (zMax - zMin)) * HEIGHT_SHARE] })),
  { kind: "zTop", key: "z-top", value: 0, g: [0, 1, HEIGHT_SHARE] },
  { kind: "xTitle", key: "x-title", value: 0, g: [0.5, 1, 0] },
  { kind: "yTitle", key: "y-title", value: 0, g: [1, 0.5, 0] },
].map((a) => ({ ...a, px: (a.g[0] - a.g[1]) * COS, py: a.g[2] - (a.g[0] + a.g[1]) * SIN }));
const base = anchors.filter((a) => a.kind === "base");
const xTickAnchors = anchors.filter((a) => a.kind === "x");
const yTickAnchors = anchors.filter((a) => a.kind === "y");
const zTickAnchors = anchors.filter((a) => a.kind === "z");
const zTop = anchors.find((a) => a.kind === "zTop")!;
const xTitle = anchors.find((a) => a.kind === "xTitle")!;
const yTitle = anchors.find((a) => a.kind === "yTitle")!;

const allPoints = [...vertices.flat(), ...anchors];
const pxLo = Math.min(...allPoints.map((p) => p.px));
const pxHi = Math.max(...allPoints.map((p) => p.px));
const pyLo = Math.min(...allPoints.map((p) => p.py));
const pyHi = Math.max(...allPoints.map((p) => p.py));
const tickFormat = (v: number) => Number(v.toFixed(2)).toString();

const TITLE = "surface-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${x.length} × ${y.length} grid · ${Z_NAME} from ${tickFormat(zMin)} to ${tickFormat(zMax)}`;
const textSx = { fontSize: 14, fill: t.inkSoft };
const titleText = { fontSize: 16, fontWeight: 600, fill: t.ink };

function SurfaceLayer() {
  const xScale = useXScale("iso-x");
  const yScale = useYScale("iso-y");
  const colorOf = useZColorScale("height");

  return (
    <g>
      <polygon
        points={base.map((p) => `${xScale(p.px)},${yScale(p.py)}`).join(" ")}
        fill="none"
        stroke={t.grid}
        strokeWidth={1.5}
      />
      {quads.map((q) => (
        <polygon
          key={q.id}
          points={q.corners.map((p) => `${xScale(p.px)},${yScale(p.py)}`).join(" ")}
          fill={colorOf?.(q.height) ?? t.seq[0]}
          stroke={t.pageBg}
          strokeOpacity={0.35}
          strokeWidth={0.6}
        />
      ))}
      <g stroke={t.inkSoft} strokeWidth={1.5}>
        <line x1={xScale(base[3].px)} y1={yScale(base[3].py)} x2={xScale(base[2].px)} y2={yScale(base[2].py)} />
        <line x1={xScale(base[1].px)} y1={yScale(base[1].py)} x2={xScale(base[2].px)} y2={yScale(base[2].py)} />
        <line x1={xScale(base[3].px)} y1={yScale(base[3].py)} x2={xScale(zTop.px)} y2={yScale(zTop.py)} />
      </g>
      {xTickAnchors.map((a) => (
        <g key={a.key}>
          <line
            x1={xScale(a.px)}
            y1={yScale(a.py)}
            x2={xScale(a.px) - TICK_PX * COS}
            y2={yScale(a.py) + TICK_PX * SIN}
            stroke={t.inkSoft}
            strokeWidth={1.5}
          />
          <text
            x={xScale(a.px) - TICK_LABEL_PX * COS}
            y={yScale(a.py) + TICK_LABEL_PX * SIN}
            textAnchor="end"
            dominantBaseline="hanging"
            {...textSx}
          >
            {tickFormat(a.value)}
          </text>
        </g>
      ))}
      {yTickAnchors.map((a) => (
        <g key={a.key}>
          <line
            x1={xScale(a.px)}
            y1={yScale(a.py)}
            x2={xScale(a.px) + TICK_PX * COS}
            y2={yScale(a.py) + TICK_PX * SIN}
            stroke={t.inkSoft}
            strokeWidth={1.5}
          />
          <text
            x={xScale(a.px) + TICK_LABEL_PX * COS}
            y={yScale(a.py) + TICK_LABEL_PX * SIN}
            textAnchor="start"
            dominantBaseline="hanging"
            {...textSx}
          >
            {tickFormat(a.value)}
          </text>
        </g>
      ))}
      {zTickAnchors.map((a) => (
        <g key={a.key}>
          <line x1={xScale(a.px)} y1={yScale(a.py)} x2={xScale(a.px) - TICK_PX} y2={yScale(a.py)} stroke={t.inkSoft} strokeWidth={1.5} />
          <text x={xScale(a.px) - TICK_LABEL_PX} y={yScale(a.py)} textAnchor="end" dominantBaseline="central" {...textSx}>
            {tickFormat(a.value)}
          </text>
        </g>
      ))}
      <text x={xScale(xTitle.px) - AXIS_TITLE_PX * COS} y={yScale(xTitle.py) + AXIS_TITLE_PX * SIN} textAnchor="end" dominantBaseline="hanging" {...titleText}>
        {X_NAME}
      </text>
      <text x={xScale(yTitle.px) + AXIS_TITLE_PX * COS} y={yScale(yTitle.py) + AXIS_TITLE_PX * SIN} textAnchor="start" dominantBaseline="hanging" {...titleText}>
        {Y_NAME}
      </text>
      <text x={xScale(zTop.px)} y={yScale(zTop.py) - 18} textAnchor="middle" {...titleText}>
        {Z_NAME}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartW = width - LEGEND_W;
  const chartH = height - HEADER_H;
  // equal px per unit on both axes keeps the projection's angles true; the chart takes
  // only the width the surface needs, so the colour bar sits right beside it
  const k = Math.min(
    (chartW - MARGIN.left - MARGIN.right) / (pxHi - pxLo),
    (chartH - MARGIN.top - MARGIN.bottom) / (pyHi - pyLo),
  );
  const drawW = k * (pxHi - pxLo);
  const drawH = chartH - MARGIN.top - MARGIN.bottom;
  const plotW = drawW + MARGIN.left + MARGIN.right;
  const pxMid = (pxLo + pxHi) / 2;
  const pyMid = (pyLo + pyHi) / 2;

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
          <ChartsSurface>
            <SurfaceLayer />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </Box>
  );
}
