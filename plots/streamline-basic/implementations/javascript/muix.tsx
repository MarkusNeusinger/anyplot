// anyplot.ai
// streamline-basic: Basic Streamline Plot
// Library: muix 9.17.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-09
import { ChartsDataProvider } from "@mui/x-charts/ChartsDataProvider";
import { ChartsSurface } from "@mui/x-charts/ChartsSurface";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ContinuousColorLegend } from "@mui/x-charts/ChartsLegend";
import { useXScale, useYScale, useZAxis } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const MASK_CELLS_X = 26; // streamline spacing: one line per mask cell across the x range
const STEP_SHARE = 0.2; // integration step as a share of a grid cell
const MAX_STEPS = 1500; // steps per direction from a seed
const MIN_POINTS = 22; // shorter traces are dropped, so no isolated dashes stay behind
const SEGMENT_POINTS = 6; // points per coloured piece of a line
const COHERENT_COS = 0.7; // a cell whose corner directions spread wider than ~45° holds a source, sink or singular point
const COLOR_QUANTITY = "log₁₀ magnitude"; // what the colour of a line encodes, for any (u, v) field

// Columns: set these to your data's column names
const X = "x (normalized distance)"; // role: x
const Y = "y (normalized distance)"; // role: y
const U = "Ex (normalized field)"; // role: u
const V = "Ey (normalized field)"; // role: v

// Data: replace this block with your own records, one object per row
// Electric field of a dipole (a positive and a negative unit charge on the x axis),
// sampled on a 36 x 20 grid; one row per grid point
const data = (() => {
  const charges = [
    { x: -1.1, y: 0, q: 1 },
    { x: 1.1, y: 0, q: -1 },
  ];
  const rows: Record<string, number>[] = [];
  for (let j = 0; j < 20; j += 1) {
    for (let i = 0; i < 36; i += 1) {
      const x = -4.5 + (i * 9) / 35;
      const y = -2.5 + (j * 5) / 19;
      let ex = 0;
      let ey = 0;
      for (const c of charges) {
        const r3 = Math.hypot(x - c.x, y - c.y) ** 3;
        ex += (c.q * (x - c.x)) / r3;
        ey += (c.q * (y - c.y)) / r3;
      }
      rows.push({
        [X]: Number(x.toFixed(4)),
        [Y]: Number(y.toFixed(4)),
        [U]: Number(ex.toFixed(5)),
        [V]: Number(ey.toFixed(5)),
      });
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
// The long grid table becomes U and V matrices on the sorted unique x and y values
const gx = [...new Set(data.map((d) => d[X]))].sort((a, b) => a - b);
const gy = [...new Set(data.map((d) => d[Y]))].sort((a, b) => a - b);
const nx = gx.length;
const ny = gy.length;
const colOf = new Map(gx.map((v, i) => [v, i]));
const rowOf = new Map(gy.map((v, j) => [v, j]));
const Ugrid = gy.map(() => new Array(nx).fill(NaN));
const Vgrid = gy.map(() => new Array(nx).fill(NaN));
for (const d of data) {
  Ugrid[rowOf.get(d[Y]) as number][colOf.get(d[X]) as number] = d[U];
  Vgrid[rowOf.get(d[Y]) as number][colOf.get(d[X]) as number] = d[V];
}
const xMin = gx[0];
const xMax = gx[nx - 1];
const yMin = gy[0];
const yMax = gy[ny - 1];
const cellX = (xMax - xMin) / (nx - 1);
const cellY = (yMax - yMin) / (ny - 1);
const step = STEP_SHARE * Math.min(cellX, cellY);

// Cells where the field direction is coherent; lines stop before entering any other cell
const coherent = Array.from({ length: ny - 1 }, (_, j) =>
  Array.from({ length: nx - 1 }, (_, i) => {
    const corners = [
      [Ugrid[j][i], Vgrid[j][i]],
      [Ugrid[j][i + 1], Vgrid[j][i + 1]],
      [Ugrid[j + 1][i], Vgrid[j + 1][i]],
      [Ugrid[j + 1][i + 1], Vgrid[j + 1][i + 1]],
    ].map(([u, v]) => [u / Math.hypot(u, v), v / Math.hypot(u, v)]);
    const mx = corners.reduce((acc, c) => acc + c[0], 0);
    const my = corners.reduce((acc, c) => acc + c[1], 0);
    const mLen = Math.hypot(mx, my);
    return corners.every((c) => (c[0] * mx + c[1] * my) / mLen >= COHERENT_COS);
  }),
);

// Streamlines, as in a streamplot: seeds from the border inward, each traced both ways along the
// unit field direction (midpoint rule on the bilinear field), stopping at the edge, at a reversal
// (a source or sink), or where it enters a mask cell another line already holds
const maskNx = MASK_CELLS_X;
const maskNy = Math.max(2, Math.round((MASK_CELLS_X * (yMax - yMin)) / (xMax - xMin)));
const maskW = (xMax - xMin) / maskNx;
const maskH = (yMax - yMin) / maskNy;
const occupied = new Uint8Array(maskNx * maskNy);
const ring = Array.from({ length: maskNx * maskNy }, (_, k) =>
  Math.min(k % maskNx, maskNx - 1 - (k % maskNx), Math.floor(k / maskNx), maskNy - 1 - Math.floor(k / maskNx)),
);
const seeds = ring.map((_, k) => k).sort((a, b) => ring[a] - ring[b] || a - b);
const lines: { x: number; y: number; s: number }[][] = [];
for (const seed of seeds) {
  if (occupied[seed]) continue;
  occupied[seed] = 1;
  const claimed = [seed];
  const halves: { x: number; y: number; s: number }[][] = [];
  for (const sign of [1, -1]) {
    const pts: { x: number; y: number; s: number }[] = [];
    let px = xMin + ((seed % maskNx) + 0.5) * maskW;
    let py = yMin + (Math.floor(seed / maskNx) + 0.5) * maskH;
    let qx = px;
    let qy = py;
    let midStage = false;
    let prevDx = 0;
    let prevDy = 0;
    let cell = seed;
    for (let n = 0; n < 2 * MAX_STEPS; n += 1) {
      const fi = (qx - xMin) / cellX;
      const fj = (qy - yMin) / cellY;
      const i0 = Math.min(Math.max(Math.floor(fi), 0), nx - 2);
      const j0 = Math.min(Math.max(Math.floor(fj), 0), ny - 2);
      const ax = fi - i0;
      const ay = fj - j0;
      const fu =
        Ugrid[j0][i0] * (1 - ax) * (1 - ay) + Ugrid[j0][i0 + 1] * ax * (1 - ay) +
        Ugrid[j0 + 1][i0] * (1 - ax) * ay + Ugrid[j0 + 1][i0 + 1] * ax * ay;
      const fv =
        Vgrid[j0][i0] * (1 - ax) * (1 - ay) + Vgrid[j0][i0 + 1] * ax * (1 - ay) +
        Vgrid[j0 + 1][i0] * (1 - ax) * ay + Vgrid[j0 + 1][i0 + 1] * ax * ay;
      const mag = Math.hypot(fu, fv);
      if (!(mag > 0) || !coherent[j0][i0]) break;
      const dx = (sign * fu) / mag;
      const dy = (sign * fv) / mag;
      if (!midStage) {
        if (pts.length > 0 && dx * prevDx + dy * prevDy < 0) break;
        pts.push({ x: px, y: py, s: Math.log10(mag) });
        prevDx = dx;
        prevDy = dy;
        qx = px + (step / 2) * dx;
        qy = py + (step / 2) * dy;
        midStage = true;
      } else {
        px += step * dx;
        py += step * dy;
        qx = px;
        qy = py;
        midStage = false;
        if (px < xMin || px > xMax || py < yMin || py > yMax) break;
        const c =
          Math.min(maskNy - 1, Math.floor((py - yMin) / maskH)) * maskNx + Math.min(maskNx - 1, Math.floor((px - xMin) / maskW));
        if (c !== cell) {
          if (occupied[c]) break;
          occupied[c] = 1;
          claimed.push(c);
          cell = c;
        }
      }
    }
    halves.push(pts);
  }
  const line = [...halves[1].slice(1).reverse(), ...halves[0]];
  if (line.length < MIN_POINTS) {
    for (const c of claimed) occupied[c] = 0;
    continue;
  }
  lines.push(line);
}
const logSpeeds = lines.flatMap((l) => l.map((p) => p.s));
const speedMin = Math.min(...logSpeeds);
const speedMax = Math.max(...logSpeeds);

const TITLE = "streamline-basic · javascript · muix · anyplot.ai";
const [uName, vName] = [U, V].map((name) => name.replace(/\s*\([^)]*\)/, ""));
const fieldUnit = U.match(/\(([^)]+)\)/)?.[1];
const SUBTITLE = `${lines.length} streamlines traced through a ${nx} × ${ny} grid of (${uName}, ${vName})${fieldUnit ? `, ${fieldUnit}` : ""}`;
const HEADER_H = 76;
const LEGEND_H = 44;
const X_BAND = 64;
const Y_BAND = 72;

// Each streamline in short pieces coloured by the field magnitude, with one arrow at its middle
function Streamlines() {
  const xs = useXScale() as (v: number) => number;
  const ys = useYScale() as (v: number) => number;
  const colorScale = useZAxis("speed").colorScale as (v: number) => string;
  return (
    <g fill="none" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
      {lines.map((line, li) => {
        const pieces = [];
        for (let k = 0; k < line.length - 1; k += SEGMENT_POINTS) {
          const piece = line.slice(k, k + SEGMENT_POINTS + 1);
          const meanS = piece.reduce((acc, p) => acc + p.s, 0) / piece.length;
          pieces.push(
            <path
              key={`${li}-${k}`}
              d={`M${piece.map((p) => `${xs(p.x)} ${ys(p.y)}`).join(" L")}`}
              stroke={colorScale(meanS)}
            />,
          );
        }
        const mid = Math.floor(line.length / 2);
        const ax = xs(line[mid].x);
        const ay = ys(line[mid].y);
        const angle = Math.atan2(ys(line[mid + 1].y) - ay, xs(line[mid + 1].x) - ax);
        const arrow = [
          [ax + 10 * Math.cos(angle), ay + 10 * Math.sin(angle)],
          [ax + 8 * Math.cos(angle + Math.PI - 0.5), ay + 8 * Math.sin(angle + Math.PI - 0.5)],
          [ax + 8 * Math.cos(angle + Math.PI + 0.5), ay + 8 * Math.sin(angle + Math.PI + 0.5)],
        ]
          .map((p) => p.join(","))
          .join(" ");
        return (
          <g key={`line-${li}`}>
            {pieces}
            <polygon points={arrow} fill={colorScale(line[mid].s)} stroke="none" />
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width: W, height: H } = window.ANYPLOT_SIZE;
  const chartH = H - HEADER_H - LEGEND_H;
  // One unit of x and of y take the same number of pixels, so the field keeps its geometry
  const availW = W - Y_BAND - 64;
  const availH = chartH - X_BAND - 24;
  const pxPerUnit = Math.min(availW / (xMax - xMin), availH / (yMax - yMin));
  const drawW = pxPerUnit * (xMax - xMin);
  const drawH = pxPerUnit * (yMax - yMin);
  const left = (W - Y_BAND - drawW) / 2;
  const top = (chartH - X_BAND - drawH) / 2;

  return (
    <div style={{ width: W, height: H, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div
        style={{
          height: HEADER_H,
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
        width={W}
        height={chartH}
        skipAnimation
        margin={{ top, bottom: top, left, right: left }}
        series={[]}
        xAxis={[
          {
            id: "x",
            scaleType: "linear",
            min: xMin,
            max: xMax,
            label: X,
            height: X_BAND,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "y",
            scaleType: "linear",
            min: yMin,
            max: yMax,
            label: Y,
            width: Y_BAND,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        zAxis={[
          {
            id: "speed",
            colorMap: { type: "continuous", min: speedMin, max: speedMax, color: [t.seq[0], t.seq[1]] },
          },
        ]}
      >
        <div
          style={{
            height: LEGEND_H,
            display: "flex",
            alignItems: "center",
            justifyContent: "flex-end",
            gap: 14,
            paddingRight: left,
            color: t.inkSoft,
            fontSize: 15,
          }}
        >
          <span>{COLOR_QUANTITY}</span>
          <ContinuousColorLegend
            axisDirection="z"
            axisId="speed"
            direction="horizontal"
            thickness={14}
            labelPosition="end"
            minLabel={({ value }) => (value as number).toFixed(1)}
            maxLabel={({ value }) => (value as number).toFixed(1)}
            sx={{ width: 280, fontSize: 14, color: t.inkSoft }}
          />
        </div>
        <ChartsSurface
          sx={{
            "& .MuiChartsAxis-line": { stroke: t.inkSoft },
            "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
            "& .MuiChartsGrid-line": { stroke: t.grid },
          }}
        >
          <ChartsGrid horizontal vertical />
          <Streamlines />
          <ChartsXAxis />
          <ChartsYAxis />
        </ChartsSurface>
      </ChartsDataProvider>
    </div>
  );
}
