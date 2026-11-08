// anyplot.ai
// contour-density: Density Contour Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 93/100 | Created: 2026-09-04
//# anyplot-orientation: square
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const LEVEL_FRACTIONS = [0.12, 0.28, 0.46, 0.65, 0.85]; // contour levels as shares of the peak density
const GRID_STEPS = 70; // density grid nodes per axis
const PAD_SHARE = 0.12; // plot extent beyond the points, as a share of each variable's range
const SILVERMAN = 1.06; // Silverman's rule of thumb: h = 1.06 · sd · n^(-1/5) per axis

// Columns: set these to your data's column names
const DIAMETER = "Outer diameter (mm)"; // role: x
const WEIGHT = "Weight (g)"; // role: y

// Data: replace this block with your own records, one object per part
// Bearing quality control: 900 parts from an on-spec batch and 500 from a batch that drifted high on
// both dimensions, diameter and weight correlated within each batch
const data = (() => {
  let state = 42;
  const rand = () => {
    state = (1664525 * state + 1013904223) >>> 0;
    return state / 4294967296;
  };
  const normal = () => Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-9))) * Math.cos(2 * Math.PI * rand());
  const batches = [
    { n: 900, meanDiameter: 23.92, sdDiameter: 0.13, meanWeight: 45.6, sdWeight: 0.7, rho: 0.5 },
    { n: 500, meanDiameter: 24.58, sdDiameter: 0.12, meanWeight: 48.4, sdWeight: 0.65, rho: 0.45 },
  ];
  return batches.flatMap((b) =>
    Array.from({ length: b.n }, () => {
      const z1 = normal();
      const z2 = normal();
      return {
        [DIAMETER]: b.meanDiameter + b.sdDiameter * z1,
        [WEIGHT]: b.meanWeight + b.sdWeight * (b.rho * z1 + Math.sqrt(1 - b.rho * b.rho) * z2),
      };
    }),
  );
})();

// Plot: reads only data and the constants above
const points = data
  .filter((d) => Number.isFinite(d[DIAMETER]) && Number.isFinite(d[WEIGHT]))
  .map((d, i) => ({ id: i, x: d[DIAMETER], y: d[WEIGHT] }));
const n = points.length;

// Per axis: padded extent and the Silverman bandwidth of a Gaussian kernel
const [xAxisStats, yAxisStats] = [points.map((p) => p.x), points.map((p) => p.y)].map((values) => {
  const low = Math.min(...values);
  const high = Math.max(...values);
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const sd = Math.sqrt(values.reduce((a, b) => a + (b - mean) ** 2, 0) / (values.length - 1));
  const pad = (high - low) * PAD_SHARE;
  return { min: low - pad, max: high + pad, bandwidth: SILVERMAN * sd * values.length ** (-1 / 5) };
});

// Kernel density estimate on a regular grid, density[j][i] at (gridX[i], gridY[j])
const gridX = Array.from({ length: GRID_STEPS }, (_, i) => xAxisStats.min + (i / (GRID_STEPS - 1)) * (xAxisStats.max - xAxisStats.min));
const gridY = Array.from({ length: GRID_STEPS }, (_, j) => yAxisStats.min + (j / (GRID_STEPS - 1)) * (yAxisStats.max - yAxisStats.min));
const density = gridY.map((gy) =>
  gridX.map((gx) => {
    let sum = 0;
    points.forEach((p) => {
      const dx = (gx - p.x) / xAxisStats.bandwidth;
      const dy = (gy - p.y) / yAxisStats.bandwidth;
      sum += Math.exp(-0.5 * (dx * dx + dy * dy));
    });
    return sum / (2 * Math.PI * n * xAxisStats.bandwidth * yAxisStats.bandwidth);
  }),
);
const peakDensity = Math.max(...density.flat());

// Marching triangles: each grid cell splits into four triangles around its centre, which resolves
// saddles; per level, the segment where the density crosses it inside every triangle
const triangles: { x: number; y: number; z: number }[][] = [];
for (let j = 0; j < GRID_STEPS - 1; j += 1) {
  for (let i = 0; i < GRID_STEPS - 1; i += 1) {
    const [sw, se, ne, nw] = [
      [i, j],
      [i + 1, j],
      [i + 1, j + 1],
      [i, j + 1],
    ].map(([ii, jj]) => ({ x: gridX[ii], y: gridY[jj], z: density[jj][ii] }));
    const centre = { x: (sw.x + se.x) / 2, y: (sw.y + nw.y) / 2, z: (sw.z + se.z + ne.z + nw.z) / 4 };
    triangles.push([sw, se, centre], [se, ne, centre], [ne, nw, centre], [nw, sw, centre]);
  }
}
const contours = LEVEL_FRACTIONS.map((fraction, k) => {
  const level = fraction * peakDensity;
  const segments: { x: number; y: number }[][] = [];
  triangles.forEach((tri) => {
    const inside = tri.map((p) => p.z >= level);
    if (inside.every(Boolean) || !inside.some(Boolean)) return;
    const segment: { x: number; y: number }[] = [];
    tri.forEach((p, m) => {
      const q = tri[(m + 1) % 3];
      if (inside[m] !== inside[(m + 1) % 3]) {
        const r = (level - p.z) / (q.z - p.z);
        segment.push({ x: p.x + r * (q.x - p.x), y: p.y + r * (q.y - p.y) });
      }
    });
    segments.push(segment);
  });
  // Sequential Imprint ramp t.seq[0] -> t.seq[1]: the strongest colour marks the highest density
  const share = k / (LEVEL_FRACTIONS.length - 1);
  const [low, high] = t.seq.map((hex: string) => [16, 8, 0].map((shift) => (parseInt(hex.slice(1), 16) >> shift) & 255));
  const color = `rgb(${low.map((c: number, ch: number) => Math.round(c + (high[ch] - c) * share)).join(", ")})`;
  return { fraction, segments, color, strokeWidth: 2.5 + k * 0.7 };
});

const TITLE = "Bearing QC · contour-density · javascript · muix · anyplot.ai";
const subtitle = `n = ${n.toLocaleString("en-US")} · Gaussian KDE, Silverman bandwidths ${xAxisStats.bandwidth.toFixed(3)} and ${yAxisStats.bandwidth.toFixed(2)} · ${GRID_STEPS} × ${GRID_STEPS} grid`;
const HEADER_H = 92;
const LEGEND_W = 190;

function ContourLines() {
  const xScale = useXScale();
  const yScale = useYScale();
  return (
    <g>
      {contours.map((c) => (
        <path
          key={c.fraction}
          d={c.segments.map(([a, b]) => `M${xScale(a.x)!.toFixed(1)},${yScale(a.y)!.toFixed(1)}L${xScale(b.x)!.toFixed(1)},${yScale(b.y)!.toFixed(1)}`).join("")}
          fill="none"
          stroke={c.color}
          strokeWidth={c.strokeWidth}
          strokeOpacity={0.92}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column" }}>
      <Box sx={{ height: HEADER_H, display: "flex", flexDirection: "column", justifyContent: "center", gap: "6px", px: "40px", pt: "8px" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.3 }}>{subtitle}</Typography>
      </Box>
      <Box sx={{ display: "flex", flexDirection: "row" }}>
        <ScatterChart
          width={width - LEGEND_W}
          height={height - HEADER_H}
          skipAnimation
          hideLegend
          disableVoronoi
          grid={{ horizontal: true, vertical: true }}
          margin={{ top: 20, right: 24, bottom: 24, left: 24 }}
          series={[{ id: "parts", type: "scatter", data: points, color: t.inkSoft, markerSize: 3 }]}
          xAxis={[
            {
              scaleType: "linear",
              min: xAxisStats.min,
              max: xAxisStats.max,
              label: DIAMETER,
              height: 60,
              labelStyle: { fontSize: 16, fill: t.ink },
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            },
          ]}
          yAxis={[
            {
              scaleType: "linear",
              min: yAxisStats.min,
              max: yAxisStats.max,
              label: WEIGHT,
              width: 72,
              labelStyle: { fontSize: 16, fill: t.ink },
              tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            },
          ]}
          sx={{
            "& .MuiScatterChart-marker": { fillOpacity: 0.3 },
            "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
            "& .MuiChartsAxis-line": { stroke: t.inkSoft },
            "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          }}
        >
          <ContourLines />
        </ScatterChart>
        <Box sx={{ width: LEGEND_W, display: "flex", flexDirection: "column", justifyContent: "center", gap: "10px", pl: "12px" }}>
          <Typography sx={{ fontSize: 15, fontWeight: 600, color: t.ink, lineHeight: 1.3 }}>Density contours</Typography>
          {[...contours].reverse().map((c) => (
            <Box key={c.fraction} sx={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <Box sx={{ width: 26, height: `${c.strokeWidth}px`, borderRadius: "3px", bgcolor: c.color, flexShrink: 0 }} />
              <Typography sx={{ fontSize: 14, color: t.inkSoft }}>{`${Math.round(c.fraction * 100)} % of peak`}</Typography>
            </Box>
          ))}
        </Box>
      </Box>
    </Box>
  );
}
