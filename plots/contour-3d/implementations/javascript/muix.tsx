// anyplot.ai
// contour-3d: 3D Contour Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 0/100 | Created: 2026-09-10

// Community @mui/x-charts has no 3D/surface/heatmap component, so this renders
// a genuine oblique 3D projection (isometric heightfield + marching-squares
// contour extraction) as SVG, driven entirely by the Imprint theme tokens.

const t = window.ANYPLOT_TOKENS;

// --- Data: a deterministic chemical-process yield response surface ----------
const GRID_N = 34;
const TEMP_MIN = 150;
const TEMP_MAX = 250;
const PRESSURE_MIN = 10;
const PRESSURE_MAX = 50;
const N_BANDS = 8;

const temperatures = Array.from(
  { length: GRID_N },
  (_, i) => TEMP_MIN + (i / (GRID_N - 1)) * (TEMP_MAX - TEMP_MIN),
);
const pressures = Array.from(
  { length: GRID_N },
  (_, j) => PRESSURE_MIN + (j / (GRID_N - 1)) * (PRESSURE_MAX - PRESSURE_MIN),
);

function yieldAt(i, j) {
  const u = (temperatures[i] - 200) / 50;
  const v = (pressures[j] - 30) / 20;
  return (
    90 -
    15 * u * u -
    20 * v * v +
    8 * u * v +
    3 * Math.sin(3 * u) * Math.cos(2 * v)
  );
}

const zGrid = Array.from({ length: GRID_N }, (_, i) =>
  Array.from({ length: GRID_N }, (_, j) => yieldAt(i, j)),
);

let zMin = Infinity;
let zMax = -Infinity;
for (const row of zGrid) {
  for (const v of row) {
    if (v < zMin) zMin = v;
    if (v > zMax) zMax = v;
  }
}
const zRange = zMax - zMin;

// --- Imprint sequential colormap (brand green -> blue), single-polarity data -
function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
function lerpColor(hexA, hexB, frac) {
  const [r1, g1, b1] = hexToRgb(hexA);
  const [r2, g2, b2] = hexToRgb(hexB);
  const r = Math.round(r1 + (r2 - r1) * frac);
  const g = Math.round(g1 + (g2 - g1) * frac);
  const b = Math.round(b1 + (b2 - b1) * frac);
  return `rgb(${r}, ${g}, ${b})`;
}
function bandColor(index) {
  return lerpColor(t.seq[0], t.seq[1], (index + 0.5) / N_BANDS);
}

// --- Surface quads: one per grid cell, shaded by its mean elevation band ----
const quads = [];
for (let i = 0; i < GRID_N - 1; i++) {
  for (let j = 0; j < GRID_N - 1; j++) {
    const z00 = zGrid[i][j];
    const z10 = zGrid[i + 1][j];
    const z11 = zGrid[i + 1][j + 1];
    const z01 = zGrid[i][j + 1];
    const avg = (z00 + z10 + z11 + z01) / 4;
    const bandIdx = Math.min(
      N_BANDS - 1,
      Math.max(0, Math.floor(((avg - zMin) / zRange) * N_BANDS)),
    );
    quads.push({
      i,
      j,
      z00,
      z10,
      z11,
      z01,
      depth: i + j,
      color: bandColor(bandIdx),
    });
  }
}
quads.sort((a, b) => a.depth - b.depth);

// --- Marching squares: extract contour-line segments at each band boundary --
const levels = Array.from(
  { length: N_BANDS - 1 },
  (_, k) => zMin + ((k + 1) / N_BANDS) * zRange,
);

function marchingSquares(level) {
  const segments = [];
  for (let i = 0; i < GRID_N - 1; i++) {
    for (let j = 0; j < GRID_N - 1; j++) {
      const tl = zGrid[i][j];
      const tr = zGrid[i + 1][j];
      const br = zGrid[i + 1][j + 1];
      const bl = zGrid[i][j + 1];
      const caseIdx =
        (tl >= level ? 8 : 0) |
        (tr >= level ? 4 : 0) |
        (br >= level ? 2 : 0) |
        (bl >= level ? 1 : 0);
      if (caseIdx === 0 || caseIdx === 15) continue;

      const topPt = { fi: i + (level - tl) / (tr - tl), fj: j };
      const rightPt = { fi: i + 1, fj: j + (level - tr) / (br - tr) };
      const bottomPt = { fi: i + (level - bl) / (br - bl), fj: j + 1 };
      const leftPt = { fi: i, fj: j + (level - tl) / (bl - tl) };
      const pair = (p1, p2) => segments.push({ p1, p2 });

      switch (caseIdx) {
        case 1:
          pair(leftPt, bottomPt);
          break;
        case 2:
          pair(bottomPt, rightPt);
          break;
        case 3:
          pair(leftPt, rightPt);
          break;
        case 4:
          pair(topPt, rightPt);
          break;
        case 5:
          pair(topPt, leftPt);
          pair(bottomPt, rightPt);
          break;
        case 6:
          pair(topPt, bottomPt);
          break;
        case 7:
        case 8:
          pair(topPt, leftPt);
          break;
        case 9:
          pair(topPt, bottomPt);
          break;
        case 10:
          pair(topPt, rightPt);
          pair(leftPt, bottomPt);
          break;
        case 11:
          pair(topPt, rightPt);
          break;
        case 12:
          pair(leftPt, rightPt);
          break;
        case 13:
          pair(bottomPt, rightPt);
          break;
        case 14:
          pair(leftPt, bottomPt);
          break;
        default:
          break;
      }
    }
  }
  return segments;
}

const contoursByLevel = levels.map((level) => ({
  level,
  segments: marchingSquares(level),
}));

// --- Chart (default-exported component — the harness mounts it) -------------
export default function Chart() {
  const size = window.ANYPLOT_SIZE;
  const W = size.width;
  const H = size.height;

  const marginTop = 130;
  const marginBottom = 70;
  const marginLeft = 60;
  const colorbarWidth = 150;
  const marginRight = 40;

  const plotW = W - marginLeft - marginRight - colorbarWidth;
  const plotH = H - marginTop - marginBottom;

  const footprintH = plotH * 0.6;
  const heightScale = plotH * 0.36;

  const halfTileW = plotW / (2 * (GRID_N - 1));
  const halfTileH = footprintH / (2 * (GRID_N - 1));

  const originX = marginLeft + plotW / 2;
  const originY = marginTop + heightScale;

  function project(fi, fj, elevation) {
    const h = ((elevation - zMin) / zRange) * heightScale;
    const x = originX + (fi - fj) * halfTileW;
    const y = originY + (fi + fj) * halfTileH - h;
    return [x, y];
  }

  const quadPaths = quads.map((q) => {
    const p00 = project(q.i, q.j, q.z00);
    const p10 = project(q.i + 1, q.j, q.z10);
    const p11 = project(q.i + 1, q.j + 1, q.z11);
    const p01 = project(q.i, q.j + 1, q.z01);
    const d = `M ${p00[0]},${p00[1]} L ${p10[0]},${p10[1]} L ${p11[0]},${p11[1]} L ${p01[0]},${p01[1]} Z`;
    return { key: `q-${q.i}-${q.j}`, d, color: q.color };
  });

  const surfaceContours = [];
  const baseContours = [];
  contoursByLevel.forEach(({ level, segments }, levelIdx) => {
    segments.forEach((seg, segIdx) => {
      const a = project(seg.p1.fi, seg.p1.fj, level);
      const b = project(seg.p2.fi, seg.p2.fj, level);
      surfaceContours.push({
        key: `sc-${levelIdx}-${segIdx}`,
        x1: a[0],
        y1: a[1],
        x2: b[0],
        y2: b[1],
      });
      const a0 = project(seg.p1.fi, seg.p1.fj, zMin);
      const b0 = project(seg.p2.fi, seg.p2.fj, zMin);
      baseContours.push({
        key: `bc-${levelIdx}-${segIdx}`,
        x1: a0[0],
        y1: a0[1],
        x2: b0[0],
        y2: b0[1],
      });
    });
  });

  // Front-edge anchors (corner nearest the viewer) for axis captions.
  const mid = Math.round((GRID_N - 1) / 2);
  const tempAnchor = project(mid, GRID_N - 1, zGrid[mid][GRID_N - 1]);
  const pressureAnchor = project(GRID_N - 1, mid, zGrid[GRID_N - 1][mid]);

  const colorbarX = W - marginRight - colorbarWidth + 55;
  const colorbarY = marginTop;
  const colorbarH = plotH;
  const colorbarW = 26;
  const bandH = colorbarH / N_BANDS;

  return (
    <svg width={W} height={H}>
      <text x={marginLeft} y={58} fontSize={26} fontWeight={600} fill={t.ink}>
        contour-3d · javascript · muix · anyplot.ai
      </text>

      <g>
        {baseContours.map((seg) => (
          <line
            key={seg.key}
            x1={seg.x1}
            y1={seg.y1}
            x2={seg.x2}
            y2={seg.y2}
            stroke={t.inkSoft}
            strokeWidth={1.25}
            strokeDasharray="5 5"
            opacity={0.5}
          />
        ))}
      </g>

      <g>
        {quadPaths.map((q) => (
          <path
            key={q.key}
            d={q.d}
            fill={q.color}
            stroke={t.grid}
            strokeWidth={0.75}
          />
        ))}
      </g>

      <g>
        {surfaceContours.map((seg) => (
          <line
            key={seg.key}
            x1={seg.x1}
            y1={seg.y1}
            x2={seg.x2}
            y2={seg.y2}
            stroke={t.ink}
            strokeWidth={1.5}
            opacity={0.55}
          />
        ))}
      </g>

      <text
        x={tempAnchor[0]}
        y={tempAnchor[1] + 48}
        fontSize={16}
        fill={t.inkSoft}
        textAnchor="middle"
      >
        Temperature 150–250°C
      </text>
      <text
        x={pressureAnchor[0] + 26}
        y={pressureAnchor[1] + 20}
        fontSize={16}
        fill={t.inkSoft}
        textAnchor="start"
      >
        Pressure 10–50 bar
      </text>

      <text x={colorbarX} y={colorbarY - 22} fontSize={17} fill={t.ink}>
        Yield (%)
      </text>
      {Array.from({ length: N_BANDS }, (_, k) => (
        <rect
          key={`cb-${k}`}
          x={colorbarX}
          y={colorbarY + k * bandH}
          width={colorbarW}
          height={bandH}
          fill={bandColor(N_BANDS - 1 - k)}
        />
      ))}
      <rect
        x={colorbarX}
        y={colorbarY}
        width={colorbarW}
        height={colorbarH}
        fill="none"
        stroke={t.grid}
        strokeWidth={1}
      />
      {Array.from({ length: N_BANDS + 1 }, (_, k) => {
        const value = zMax - (k / N_BANDS) * zRange;
        return (
          <text
            key={`cbl-${k}`}
            x={colorbarX + colorbarW + 10}
            y={colorbarY + k * bandH + 5}
            fontSize={14}
            fill={t.inkSoft}
          >
            {value.toFixed(0)}
          </text>
        );
      })}
    </svg>
  );
}
