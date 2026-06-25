// anyplot.ai
// contour-basic: Basic Contour Plot
// Library: muix 7.29.1 | JavaScript 22.23.0
// Quality: 76/100 | Created: 2026-06-25
//# anyplot-orientation: landscape
// anyplot.ai
// contour-basic: Basic Contour Plot
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-25

import { ScatterChart } from "@mui/x-charts/ScatterChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// --- Data: 2D elevation surface z = f(x, y) — two Gaussian peaks + ridge ----
// 60×60 = 3600 grid points for full coverage
const GRID = 60;

// Data range; axis auto-pads beyond ±3 so edge circles aren't clipped
const X0 = -3, X1 = 3, Y0 = -3, Y1 = 3;

function elevation(x, y) {
  const peak1 = Math.exp(-((x - 1) * (x - 1) + (y - 0.5) * (y - 0.5)) * 1.5);
  const peak2 = 0.75 * Math.exp(-((x + 1) * (x + 1) + (y + 1) * (y + 1)) * 2.0);
  const ridge = 0.35 * Math.exp(-(x - y) * (x - y) * 0.8) * 0.5;
  return peak1 + peak2 + ridge;
}

const allPoints = [];
for (let i = 0; i < GRID; i++) {
  for (let j = 0; j < GRID; j++) {
    const x = X0 + (i / (GRID - 1)) * (X1 - X0);
    const y = Y0 + (j / (GRID - 1)) * (Y1 - Y0);
    allPoints.push({ x, y, z: elevation(x, y) });
  }
}

const zMin = Math.min(...allPoints.map(p => p.z));
const zMax = Math.max(...allPoints.map(p => p.z));

// Imprint sequential colormap: brand green (#009E73) → blue (#4467A3)
function seqColor(frac) {
  const h1 = t.seq[0]; // #009E73
  const h2 = t.seq[1]; // #4467A3
  const cR = s => parseInt(s.slice(1, 3), 16);
  const cG = s => parseInt(s.slice(3, 5), 16);
  const cB = s => parseInt(s.slice(5, 7), 16);
  const lerp = (a, b, f) => Math.round(a + f * (b - a));
  const hex = n => n.toString(16).padStart(2, "0");
  return `#${hex(lerp(cR(h1), cR(h2), frac))}${hex(lerp(cG(h1), cG(h2), frac))}${hex(lerp(cB(h1), cB(h2), frac))}`;
}

// 6 filled contour bands — each is a ScatterChart series colored by elevation
const NUM_BANDS = 6;
const bandWidth = (zMax - zMin) / NUM_BANDS;

const series = Array.from({ length: NUM_BANDS }, (_, i) => {
  const lo = zMin + i * bandWidth;
  const hi = lo + bandWidth;
  const color = seqColor(i / (NUM_BANDS - 1));
  const data = allPoints
    .filter(p => (i === NUM_BANDS - 1 ? p.z >= lo && p.z <= hi : p.z >= lo && p.z < hi))
    .map((p, k) => ({ x: p.x, y: p.y, id: `${i}_${k}` }));
  return {
    data,
    label: `${lo.toFixed(2)} – ${hi.toFixed(2)}`,
    color,
    markerSize: 15, // radius large enough to fill diagonal gaps in a non-square plot area
  };
});

const TITLE = "contour-basic · javascript · muix · anyplot.ai";

// --- Chart ------------------------------------------------------------------
export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;

  return (
    <Box
      sx={{
        width: W,
        height: H,
        display: "flex",
        flexDirection: "column",
        bgcolor: t.pageBg,
        boxSizing: "border-box",
        pt: "28px",
        px: "32px",
        pb: "8px",
      }}
    >
      <Typography
        component="div"
        sx={{
          fontSize: 22,
          fontWeight: 500,
          color: t.ink,
          textAlign: "center",
          lineHeight: 1.3,
          mb: "6px",
          flexShrink: 0,
        }}
      >
        {TITLE}
      </Typography>
      <ScatterChart
        width={W - 64}
        height={H - 28 - 36 - 8}
        skipAnimation
        tooltip={{ trigger: "none" }}
        series={series}
        xAxis={[{
          label: "X",
          tickMinStep: 1,
          labelStyle: { fontSize: 15, fill: t.ink },
          tickLabelStyle: { fontSize: 13, fill: t.inkSoft },
        }]}
        yAxis={[{
          label: "Y",
          tickMinStep: 1,
          labelStyle: { fontSize: 15, fill: t.ink },
          tickLabelStyle: { fontSize: 13, fill: t.inkSoft },
        }]}
        margin={{ left: 65, right: 200, top: 12, bottom: 58 }}
        slotProps={{
          legend: {
            direction: "column",
            position: { vertical: "middle", horizontal: "right" },
            itemMarkWidth: 14,
            itemMarkHeight: 14,
            labelStyle: { fontSize: 13, fill: t.inkSoft },
          },
        }}
      />
    </Box>
  );
}
