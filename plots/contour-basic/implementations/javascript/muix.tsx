// anyplot.ai
// contour-basic: Basic Contour Plot
// Library: muix 7.29.1 | JavaScript 22.23.0
// Quality: 84/100 | Created: 2026-06-25
//# anyplot-orientation: landscape
// anyplot.ai
// contour-basic: Basic Contour Plot
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-25

import { ScatterChart } from "@mui/x-charts/ScatterChart";
import { useDrawingArea } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// --- Grid setup ------------------------------------------------------------
const GRID = 60;
const X_MIN = -3, X_MAX = 3, Y_MIN = -3, Y_MAX = 3;

const xs = Array.from({ length: GRID }, (_, i) => X_MIN + (i / (GRID - 1)) * (X_MAX - X_MIN));
const ys = Array.from({ length: GRID }, (_, j) => Y_MIN + (j / (GRID - 1)) * (Y_MAX - Y_MIN));

// --- Elevation: two Gaussian peaks + ridge ---------------------------------
function elevation(x, y) {
  const peak1 = Math.exp(-((x - 1) * (x - 1) + (y - 0.5) * (y - 0.5)) * 1.5);
  const peak2 = 0.75 * Math.exp(-((x + 1) * (x + 1) + (y + 1) * (y + 1)) * 2.0);
  const ridge = 0.175 * Math.exp(-(x - y) * (x - y) * 0.8);
  return peak1 + peak2 + ridge;
}

// zGrid[j][i] = z at (xs[i], ys[j])
const zGrid = ys.map(y => xs.map(x => elevation(x, y)));
const allZ = zGrid.flat();
const zMin = Math.min(...allZ);
const zMax = Math.max(...allZ);

// --- Imprint sequential colormap: t.seq[0] → t.seq[1] --------------------
function seqColor(frac) {
  const h1 = t.seq[0], h2 = t.seq[1];
  const chan = (s, o) => parseInt(s.slice(o, o + 2), 16);
  const lerp = (a, b) => Math.round(a + frac * (b - a));
  const hex = n => n.toString(16).padStart(2, "0");
  return `#${hex(lerp(chan(h1, 1), chan(h2, 1)))}${hex(lerp(chan(h1, 3), chan(h2, 3)))}${hex(lerp(chan(h1, 5), chan(h2, 5)))}`;
}

// --- Filled contour bands via scatter proxy --------------------------------
const NUM_BANDS = 6;
const bandW = (zMax - zMin) / NUM_BANDS;

const allPoints = xs.flatMap((x, i) => ys.map((y, j) => ({ x, y, z: zGrid[j][i] })));

const scatterSeries = Array.from({ length: NUM_BANDS }, (_, b) => {
  const lo = zMin + b * bandW;
  const hi = lo + bandW;
  const isLast = b === NUM_BANDS - 1;
  return {
    data: allPoints
      .filter(p => isLast ? p.z >= lo && p.z <= hi : p.z >= lo && p.z < hi)
      .map((p, k) => ({ x: p.x, y: p.y, id: `${b}_${k}` })),
    label: `${lo.toFixed(2)} – ${hi.toFixed(2)}`,
    color: seqColor(b / (NUM_BANDS - 1)),
    markerSize: 17,
  };
});

// --- Contour isolines via marching squares ---------------------------------
function marchingSquares(level) {
  const lerpVal = (a, b, za, zb) => a + (b - a) * (level - za) / (zb - za);
  const segs = [];
  for (let j = 0; j < GRID - 1; j++) {
    for (let i = 0; i < GRID - 1; i++) {
      const sw = zGrid[j][i],     se = zGrid[j][i + 1];
      const ne = zGrid[j + 1][i + 1], nw = zGrid[j + 1][i];
      const swA = sw > level, seA = se > level, neA = ne > level, nwA = nw > level;

      // Interpolated crossing point on each cell edge (null if not crossed)
      const edgeS = swA !== seA ? [lerpVal(xs[i], xs[i + 1], sw, se), ys[j]]           : null;
      const edgeE = seA !== neA ? [xs[i + 1], lerpVal(ys[j], ys[j + 1], se, ne)]       : null;
      const edgeN = nwA !== neA ? [lerpVal(xs[i], xs[i + 1], nw, ne), ys[j + 1]]       : null;
      const edgeW = swA !== nwA ? [xs[i],     lerpVal(ys[j], ys[j + 1], sw, nw)]       : null;

      const pts = [edgeS, edgeE, edgeN, edgeW].filter(Boolean);
      if (pts.length === 2) {
        segs.push([pts[0], pts[1]]);
      } else if (pts.length === 4) {
        // Saddle point: use cell center value to resolve ambiguity
        const mid = (sw + se + ne + nw) / 4;
        if (mid > level) {
          segs.push([edgeS, edgeE]); segs.push([edgeN, edgeW]);
        } else {
          segs.push([edgeS, edgeW]); segs.push([edgeN, edgeE]);
        }
      }
    }
  }
  return segs;
}

// Isolines at the 5 band boundaries
const isolineData = Array.from({ length: NUM_BANDS - 1 }, (_, i) => ({
  segments: marchingSquares(zMin + (i + 1) * bandW),
}));

// --- SVG isoline overlay (rendered as a ScatterChart child) ----------------
function IsolineOverlay() {
  const { left, top, width, height } = useDrawingArea();

  // Map data coords → SVG pixel coords (y axis is inverted in SVG)
  const toSVG = (dx, dy) => [
    left + (dx - X_MIN) / (X_MAX - X_MIN) * width,
    top  + (1 - (dy - Y_MIN) / (Y_MAX - Y_MIN)) * height,
  ];

  return (
    <>
      {isolineData.map(({ segments }, li) => {
        const d = segments
          .map(([p0, p1]) => {
            const [x0, y0] = toSVG(p0[0], p0[1]);
            const [x1, y1] = toSVG(p1[0], p1[1]);
            return `M ${x0.toFixed(1)},${y0.toFixed(1)} L ${x1.toFixed(1)},${y1.toFixed(1)}`;
          })
          .join(" ");
        return d
          ? <path key={li} d={d} stroke={t.ink} strokeWidth={1.5} strokeOpacity={0.5} fill="none" />
          : null;
      })}
    </>
  );
}

// --- Chart -----------------------------------------------------------------
const TITLE = "contour-basic · javascript · muix · anyplot.ai";

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  return (
    <Box sx={{ width: W, height: H, display: "flex", flexDirection: "column",
               bgcolor: t.pageBg, boxSizing: "border-box", pt: "28px", px: "32px", pb: "8px" }}>
      <Typography component="div"
        sx={{ fontSize: 22, fontWeight: 500, color: t.ink, textAlign: "center",
              lineHeight: 1.3, mb: "6px", flexShrink: 0 }}>
        {TITLE}
      </Typography>
      <ScatterChart
        width={W - 64}
        height={H - 28 - 36 - 8}
        skipAnimation
        tooltip={{ trigger: "none" }}
        series={scatterSeries}
        xAxis={[{
          min: X_MIN, max: X_MAX,
          label: "X",
          tickMinStep: 1,
          disableLine: true,
          labelStyle: { fontSize: 15, fill: t.ink },
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
        }]}
        yAxis={[{
          min: Y_MIN, max: Y_MAX,
          label: "Y",
          tickMinStep: 1,
          disableLine: true,
          labelStyle: { fontSize: 15, fill: t.ink },
          tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
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
      >
        <IsolineOverlay />
      </ScatterChart>
    </Box>
  );
}
