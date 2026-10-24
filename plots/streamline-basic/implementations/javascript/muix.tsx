// anyplot.ai
// streamline-basic: Basic Streamline Plot
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-09

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { LinePlot } from "@mui/x-charts/LineChart";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsText } from "@mui/x-charts/ChartsText";
import { useXScale, useYScale, useDrawingArea } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const EXCLUSION_R = 0.16;
const X_BOUND = 4.6;
const Y_BOUND = 2.55;
const STEP_LEN = 0.032;
const MAX_STEPS = 2200;
const LINE_COUNT = 16;
const SEGMENTS_PER_LINE = 5;
const X_MIN = -X_BOUND;
const X_MAX = 2.0;
const Y_MIN = -Y_BOUND;
const Y_MAX = Y_BOUND;
const TITLE_HEIGHT = 70;
const MARGIN = { top: 30, bottom: 90, left: 100, right: 60 };

// Columns: set these to your data's column names
const X_COORD = "x (normalized distance)"; // role: x
const Y_COORD = "y (normalized distance)"; // role: y
const U_VEL = "Horizontal Field Component (Ex)"; // role: u
const V_VEL = "Vertical Field Component (Ey)"; // role: v

// Data: replace this block with your own records
const polePosX = -1.1;
const polePosY = 0;
const poleNegX = 1.1;
const poleNegY = 0;
const gridNx = 47;
const gridNy = 27;

const data: Array<Record<string, number>> = [];
for (let j = 0; j < gridNy; j++) {
  const gy = -Y_BOUND + (j / (gridNy - 1)) * (2 * Y_BOUND);
  for (let i = 0; i < gridNx; i++) {
    const gx = -X_BOUND + (i / (gridNx - 1)) * (2 * X_BOUND);
    const dxP = gx - polePosX;
    const dyP = gy - polePosY;
    const dxN = gx - poleNegX;
    const dyN = gy - poleNegY;
    const rP3 = Math.pow(dxP * dxP + dyP * dyP, 1.5) + 1e-4;
    const rN3 = Math.pow(dxN * dxN + dyN * dyN, 1.5) + 1e-4;
    const uVal = dxP / rP3 - dxN / rN3;
    const vVal = dyP / rP3 - dyN / rN3;
    data.push({
      [X_COORD]: Number(gx.toFixed(3)),
      [Y_COORD]: Number(gy.toFixed(3)),
      [U_VEL]: uVal,
      [V_VEL]: vVal,
    });
  }
}

// Plot: reads only data and the constants above
// Locate the source and sink poles from the vector field grid
let sourceNode = data[0];
let sinkNode = data[0];
let maxSourceScore = -Infinity;
let maxSinkScore = -Infinity;

for (let idx = 0; idx < data.length; idx++) {
  const row = data[idx];
  const rx = Number(row[X_COORD]);
  const ry = Number(row[Y_COORD]);
  let outFlux = 0;
  for (let k = 0; k < data.length; k++) {
    const nb = data[k];
    const dx = Number(nb[X_COORD]) - rx;
    const dy = Number(nb[Y_COORD]) - ry;
    const d2 = dx * dx + dy * dy;
    if (d2 > 0.01 && d2 < 0.12) {
      const dist = Math.sqrt(d2);
      outFlux += (Number(nb[U_VEL]) * dx + Number(nb[V_VEL]) * dy) / dist;
    }
  }
  if (outFlux > maxSourceScore) {
    maxSourceScore = outFlux;
    sourceNode = row;
  }
  if (-outFlux > maxSinkScore) {
    maxSinkScore = -outFlux;
    sinkNode = row;
  }
}

const chargePos = {
  x: Number(sourceNode[X_COORD]),
  y: Number(sourceNode[Y_COORD]),
  q: 1,
};
const chargeNeg = {
  x: Number(sinkNode[X_COORD]),
  y: Number(sinkNode[Y_COORD]),
  q: -1,
};

const rawLines: Array<{ xs: number[]; ys: number[]; mags: number[] }> = [];
for (let k = 0; k < LINE_COUNT; k++) {
  const theta = ((k + 0.5) / LINE_COUNT) * 2 * Math.PI;
  let x = chargePos.x + EXCLUSION_R * Math.cos(theta);
  let y = chargePos.y + EXCLUSION_R * Math.sin(theta);
  const xs = [x];
  const ys = [y];

  const dxP0 = x - chargePos.x;
  const dyP0 = y - chargePos.y;
  const dxN0 = x - chargeNeg.x;
  const dyN0 = y - chargeNeg.y;
  const rP30 = Math.pow(dxP0 * dxP0 + dyP0 * dyP0, 1.5) + 1e-6;
  const rN30 = Math.pow(dxN0 * dxN0 + dyN0 * dyN0, 1.5) + 1e-6;
  const mags = [
    Math.hypot(
      chargePos.q * (dxP0 / rP30) + chargeNeg.q * (dxN0 / rN30),
      chargePos.q * (dyP0 / rP30) + chargeNeg.q * (dyN0 / rN30),
    ),
  ];

  for (let step = 0; step < MAX_STEPS; step++) {
    // 4-stage RK4 on unit field vector
    const pts = [
      [x, y],
      [x, y],
      [x, y],
      [x, y],
    ];
    const ks = [
      [0, 0],
      [0, 0],
      [0, 0],
      [0, 0],
    ];
    for (let stage = 0; stage < 4; stage++) {
      const px =
        stage === 0
          ? x
          : stage === 1
            ? x + (STEP_LEN / 2) * ks[0][0]
            : stage === 2
              ? x + (STEP_LEN / 2) * ks[1][0]
              : x + STEP_LEN * ks[2][0];
      const py =
        stage === 0
          ? y
          : stage === 1
            ? y + (STEP_LEN / 2) * ks[0][1]
            : stage === 2
              ? y + (STEP_LEN / 2) * ks[1][1]
              : y + STEP_LEN * ks[2][1];
      pts[stage] = [px, py];
      const dxP = px - chargePos.x;
      const dyP = py - chargePos.y;
      const dxN = px - chargeNeg.x;
      const dyN = py - chargeNeg.y;
      const rP3 = Math.pow(dxP * dxP + dyP * dyP, 1.5) + 1e-6;
      const rN3 = Math.pow(dxN * dxN + dyN * dyN, 1.5) + 1e-6;
      const ex = chargePos.q * (dxP / rP3) + chargeNeg.q * (dxN / rN3);
      const ey = chargePos.q * (dyP / rP3) + chargeNeg.q * (dyN / rN3);
      const mag = Math.hypot(ex, ey) || 1e-9;
      ks[stage] = [ex / mag, ey / mag];
    }

    x += (STEP_LEN / 6) * (ks[0][0] + 2 * ks[1][0] + 2 * ks[2][0] + ks[3][0]);
    y += (STEP_LEN / 6) * (ks[0][1] + 2 * ks[1][1] + 2 * ks[2][1] + ks[3][1]);

    const dSink = Math.hypot(x - chargeNeg.x, y - chargeNeg.y);
    if (dSink < EXCLUSION_R) {
      const snap = EXCLUSION_R / dSink;
      x = chargeNeg.x + (x - chargeNeg.x) * snap;
      y = chargeNeg.y + (y - chargeNeg.y) * snap;
      xs.push(x);
      ys.push(y);
      const dxP = x - chargePos.x;
      const dyP = y - chargePos.y;
      const dxN = x - chargeNeg.x;
      const dyN = y - chargeNeg.y;
      const rP3 = Math.pow(dxP * dxP + dyP * dyP, 1.5) + 1e-6;
      const rN3 = Math.pow(dxN * dxN + dyN * dyN, 1.5) + 1e-6;
      mags.push(
        Math.hypot(
          chargePos.q * (dxP / rP3) + chargeNeg.q * (dxN / rN3),
          chargePos.q * (dyP / rP3) + chargeNeg.q * (dyN / rN3),
        ),
      );
      break;
    }
    if (Math.abs(x) > X_BOUND || Math.abs(y) > Y_BOUND) break;
    xs.push(x);
    ys.push(y);
    const dxP = x - chargePos.x;
    const dyP = y - chargePos.y;
    const dxN = x - chargeNeg.x;
    const dyN = y - chargeNeg.y;
    const rP3 = Math.pow(dxP * dxP + dyP * dyP, 1.5) + 1e-6;
    const rN3 = Math.pow(dxN * dxN + dyN * dyN, 1.5) + 1e-6;
    mags.push(
      Math.hypot(
        chargePos.q * (dxP / rP3) + chargeNeg.q * (dxN / rN3),
        chargePos.q * (dyP / rP3) + chargeNeg.q * (dyN / rN3),
      ),
    );
  }
  rawLines.push({ xs, ys, mags });
}

const allLogMags = rawLines.flatMap((l) =>
  l.mags.map((m) => Math.log10(m + 1e-6)),
);
const logMin = Math.min(...allLogMags);
const logMax = Math.max(...allLogMags);

const seqR1 = parseInt(t.seq[0].slice(1, 3), 16);
const seqG1 = parseInt(t.seq[0].slice(3, 5), 16);
const seqB1 = parseInt(t.seq[0].slice(5, 7), 16);
const seqR2 = parseInt(t.seq[1].slice(1, 3), 16);
const seqG2 = parseInt(t.seq[1].slice(3, 5), 16);
const seqB2 = parseInt(t.seq[1].slice(5, 7), 16);

let axisCounter = 0;
const segments: Array<{
  axisId: string;
  xs: number[];
  ys: number[];
  color: string;
}> = [];
const arrowSpecs: Array<{
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  color: string;
}> = [];

for (const line of rawLines) {
  const n = line.xs.length;
  const segLen = Math.max(1, Math.floor((n - 1) / SEGMENTS_PER_LINE));
  const lineSegments: typeof segments = [];
  for (let s = 0; s < SEGMENTS_PER_LINE; s++) {
    const start = s * segLen;
    const end = s === SEGMENTS_PER_LINE - 1 ? n - 1 : (s + 1) * segLen;
    if (end <= start) continue;
    const segMags = line.mags.slice(start, end + 1);
    const avgLogMag =
      segMags.reduce((acc, m) => acc + Math.log10(m + 1e-6), 0) /
      segMags.length;
    const norm = Math.min(
      1,
      Math.max(0, logMax > logMin ? (avgLogMag - logMin) / (logMax - logMin) : 0.5),
    );
    const r = Math.round(seqR1 + (seqR2 - seqR1) * norm);
    const g = Math.round(seqG1 + (seqG2 - seqG1) * norm);
    const b = Math.round(seqB1 + (seqB2 - seqB1) * norm);
    const segment = {
      axisId: `fl-${axisCounter++}`,
      xs: line.xs.slice(start, end + 1),
      ys: line.ys.slice(start, end + 1),
      color: `rgb(${r}, ${g}, ${b})`,
    };
    segments.push(segment);
    lineSegments.push(segment);
  }
  if (n > 12 && lineSegments.length > 0) {
    for (const frac of [0.15, 0.42, 0.72]) {
      const idx = Math.min(n - 3, Math.max(2, Math.round(frac * (n - 1))));
      const segIdx = Math.min(
        lineSegments.length - 1,
        Math.floor(idx / segLen),
      );
      const segment = lineSegments[segIdx];
      arrowSpecs.push({
        x0: line.xs[idx],
        y0: line.ys[idx],
        x1: line.xs[idx + 2],
        y1: line.ys[idx + 2],
        color: segment.color,
      });
    }
  }
}

const sharedAxisId = segments[0].axisId;

function FieldOverlay() {
  const xScale = useXScale(sharedAxisId) as (v: number) => number;
  const yScale = useYScale() as (v: number) => number;
  const area = useDrawingArea();

  const legendW = 190;
  const legendH = 14;
  const legendX = area.left + area.width - legendW - 18;
  const legendY = area.top + 18;
  const arrowSize = 11;
  const spread = 0.48;

  return (
    <g>
      {arrowSpecs.map((a, i) => {
        const p0x = xScale(a.x0);
        const p0y = yScale(a.y0);
        const p1x = xScale(a.x1);
        const p1y = yScale(a.y1);
        const angle = Math.atan2(p1y - p0y, p1x - p0x);
        const backAngle = angle + Math.PI;
        const tipX = p0x + Math.cos(angle) * arrowSize;
        const tipY = p0y + Math.sin(angle) * arrowSize;
        const leftX = p0x + Math.cos(backAngle - spread) * arrowSize;
        const leftY = p0y + Math.sin(backAngle - spread) * arrowSize;
        const rightX = p0x + Math.cos(backAngle + spread) * arrowSize;
        const rightY = p0y + Math.sin(backAngle + spread) * arrowSize;
        return (
          <polygon
            key={i}
            points={`${tipX},${tipY} ${leftX},${leftY} ${rightX},${rightY}`}
            fill={a.color}
            stroke={t.pageBg}
            strokeWidth={1}
          />
        );
      })}

      <defs>
        <linearGradient id="streamline-strength-grad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor={t.seq[0]} />
          <stop offset="100%" stopColor={t.seq[1]} />
        </linearGradient>
      </defs>
      <ChartsText
        x={legendX + legendW / 2}
        y={legendY - 14}
        text="Field strength (|E|)"
        style={{
          fontSize: 14,
          fill: t.inkSoft,
          textAnchor: "middle",
          dominantBaseline: "central",
        }}
      />
      <rect
        x={legendX}
        y={legendY}
        width={legendW}
        height={legendH}
        rx={3}
        fill="url(#streamline-strength-grad)"
      />
      <ChartsText
        x={legendX}
        y={legendY + legendH + 15}
        text="weak"
        style={{
          fontSize: 14,
          fill: t.inkSoft,
          textAnchor: "start",
          dominantBaseline: "central",
        }}
      />
      <ChartsText
        x={legendX + legendW}
        y={legendY + legendH + 15}
        text="strong"
        style={{
          fontSize: 14,
          fill: t.inkSoft,
          textAnchor: "end",
          dominantBaseline: "central",
        }}
      />
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div
      style={{
        width,
        height,
        background: t.pageBg,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          fontWeight: 600,
          color: t.ink,
        }}
      >
        Electric Dipole Field Lines · streamline-basic · javascript · muix · anyplot.ai
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_HEIGHT}
        margin={MARGIN}
        sx={{
          "& .MuiLineChart-line": {
            strokeWidth: 2.75,
            strokeLinecap: "round",
          },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 0.75 },
        }}
        xAxis={segments.map((seg, idx) =>
          idx === 0
            ? {
                id: seg.axisId,
                scaleType: "linear" as const,
                data: seg.xs,
                min: X_MIN,
                max: X_MAX,
                height: 60,
                label: X_COORD,
                labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
                tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
              }
            : {
                id: seg.axisId,
                scaleType: "linear" as const,
                data: seg.xs,
                min: X_MIN,
                max: X_MAX,
                position: "none" as const,
              },
        )}
        yAxis={[
          {
            scaleType: "linear",
            min: Y_MIN,
            max: Y_MAX,
            width: 84,
            label: Y_COORD,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        series={segments.map((seg) => ({
          type: "line" as const,
          data: seg.ys,
          xAxisId: seg.axisId,
          color: seg.color,
          curve: "linear" as const,
          showMark: false,
        }))}
      >
        <ChartsGrid horizontal />
        <LinePlot skipAnimation />
        <FieldOverlay />
        <ChartsXAxis axisId={sharedAxisId} />
        <ChartsYAxis />
      </ChartsContainer>
    </div>
  );
}
