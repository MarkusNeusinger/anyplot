// anyplot.ai
// quiver-basic: Basic Quiver Plot
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 91/100 | Created: 2026-07-24
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "Cyclonic Wind Field · quiver-basic · javascript · muix · anyplot.ai";
const HEAD_PX = 10;
const ARROW_STEP_FRAC = 0.85;
const COLORBAR_TITLE = "Wind Speed (m/s)";

// Columns: set these to your data's column names
const X_POS = "X Position (km)"; // role: x
const Y_POS = "Y Position (km)"; // role: y
const U_VEL = "Zonal wind u (m/s)"; // role: u
const V_VEL = "Meridional wind v (m/s)"; // role: v

// Data: replace this block with your own records
const DOMAIN = 7;
const GRID_N = 15;
const CORE_RADIUS = 3.2;
const PEAK_SPEED = 22;

const data = [];
for (let i = 0; i < GRID_N; i += 1) {
  for (let j = 0; j < GRID_N; j += 1) {
    const x = -DOMAIN + (2 * DOMAIN * i) / (GRID_N - 1);
    const y = -DOMAIN + (2 * DOMAIN * j) / (GRID_N - 1);
    const r = Math.sqrt(x * x + y * y) + 1e-6;
    const speed = r <= CORE_RADIUS ? (PEAK_SPEED * r) / CORE_RADIUS : (PEAK_SPEED * CORE_RADIUS) / r;
    const u = (-y / r) * speed;
    const v = (x / r) * speed;
    data.push({ [X_POS]: x, [Y_POS]: y, [U_VEL]: u, [V_VEL]: v });
  }
}

// Plot: reads only data and the constants above
const vectors = data.map((row) => {
  const x = Number(row[X_POS]);
  const y = Number(row[Y_POS]);
  const u = Number(row[U_VEL]);
  const v = Number(row[V_VEL]);
  const speed = Math.hypot(u, v);
  return { x, y, u, v, speed };
});

const xs = vectors.map((vec) => vec.x);
const ys = vectors.map((vec) => vec.y);
const xMinRaw = Math.min(...xs);
const xMaxRaw = Math.max(...xs);
const yMinRaw = Math.min(...ys);
const yMaxRaw = Math.max(...ys);
const maxSpeed = Math.max(...vectors.map((vec) => vec.speed));

const uniqueXs = Array.from(new Set(xs)).sort((a, b) => a - b);
const gridStep = uniqueXs.length > 1 ? uniqueXs[1] - uniqueXs[0] : 1;
const arrowScale = (ARROW_STEP_FRAC * gridStep) / maxSpeed;
const pad = gridStep * 0.8;

const seqA = parseInt(t.seq[0].slice(1), 16);
const seqB = parseInt(t.seq[1].slice(1), 16);
const ar = (seqA >> 16) & 255;
const ag = (seqA >> 8) & 255;
const ab = seqA & 255;
const br = (seqB >> 16) & 255;
const bg = (seqB >> 8) & 255;
const bb = seqB & 255;

function QuiverLayer() {
  const xScale = useXScale();
  const yScale = useYScale();
  const { left, top, width: gW, height: gH } = useDrawingArea();
  const cbX = left + gW + 26;
  const cbW = 18;
  const titleSize = TITLE.length > 67 ? Math.round(22 * (67 / TITLE.length)) : 22;

  return (
    <g>
      <text
        x={left + gW / 2}
        y={top - 62}
        textAnchor="middle"
        fontSize={titleSize}
        fontWeight={600}
        fill={t.ink}
      >
        {TITLE}
      </text>

      <g strokeLinecap="round">
        {vectors.map((vec, i) => {
          const x1 = xScale(vec.x);
          const y1 = yScale(vec.y);
          const x2 = xScale(vec.x + vec.u * arrowScale);
          const y2 = yScale(vec.y + vec.v * arrowScale);
          const frac = Math.min(1, vec.speed / maxSpeed);
          const rr = Math.round(ar + (br - ar) * frac);
          const rg = Math.round(ag + (bg - ag) * frac);
          const rb = Math.round(ab + (bb - ab) * frac);
          const color = `rgb(${rr}, ${rg}, ${rb})`;
          const angle = Math.atan2(y2 - y1, x2 - x1);
          const a1 = angle - 0.4;
          const a2 = angle + 0.4;
          const headPoints = `${x2},${y2} ${x2 - HEAD_PX * Math.cos(a1)},${y2 - HEAD_PX * Math.sin(a1)} ${x2 - HEAD_PX * Math.cos(a2)},${y2 - HEAD_PX * Math.sin(a2)}`;
          return (
            <g key={i}>
              <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={color} strokeWidth={2.2} />
              <polygon points={headPoints} fill={color} />
            </g>
          );
        })}
      </g>

      <defs>
        <linearGradient id="quiverSpeedGrad" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor={t.seq[0]} />
          <stop offset="100%" stopColor={t.seq[1]} />
        </linearGradient>
      </defs>
      <rect x={cbX} y={top} width={cbW} height={gH} fill="url(#quiverSpeedGrad)" />
      <text x={cbX + cbW / 2} y={top - 8} textAnchor="middle" fontSize={13} fill={t.inkSoft}>
        {Math.round(maxSpeed)}
      </text>
      <text x={cbX + cbW / 2} y={top + gH + 18} textAnchor="middle" fontSize={13} fill={t.inkSoft}>
        0
      </text>
      <text
        x={cbX + cbW + 20}
        y={top + gH / 2}
        textAnchor="middle"
        fontSize={14}
        fill={t.inkSoft}
        transform={`rotate(90, ${cbX + cbW + 20}, ${top + gH / 2})`}
      >
        {COLORBAR_TITLE}
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <ChartsContainer
      width={width}
      height={height}
      skipAnimation
      series={[]}
      xAxis={[
        {
          scaleType: "linear",
          min: xMinRaw - pad,
          max: xMaxRaw + pad,
          height: 64,
          label: X_POS,
          labelStyle: { fontSize: 16 },
          tickLabelStyle: { fontSize: 14 },
        },
      ]}
      yAxis={[
        {
          scaleType: "linear",
          min: yMinRaw - pad,
          max: yMaxRaw + pad,
          width: 80,
          label: Y_POS,
          labelStyle: { fontSize: 16 },
          tickLabelStyle: { fontSize: 14 },
        },
      ]}
      margin={{ top: 130, right: 170, bottom: 36, left: 24 }}
    >
      <QuiverLayer />
      <ChartsXAxis />
      <ChartsYAxis />
    </ChartsContainer>
  );
}
