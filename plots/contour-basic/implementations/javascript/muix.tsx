// anyplot.ai
// contour-basic: Basic Contour Plot
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 85/100 | Updated: 2026-11-08
//# anyplot-orientation: square
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { PiecewiseColorLegend } from "@mui/x-charts/ChartsLegend";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsWrapper } from "@mui/x-charts/ChartsWrapper";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale, useZColorScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const LEVEL_COUNT = 9; // filled bands between the field's minimum and maximum, evenly stepped
const ISOLINE_INK = "#1A1A17"; // fixed ink: the bands keep their colours in both themes

// Columns: set these to your data's column names
const EASTING = "Easting (km)"; // role: x
const NORTHING = "Northing (km)"; // role: y
const ELEVATION = "Elevation (km)"; // role: z

// Data: replace this block with your own records, one object per grid point
// Terrain of a 6 × 6 km survey square: two summits joined by a low diagonal ridge, sampled on a 60 × 60 grid
const data = (() => {
  const gridSize = 60;
  const halfSpan = 3;
  const rows: Record<string, number>[] = [];
  for (let j = 0; j < gridSize; j += 1) {
    const y = -halfSpan + (2 * halfSpan * j) / (gridSize - 1);
    for (let i = 0; i < gridSize; i += 1) {
      const x = -halfSpan + (2 * halfSpan * i) / (gridSize - 1);
      const northSummit = Math.exp(-((x - 1) ** 2 + (y - 0.5) ** 2) * 1.5);
      const southSummit = 0.75 * Math.exp(-((x + 1) ** 2 + (y + 1) ** 2) * 2.0);
      const ridge = 0.175 * Math.exp(-((x - y) ** 2) * 0.8);
      rows.push({ [EASTING]: x, [NORTHING]: y, [ELEVATION]: northSummit + southSummit + ridge });
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
// Regular grid rebuilt from the records: sorted coordinates, z indexed as zGrid[row][column]
const xs = [...new Set(data.map((d) => d[EASTING]))].sort((a, b) => a - b);
const ys = [...new Set(data.map((d) => d[NORTHING]))].sort((a, b) => a - b);
const xIndex = new Map(xs.map((v, i) => [v, i]));
const yIndex = new Map(ys.map((v, j) => [v, j]));
const zGrid = ys.map(() => xs.map(() => NaN));
data.forEach((d) => {
  zGrid[yIndex.get(d[NORTHING])!][xIndex.get(d[EASTING])!] = d[ELEVATION];
});
const zValues = data.map((d) => d[ELEVATION]).filter((v) => Number.isFinite(v));
const zMin = Math.min(...zValues);
const zMax = Math.max(...zValues);
const levelStep = (zMax - zMin) / LEVEL_COUNT;
const levels = Array.from({ length: LEVEL_COUNT }, (_, k) => zMin + k * levelStep);
const thresholds = levels.slice(1);

// Sequential Imprint ramp t.seq[0] -> t.seq[1], one step per band
const [seqLow, seqHigh] = t.seq.map((hex: string) => [16, 8, 0].map((shift) => (parseInt(hex.slice(1), 16) >> shift) & 255));
const bandColors = levels.map(
  (_, k) => `rgb(${seqLow.map((c: number, ch: number) => Math.round(c + ((seqHigh[ch] - c) * k) / (LEVEL_COUNT - 1))).join(", ")})`,
);

// Marching triangles: each grid cell splits into four triangles around its centre, which resolves
// saddles; per level, the part of every triangle at or above the level and the cut along the level
type Pt = { x: number; y: number; z: number };
const triangles: Pt[][] = [];
for (let j = 0; j < ys.length - 1; j += 1) {
  for (let i = 0; i < xs.length - 1; i += 1) {
    const sw = { x: xs[i], y: ys[j], z: zGrid[j][i] };
    const se = { x: xs[i + 1], y: ys[j], z: zGrid[j][i + 1] };
    const ne = { x: xs[i + 1], y: ys[j + 1], z: zGrid[j + 1][i + 1] };
    const nw = { x: xs[i], y: ys[j + 1], z: zGrid[j + 1][i] };
    const centre = { x: (sw.x + se.x) / 2, y: (sw.y + nw.y) / 2, z: (sw.z + se.z + ne.z + nw.z) / 4 };
    [[sw, se], [se, ne], [ne, nw], [nw, sw]].forEach(([a, b]) => {
      if ([a.z, b.z, centre.z].every((z) => Number.isFinite(z))) triangles.push([a, b, centre]);
    });
  }
}
const bandPolygons: { x: number; y: number }[][][] = [];
const isolines: { x: number; y: number }[][][] = [];
levels.forEach((level) => {
  const polys: { x: number; y: number }[][] = [];
  const cuts: { x: number; y: number }[][] = [];
  triangles.forEach((tri) => {
    const inside = tri.map((p) => p.z >= level);
    const count = inside.filter(Boolean).length;
    if (count === 0) return;
    if (count === 3) {
      polys.push(tri);
      return;
    }
    // Walk the three edges; keep inside vertices and the level crossing on every edge that changes side
    const ring: { x: number; y: number }[] = [];
    const cut: { x: number; y: number }[] = [];
    tri.forEach((p, k) => {
      const q = tri[(k + 1) % 3];
      if (inside[k]) ring.push(p);
      if (inside[k] !== inside[(k + 1) % 3]) {
        const r = (level - p.z) / (q.z - p.z);
        const crossing = { x: p.x + r * (q.x - p.x), y: p.y + r * (q.y - p.y) };
        ring.push(crossing);
        cut.push(crossing);
      }
    });
    polys.push(ring);
    cuts.push(cut);
  });
  bandPolygons.push(polys);
  isolines.push(cuts);
});

// Layout: equal px per km on both axes, the map centred with its colour bar beside it
const { width: W, height: H } = window.ANYPLOT_SIZE;
const HEADER_H = 84;
const X_AXIS_H = 60;
const Y_AXIS_W = 72;
const MARGIN = { top: 16, bottom: 20, left: 24, right: 48 };
const LEGEND_W = 170;
const xSpan = xs[xs.length - 1] - xs[0];
const ySpan = ys[ys.length - 1] - ys[0];
const plotH = Math.min(H - HEADER_H - X_AXIS_H - MARGIN.top - MARGIN.bottom, ((W - LEGEND_W - Y_AXIS_W - MARGIN.left - MARGIN.right) * ySpan) / xSpan);
const plotW = (plotH * xSpan) / ySpan;
const surfaceW = MARGIN.left + Y_AXIS_W + plotW + MARGIN.right;
const surfaceH = MARGIN.top + plotH + X_AXIS_H + MARGIN.bottom;

const TITLE = "Survey Terrain · contour-basic · javascript · muix · anyplot.ai";
const subtitle = `${xs.length} × ${ys.length} grid points · ${LEVEL_COUNT} levels evenly stepped by ${levelStep.toFixed(2)}`;

function ContourLayer() {
  const xScale = useXScale();
  const yScale = useYScale();
  // Band fills come from the zAxis piecewise colorMap, the same scale the colour bar reads
  const colorScale = useZColorScale()!;
  const toPath = (shapes: { x: number; y: number }[][], close: boolean) =>
    shapes
      .map((shape) => shape.map((p, k) => `${k === 0 ? "M" : "L"}${xScale(p.x)!.toFixed(1)},${yScale(p.y)!.toFixed(1)}`).join("") + (close ? "Z" : ""))
      .join("");
  return (
    <g>
      {bandPolygons.map((polys, k) => {
        const fill = String(colorScale(levels[k] + levelStep / 2));
        return <path key={`band-${k}`} d={toPath(polys, true)} fill={fill} stroke={fill} strokeWidth={0.75} />;
      })}
      {isolines.map((cuts, k) => (
        <path key={`iso-${k}`} d={toPath(cuts, false)} fill="none" stroke={ISOLINE_INK} strokeOpacity={0.6} strokeWidth={1.5} />
      ))}
    </g>
  );
}

export default function Chart() {
  return (
    <Box sx={{ width: W, height: H, bgcolor: t.pageBg, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <Box sx={{ height: HEADER_H, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "6px", pt: "8px" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2 }}>{subtitle}</Typography>
      </Box>
      <ChartsDataProvider
        width={surfaceW}
        height={surfaceH}
        series={[]}
        skipAnimation
        margin={MARGIN}
        xAxis={[
          {
            id: "x",
            scaleType: "linear",
            min: xs[0],
            max: xs[xs.length - 1],
            label: EASTING,
            height: X_AXIS_H,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "y",
            scaleType: "linear",
            min: ys[0],
            max: ys[ys.length - 1],
            label: NORTHING,
            width: Y_AXIS_W,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        zAxis={[{ id: "z", colorMap: { type: "piecewise", thresholds, colors: bandColors } }]}
      >
        <ChartsWrapper
          legendPosition={{ vertical: "middle", horizontal: "end" }}
          legendDirection="vertical"
          sx={{ width: surfaceW + LEGEND_W, height: surfaceH }}
        >
          <Box sx={{ gridArea: "legend", width: LEGEND_W, display: "flex", flexDirection: "column", alignItems: "flex-start", gap: "10px" }}>
            <Typography sx={{ fontSize: 16, fontWeight: 500, color: t.ink }}>{ELEVATION}</Typography>
            <PiecewiseColorLegend
              axisDirection="z"
              axisId="z"
              direction="vertical"
              labelPosition="inline-end"
              markType="square"
              labelFormatter={({ min, max }) => `${Number(min ?? zMin).toFixed(2)} – ${Number(max ?? zMax).toFixed(2)}`}
              sx={{ fontSize: 14, color: t.inkSoft, gap: "6px" }}
            />
          </Box>
          <ChartsSurface
            sx={{
              "& .MuiChartsAxis-line": { stroke: t.inkSoft },
              "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
            }}
          >
            <ContourLayer />
            <ChartsXAxis axisId="x" />
            <ChartsYAxis axisId="y" />
          </ChartsSurface>
        </ChartsWrapper>
      </ChartsDataProvider>
    </Box>
  );
}
