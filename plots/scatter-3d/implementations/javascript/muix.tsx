// anyplot.ai
// scatter-3d: 3D Scatter Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 93/100 | Created: 2026-09-10

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "scatter-3d · javascript · muix · anyplot.ai";
const ISO_ANGLE = Math.PI / 6;
const MARKER_SIZE_BY_TIER = { near: 12, mid: 8.5, far: 5.5 };
const MARKER_ALPHA = 0.85;
const PAD = 16;

// Columns: set these to your data's column names
const X_COORD = "X (nm)"; // role: x
const Y_COORD = "Height (Y) (nm)"; // role: y
const Z_COORD = "Z (nm)"; // role: z
const COLOR_VAL = "Potential energy (eV)"; // role: color

// Data: replace this block with your own records
const AXIS_MIN = 0;
const AXIS_MAX = 100;
const FRAGMENTS = [
  { center: [22, 74, 30], sigma: 7, count: 55 },
  { center: [78, 32, 68], sigma: 8, count: 55 },
  { center: [42, 20, 84], sigma: 6, count: 45 },
];

let lcgState = 7;
const data = [];
FRAGMENTS.forEach((fragment) => {
  for (let i = 0; i < fragment.count; i += 1) {
    lcgState = (lcgState * 16807) % 2147483647;
    const u1x = Math.max((lcgState - 1) / 2147483646, 1e-9);
    lcgState = (lcgState * 16807) % 2147483647;
    const u2x = (lcgState - 1) / 2147483646;
    const gx = Math.sqrt(-2 * Math.log(u1x)) * Math.cos(2 * Math.PI * u2x);

    lcgState = (lcgState * 16807) % 2147483647;
    const u1y = Math.max((lcgState - 1) / 2147483646, 1e-9);
    lcgState = (lcgState * 16807) % 2147483647;
    const u2y = (lcgState - 1) / 2147483646;
    const gy = Math.sqrt(-2 * Math.log(u1y)) * Math.cos(2 * Math.PI * u2y);

    lcgState = (lcgState * 16807) % 2147483647;
    const u1z = Math.max((lcgState - 1) / 2147483646, 1e-9);
    lcgState = (lcgState * 16807) % 2147483647;
    const u2z = (lcgState - 1) / 2147483646;
    const gz = Math.sqrt(-2 * Math.log(u1z)) * Math.cos(2 * Math.PI * u2z);

    lcgState = (lcgState * 16807) % 2147483647;
    const u1e = Math.max((lcgState - 1) / 2147483646, 1e-9);
    lcgState = (lcgState * 16807) % 2147483647;
    const u2e = (lcgState - 1) / 2147483646;
    const ge = Math.sqrt(-2 * Math.log(u1e)) * Math.cos(2 * Math.PI * u2e);

    const x = fragment.center[0] + gx * fragment.sigma;
    const y = fragment.center[1] + gy * fragment.sigma;
    const z = fragment.center[2] + gz * fragment.sigma;
    const distanceFromCore = Math.sqrt(
      (x - fragment.center[0]) ** 2 +
        (y - fragment.center[1]) ** 2 +
        (z - fragment.center[2]) ** 2
    );
    const energy = -6.4 + 0.062 * distanceFromCore + ge * 0.22;
    data.push({
      [X_COORD]: Math.min(Math.max(x, AXIS_MIN + 1), AXIS_MAX - 1),
      [Y_COORD]: Math.min(Math.max(y, AXIS_MIN + 1), AXIS_MAX - 1),
      [Z_COORD]: Math.min(Math.max(z, AXIS_MIN + 1), AXIS_MAX - 1),
      [COLOR_VAL]: energy,
    });
  }
});

// Plot: reads only data and the constants above
const cosIso = Math.cos(ISO_ANGLE);
const sinIso = Math.sin(ISO_ANGLE);

const atoms = data.map((row, idx) => {
  const x = Number(row[X_COORD]);
  const y = Number(row[Y_COORD]);
  const z = Number(row[Z_COORD]);
  const energy = Number(row[COLOR_VAL]);
  const px = (x - z) * cosIso;
  const py = y - (x + z) * sinIso;
  return { id: `atom-${idx}`, x, y, z, energy, px, py };
});

const maxCoord = Math.max(...atoms.flatMap((a) => [a.x, a.y, a.z]));
const cellMin = 0;
const cellMax = Math.ceil(maxCoord / 50) * 50;

const groundDepths = atoms.map((atom) => atom.x + atom.z).sort((a, b) => a - b);
const tierBoundary1 = groundDepths[Math.floor(groundDepths.length / 3)];
const tierBoundary2 = groundDepths[Math.floor((2 * groundDepths.length) / 3)];

const cellCorners = [];
[cellMin, cellMax].forEach((cx) =>
  [cellMin, cellMax].forEach((cy) =>
    [cellMin, cellMax].forEach((cz) =>
      cellCorners.push({
        px: (cx - cz) * cosIso,
        py: cy - (cx + cz) * sinIso,
      })
    )
  )
);
const pxMin = Math.min(...cellCorners.map((c) => c.px)) - PAD;
const pxMax = Math.max(...cellCorners.map((c) => c.px)) + PAD;
const pyMin = Math.min(...cellCorners.map((c) => c.py)) - PAD;
const pyMax = Math.max(...cellCorners.map((c) => c.py)) + PAD * 1.6;

const seq0Num = parseInt(t.seq[0].slice(1), 16);
const seq1Num = parseInt(t.seq[1].slice(1), 16);
const seq0Rgba = `rgba(${(seq0Num >> 16) & 255}, ${(seq0Num >> 8) & 255}, ${seq0Num & 255}, ${MARKER_ALPHA})`;
const seq1Rgba = `rgba(${(seq1Num >> 16) & 255}, ${(seq1Num >> 8) & 255}, ${seq1Num & 255}, ${MARKER_ALPHA})`;

const energyValues = atoms.map((atom) => atom.energy);
const energyMin = Math.min(...energyValues);
const energyMax = Math.max(...energyValues);

const zAxis = [
  {
    id: "energyColor",
    colorMap: {
      type: "continuous",
      min: energyMin,
      max: energyMax,
      color: [seq0Rgba, seq1Rgba],
    },
  },
];

const series = ["near", "mid", "far"].map((tier) => ({
  type: "scatter",
  id: `atoms-${tier}`,
  zAxisId: "energyColor",
  markerSize: MARKER_SIZE_BY_TIER[tier],
  data: atoms
    .filter((atom) => {
      const depth = atom.x + atom.z;
      const atomTier = depth <= tierBoundary1 ? "near" : depth <= tierBoundary2 ? "mid" : "far";
      return atomTier === tier;
    })
    .map((atom) => ({
      x: atom.px,
      y: atom.py,
      z: atom.energy,
      id: atom.id,
      realX: atom.x,
      realY: atom.y,
      realZ: atom.z,
      energy: atom.energy,
    })),
  valueFormatter: (value) =>
    `x=${value.realX.toFixed(1)}, y=${value.realY.toFixed(1)}, z=${value.realZ.toFixed(1)} · ${value.energy.toFixed(2)}`,
}));

const originPoint = { px: 0, py: 0 };
const xEndPoint = { px: cellMax * cosIso, py: -cellMax * sinIso };
const yEndPoint = { px: 0, py: cellMax };
const zEndPoint = { px: -cellMax * cosIso, py: -cellMax * sinIso };
const farFloorCorner = { px: 0, py: -2 * cellMax * sinIso };

function Iso3DFrame() {
  const xScale = useXScale();
  const yScale = useYScale();
  const { width, height } = window.ANYPLOT_SIZE;

  const origin = { x: xScale(originPoint.px), y: yScale(originPoint.py) };
  const xEnd = { x: xScale(xEndPoint.px), y: yScale(xEndPoint.py) };
  const yEnd = { x: xScale(yEndPoint.px), y: yScale(yEndPoint.py) };
  const zEnd = { x: xScale(zEndPoint.px), y: yScale(zEndPoint.py) };
  const farFloor = { x: xScale(farFloorCorner.px), y: yScale(farFloorCorner.py) };

  const depthLegendX = 70;
  const depthLegendY = 96;
  const depthLegendItems = [
    { tier: "Near", r: MARKER_SIZE_BY_TIER.near },
    { tier: "Mid", r: MARKER_SIZE_BY_TIER.mid },
    { tier: "Far", r: MARKER_SIZE_BY_TIER.far },
  ];

  const cbWidth = Math.round(width * 0.26);
  const cbX = Math.round((width - cbWidth) / 2);
  const cbY = height - 48;

  return (
    <g>
      <line
        x1={xEnd.x}
        y1={xEnd.y}
        x2={farFloor.x}
        y2={farFloor.y}
        stroke={t.grid}
        strokeWidth={1.5}
        strokeDasharray="6 5"
      />
      <line
        x1={zEnd.x}
        y1={zEnd.y}
        x2={farFloor.x}
        y2={farFloor.y}
        stroke={t.grid}
        strokeWidth={1.5}
        strokeDasharray="6 5"
      />
      <line x1={origin.x} y1={origin.y} x2={xEnd.x} y2={xEnd.y} stroke={t.inkSoft} strokeWidth={2} />
      <line x1={origin.x} y1={origin.y} x2={yEnd.x} y2={yEnd.y} stroke={t.inkSoft} strokeWidth={2} />
      <line x1={origin.x} y1={origin.y} x2={zEnd.x} y2={zEnd.y} stroke={t.inkSoft} strokeWidth={2} />

      <text x={origin.x - 14} y={origin.y + 18} fill={t.ink} fontSize={15} fontWeight={600} textAnchor="middle">
        0
      </text>
      <text x={xEnd.x + 24} y={xEnd.y + 8} fill={t.ink} fontSize={15} fontWeight={600} textAnchor="middle">
        {`${X_COORD} · ${cellMax}`}
      </text>
      <text x={yEnd.x} y={yEnd.y - 14} fill={t.ink} fontSize={15} fontWeight={600} textAnchor="middle">
        {`${Y_COORD} · ${cellMax}`}
      </text>
      <text x={zEnd.x - 30} y={zEnd.y + 8} fill={t.ink} fontSize={15} fontWeight={600} textAnchor="middle">
        {`${Z_COORD} · ${cellMax}`}
      </text>

      <text x={depthLegendX} y={depthLegendY - 22} fill={t.inkSoft} fontSize={16}>
        Marker size = depth
      </text>
      {depthLegendItems.map((item, i) => (
        <g key={item.tier} transform={`translate(${depthLegendX + i * 90}, ${depthLegendY})`}>
          <circle cx={0} cy={0} r={item.r} fill={t.inkSoft} opacity={0.55} />
          <text x={18} y={5} fill={t.inkSoft} fontSize={15}>
            {item.tier}
          </text>
        </g>
      ))}

      <defs>
        <linearGradient id="scatter3dEnergyGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={seq0Rgba} />
          <stop offset="100%" stopColor={seq1Rgba} />
        </linearGradient>
      </defs>
      <text x={width / 2} y={cbY - 8} textAnchor="middle" fontSize={14} fill={t.inkSoft}>
        {COLOR_VAL}
      </text>
      <rect x={cbX} y={cbY} width={cbWidth} height={10} rx={3} fill="url(#scatter3dEnergyGrad)" />
      <text x={cbX - 10} y={cbY + 9} textAnchor="end" fontSize={14} fill={t.inkSoft}>
        {`${energyMin.toFixed(1)} · core`}
      </text>
      <text x={cbX + cbWidth + 10} y={cbY + 9} textAnchor="start" fontSize={14} fill={t.inkSoft}>
        {`${energyMax.toFixed(1)} · edge`}
      </text>
    </g>
  );
}

export default function Chart() {
  const size = window.ANYPLOT_SIZE;
  return (
    <ChartsContainer
      width={size.width}
      height={size.height}
      series={series}
      zAxis={zAxis}
      xAxis={[{ id: "iso-x", scaleType: "linear", min: pxMin, max: pxMax, position: "none" }]}
      yAxis={[{ id: "iso-y", scaleType: "linear", min: pyMin, max: pyMax, position: "none" }]}
      margin={{ top: 70, right: 60, bottom: 90, left: 60 }}
      disableVoronoi
      skipAnimation
    >
      <text
        x={size.width / 2}
        y={38}
        textAnchor="middle"
        fontSize={26}
        fontWeight={600}
        fill={t.ink}
      >
        {TITLE}
      </text>
      <Iso3DFrame />
      <ScatterPlot />
      <ChartsTooltip trigger="item" />
    </ChartsContainer>
  );
}
