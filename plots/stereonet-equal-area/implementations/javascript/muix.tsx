// anyplot.ai
// stereonet-equal-area: Structural Geology Stereonet (Equal-Area Projection)
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 94/100 | Created: 2026-06-16
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ScatterPlot } from "@mui/x-charts/ScatterChart";
import { ChartsTooltip } from "@mui/x-charts/ChartsTooltip";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const R = 1.45;
const STEPS = 180;
const NX = 80;
const NY = 80;
const K_KAMB = 28;
const LEVEL_FRACS = [0.16, 0.3, 0.48, 0.7];
const CARDINALS: Array<[string, number]> = [
  ["N", 0],
  ["E", 90],
  ["S", 180],
  ["W", 270],
];
const DEG_LABELS = [30, 60, 120, 150, 210, 240, 300, 330];

// Columns: set these to your data's column names
const STRIKE = "Strike (°)"; // role: strike
const DIP = "Dip (°)"; // role: dip
const DIP_DIRECTION = "Dip Direction (°)"; // role: dip_direction
const FEATURE_TYPE = "Feature Type"; // role: feature_type

// Data: replace this block with your own records
const featureSeeds = [
  { name: "Bedding", n: 46, dip: 24, dipDir: 118, sDip: 6, sDir: 14 },
  { name: "Joint set", n: 38, dip: 78, dipDir: 48, sDip: 5, sDir: 10 },
  { name: "Foliation", n: 34, dip: 62, dipDir: 305, sDip: 7, sDir: 12 },
  { name: "Fault", n: 26, dip: 54, dipDir: 212, sDip: 6, sDir: 11 },
];

let lcgSeed = 20260616 >>> 0;
const data: Array<Record<string, string | number>> = [];
for (const f of featureSeeds) {
  for (let i = 0; i < f.n; i++) {
    lcgSeed = (1664525 * lcgSeed + 1013904223) >>> 0;
    const u1 = Math.max(1e-9, lcgSeed / 4294967296);
    lcgSeed = (1664525 * lcgSeed + 1013904223) >>> 0;
    const u2 = lcgSeed / 4294967296;
    const zDip = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);

    lcgSeed = (1664525 * lcgSeed + 1013904223) >>> 0;
    const u3 = Math.max(1e-9, lcgSeed / 4294967296);
    lcgSeed = (1664525 * lcgSeed + 1013904223) >>> 0;
    const u4 = lcgSeed / 4294967296;
    const zDir = Math.sqrt(-2 * Math.log(u3)) * Math.cos(2 * Math.PI * u4);

    const dipVal = Math.max(2, Math.min(89, f.dip + zDip * f.sDip));
    const dipDirVal = (((f.dipDir + zDir * f.sDir) % 360) + 360) % 360;
    const strikeVal = (dipDirVal + 270) % 360;

    data.push({
      [STRIKE]: Number(strikeVal.toFixed(1)),
      [DIP]: Number(dipVal.toFixed(1)),
      [DIP_DIRECTION]: Number(dipDirVal.toFixed(1)),
      [FEATURE_TYPE]: f.name,
    });
  }
}

// Plot: reads only data and the constants above
const featureNames: string[] = [];
for (const row of data) {
  const fn = String(row[FEATURE_TYPE]);
  if (!featureNames.includes(fn)) featureNames.push(fn);
}

const allPoles: Array<{
  feature: string;
  dip: number;
  dipDir: number;
  pn: number;
  pe: number;
  pd: number;
  x: number;
  y: number;
}> = [];

for (const row of data) {
  const feature = String(row[FEATURE_TYPE]);
  const dipDeg = Number(row[DIP]);
  const dipDirDeg = Number(row[DIP_DIRECTION]);
  const pl = ((90 - dipDeg) * Math.PI) / 180;
  const tr = ((dipDirDeg + 180) * Math.PI) / 180;
  let pn = Math.cos(pl) * Math.cos(tr);
  let pe = Math.cos(pl) * Math.sin(tr);
  let pd = Math.sin(pl);
  if (pd < 0) {
    pn = -pn;
    pe = -pe;
    pd = -pd;
  }
  const plunge = Math.asin(Math.max(-1, Math.min(1, pd)));
  const trend = Math.atan2(pe, pn);
  const theta = Math.PI / 2 - plunge;
  const r = Math.SQRT2 * Math.sin(theta / 2);
  allPoles.push({
    feature,
    dip: dipDeg,
    dipDir: dipDirDeg,
    pn,
    pe,
    pd,
    x: r * Math.sin(trend),
    y: r * Math.cos(trend),
  });
}

const series = featureNames.map((fn, fIdx) => {
  const pts = allPoles
    .filter((p) => p.feature === fn)
    .map((p, i) => ({ x: p.x, y: p.y, id: `${fn}-${i}` }));
  return {
    type: "scatter" as const,
    label: fn,
    color: t.palette[fIdx % t.palette.length],
    markerSize: 5,
    data: pts,
  };
});

// Compute great-circle polylines for each feature's mean pole and for the net graticule
const planeSpecs: Array<{
  kind: "mean" | "net";
  color: string;
  pn: number;
  pe: number;
  pd: number;
}> = [];

featureNames.forEach((fn, fIdx) => {
  const group = allPoles.filter((p) => p.feature === fn);
  let sumN = 0;
  let sumE = 0;
  let sumD = 0;
  for (const p of group) {
    sumN += p.pn;
    sumE += p.pe;
    sumD += p.pd;
  }
  const mag = Math.hypot(sumN, sumE, sumD) || 1;
  planeSpecs.push({
    kind: "mean",
    color: t.palette[fIdx % t.palette.length],
    pn: sumN / mag,
    pe: sumE / mag,
    pd: sumD / mag,
  });
});

for (let dip = 10; dip <= 80; dip += 10) {
  for (const dipDir of [90, 270]) {
    const pl = ((90 - dip) * Math.PI) / 180;
    const tr = ((dipDir + 180) * Math.PI) / 180;
    planeSpecs.push({
      kind: "net",
      color: t.grid,
      pn: Math.cos(pl) * Math.cos(tr),
      pe: Math.cos(pl) * Math.sin(tr),
      pd: Math.sin(pl),
    });
  }
}

const meanPlanes: Array<{
  color: string;
  segs: Array<Array<{ x: number; y: number }>>;
}> = [];
const netGreatCircles: Array<Array<Array<{ x: number; y: number }>>> = [];

for (const ps of planeSpecs) {
  const pm = Math.hypot(ps.pn, ps.pe, ps.pd) || 1;
  const P = [ps.pn / pm, ps.pe / pm, ps.pd / pm];
  const seed = Math.abs(P[2]) < 0.9 ? [0, 0, 1] : [0, 1, 0];
  const ux0 = P[1] * seed[2] - P[2] * seed[1];
  const uy0 = P[2] * seed[0] - P[0] * seed[2];
  const uz0 = P[0] * seed[1] - P[1] * seed[0];
  const um = Math.hypot(ux0, uy0, uz0) || 1;
  const u = [ux0 / um, uy0 / um, uz0 / um];
  const v = [
    P[1] * u[2] - P[2] * u[1],
    P[2] * u[0] - P[0] * u[2],
    P[0] * u[1] - P[1] * u[0],
  ];

  const segs: Array<Array<{ x: number; y: number }>> = [];
  let cur: Array<{ x: number; y: number }> = [];
  let prev: { x: number; y: number } | null = null;
  for (let i = 0; i <= STEPS; i++) {
    const phi = (i / STEPS) * 2 * Math.PI;
    const cphi = Math.cos(phi);
    const sphi = Math.sin(phi);
    let cn = cphi * u[0] + sphi * v[0];
    let ce = cphi * u[1] + sphi * v[1];
    let cd = cphi * u[2] + sphi * v[2];
    if (cd < 0) {
      cn = -cn;
      ce = -ce;
      cd = -cd;
    }
    const plunge = Math.asin(Math.max(-1, Math.min(1, cd)));
    const trend = Math.atan2(ce, cn);
    const theta = Math.PI / 2 - plunge;
    const r = Math.SQRT2 * Math.sin(theta / 2);
    const pt = { x: r * Math.sin(trend), y: r * Math.cos(trend) };
    if (prev && Math.hypot(pt.x - prev.x, pt.y - prev.y) > 0.25) {
      if (cur.length > 1) segs.push(cur);
      cur = [];
    }
    cur.push(pt);
    prev = pt;
  }
  if (cur.length > 1) segs.push(cur);
  if (ps.kind === "mean") {
    meanPlanes.push({ color: ps.color, segs });
  } else {
    netGreatCircles.push(segs);
  }
}

// Small circles for Schmidt net graticule around North-South axis [1, 0, 0]
const netSmallCircles: Array<Array<Array<{ x: number; y: number }>>> = [];
for (let betaDeg = 10; betaDeg <= 80; betaDeg += 10) {
  for (const beta of [
    (betaDeg * Math.PI) / 180,
    ((180 - betaDeg) * Math.PI) / 180,
  ]) {
    const cb = Math.cos(beta);
    const sb = Math.sin(beta);
    const segs: Array<Array<{ x: number; y: number }>> = [];
    let cur: Array<{ x: number; y: number }> = [];
    let prev: { x: number; y: number } | null = null;
    for (let i = 0; i <= STEPS; i++) {
      const phi = (i / STEPS) * 2 * Math.PI;
      // Axis A = [1, 0, 0], e1 = [0, 1, 0], e2 = [0, 0, 1]
      const cn = cb;
      const ce = sb * Math.cos(phi);
      const cd = sb * Math.sin(phi);
      if (cd < 0) {
        if (cur.length > 1) segs.push(cur);
        cur = [];
        prev = null;
        continue;
      }
      const plunge = Math.asin(Math.max(-1, Math.min(1, cd)));
      const trend = Math.atan2(ce, cn);
      const theta = Math.PI / 2 - plunge;
      const r = Math.SQRT2 * Math.sin(theta / 2);
      const pt = { x: r * Math.sin(trend), y: r * Math.cos(trend) };
      if (prev && Math.hypot(pt.x - prev.x, pt.y - prev.y) > 0.25) {
        if (cur.length > 1) segs.push(cur);
        cur = [];
      }
      cur.push(pt);
      prev = pt;
    }
    if (cur.length > 1) segs.push(cur);
    netSmallCircles.push(segs);
  }
}

const netAllSegs = netGreatCircles.concat(netSmallCircles);

// Kamb-style density field and marching squares contours
const density = new Float64Array(NX * NY);
let maxDensity = 0;
for (let j = 0; j < NY; j++) {
  const Y = -1.0 + (j * 2) / (NY - 1);
  for (let i = 0; i < NX; i++) {
    const X = -1.0 + (i * 2) / (NX - 1);
    const r = Math.hypot(X, Y);
    if (r > 1.0) continue;
    const theta = 2 * Math.asin(Math.min(1, r / Math.SQRT2));
    const az = Math.atan2(X, Y);
    const vn = Math.sin(theta) * Math.cos(az);
    const ve = Math.sin(theta) * Math.sin(az);
    const vd = Math.cos(theta);
    let s = 0;
    for (const p of allPoles) {
      const dot = vn * p.pn + ve * p.pe + vd * p.pd;
      s += Math.exp(K_KAMB * (dot * dot - 1));
    }
    density[j * NX + i] = s;
    if (s > maxDensity) maxDensity = s;
  }
}

const seqR1 = parseInt(t.seq[0].slice(1, 3), 16);
const seqG1 = parseInt(t.seq[0].slice(3, 5), 16);
const seqB1 = parseInt(t.seq[0].slice(5, 7), 16);
const seqR2 = parseInt(t.seq[1].slice(1, 3), 16);
const seqG2 = parseInt(t.seq[1].slice(3, 5), 16);
const seqB2 = parseInt(t.seq[1].slice(5, 7), 16);

const contours = LEVEL_FRACS.map((lf, idx) => {
  const level = lf * maxDensity;
  const segs: Array<[number, number, number, number]> = [];
  for (let j = 0; j < NY - 1; j++) {
    const y0 = -1.0 + (j * 2) / (NY - 1);
    const y1 = -1.0 + ((j + 1) * 2) / (NY - 1);
    for (let i = 0; i < NX - 1; i++) {
      const x0 = -1.0 + (i * 2) / (NX - 1);
      const x1 = -1.0 + ((i + 1) * 2) / (NX - 1);
      const v0 = density[j * NX + i];
      const v1 = density[j * NX + i + 1];
      const v2 = density[(j + 1) * NX + i + 1];
      const v3 = density[(j + 1) * NX + i];
      let code = 0;
      if (v0 >= level) code |= 1;
      if (v1 >= level) code |= 2;
      if (v2 >= level) code |= 4;
      if (v3 >= level) code |= 8;
      if (code === 0 || code === 15) continue;

      const tB = (level - v0) / (v1 - v0 || 1);
      const eB: [number, number] = [x0 + tB * (x1 - x0), y0];
      const tR = (level - v1) / (v2 - v1 || 1);
      const eR: [number, number] = [x1, y0 + tR * (y1 - y0)];
      const tT = (level - v2) / (v3 - v2 || 1);
      const eT: [number, number] = [x1 + tT * (x0 - x1), y1];
      const tL = (level - v3) / (v0 - v3 || 1);
      const eL: [number, number] = [x0, y1 + tL * (y0 - y1)];

      if (code === 1 || code === 14) segs.push([eL[0], eL[1], eB[0], eB[1]]);
      else if (code === 2 || code === 13) segs.push([eB[0], eB[1], eR[0], eR[1]]);
      else if (code === 3 || code === 12) segs.push([eL[0], eL[1], eR[0], eR[1]]);
      else if (code === 4 || code === 11) segs.push([eR[0], eR[1], eT[0], eT[1]]);
      else if (code === 5) {
        segs.push([eL[0], eL[1], eT[0], eT[1]]);
        segs.push([eB[0], eB[1], eR[0], eR[1]]);
      } else if (code === 6 || code === 9) segs.push([eB[0], eB[1], eT[0], eT[1]]);
      else if (code === 7 || code === 8) segs.push([eL[0], eL[1], eT[0], eT[1]]);
      else if (code === 10) {
        segs.push([eL[0], eL[1], eB[0], eB[1]]);
        segs.push([eR[0], eR[1], eT[0], eT[1]]);
      }
    }
  }
  const f = idx / (LEVEL_FRACS.length - 1);
  const r = Math.round(seqR1 + (seqR2 - seqR1) * f)
    .toString(16)
    .padStart(2, "0");
  const g = Math.round(seqG1 + (seqG2 - seqG1) * f)
    .toString(16)
    .padStart(2, "0");
  const b = Math.round(seqB1 + (seqB2 - seqB1) * f)
    .toString(16)
    .padStart(2, "0");
  return {
    segs,
    color: `#${r}${g}${b}`,
    w: 1.4 + idx * 0.6,
    op: 0.45 + idx * 0.16,
  };
});

function NetGrid() {
  const xs = useXScale() as (v: number) => number;
  const ys = useYScale() as (v: number) => number;
  const cx = xs(0);
  const cy = ys(0);
  const rPx = Math.abs(xs(1) - xs(0));
  return (
    <g>
      {netAllSegs.map((segs, k) => (
        <path
          key={k}
          d={segs
            .map(
              (poly) =>
                "M" +
                poly
                  .map((pt) => `${xs(pt.x).toFixed(1)} ${ys(pt.y).toFixed(1)}`)
                  .join(" L"),
            )
            .join(" ")}
          fill="none"
          stroke={t.grid}
          strokeWidth={1}
        />
      ))}
      <line x1={xs(-1)} y1={cy} x2={xs(1)} y2={cy} stroke={t.grid} strokeWidth={1} />
      <line x1={cx} y1={ys(-1)} x2={cx} y2={ys(1)} stroke={t.grid} strokeWidth={1} />
      <circle cx={cx} cy={cy} r={rPx} fill="none" stroke={t.ink} strokeWidth={2.5} />
    </g>
  );
}

function DensityContours() {
  const xs = useXScale() as (v: number) => number;
  const ys = useYScale() as (v: number) => number;
  return (
    <g>
      {contours.map((c, k) => (
        <path
          key={k}
          d={c.segs
            .map(
              (s) =>
                `M${xs(s[0]).toFixed(1)} ${ys(s[1]).toFixed(1)} L${xs(s[2]).toFixed(1)} ${ys(s[3]).toFixed(1)}`,
            )
            .join(" ")}
          fill="none"
          stroke={c.color}
          strokeWidth={c.w}
          strokeOpacity={c.op}
          strokeLinecap="round"
        />
      ))}
    </g>
  );
}

function GreatCircles() {
  const xs = useXScale() as (v: number) => number;
  const ys = useYScale() as (v: number) => number;
  return (
    <g>
      {meanPlanes.map((mp, k) => (
        <path
          key={k}
          d={mp.segs
            .map(
              (poly) =>
                "M" +
                poly
                  .map((pt) => `${xs(pt.x).toFixed(1)} ${ys(pt.y).toFixed(1)}`)
                  .join(" L"),
            )
            .join(" ")}
          fill="none"
          stroke={mp.color}
          strokeWidth={3.5}
          strokeOpacity={0.95}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      ))}
    </g>
  );
}

function Chrome() {
  const xs = useXScale() as (v: number) => number;
  const ys = useYScale() as (v: number) => number;
  const ticks = [];
  for (let deg = 0; deg < 360; deg += 10) {
    const major = deg % 30 === 0;
    const a = (deg * Math.PI) / 180;
    const x1 = xs(1.0 * Math.sin(a));
    const y1 = ys(1.0 * Math.cos(a));
    const r2 = major ? 1.04 : 1.022;
    const x2 = xs(r2 * Math.sin(a));
    const y2 = ys(r2 * Math.cos(a));
    ticks.push(
      <line
        key={`t${deg}`}
        x1={x1}
        y1={y1}
        x2={x2}
        y2={y2}
        stroke={t.inkSoft}
        strokeWidth={major ? 1.6 : 1}
      />,
    );
  }
  return (
    <g>
      {ticks}
      {DEG_LABELS.map((deg) => {
        const a = (deg * Math.PI) / 180;
        const x = xs(1.11 * Math.sin(a));
        const y = ys(1.11 * Math.cos(a));
        return (
          <text
            key={`d${deg}`}
            x={x}
            y={y}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={14}
            fill={t.inkSoft}
          >
            {deg}°
          </text>
        );
      })}
      {CARDINALS.map(([label, deg]) => {
        const a = (deg * Math.PI) / 180;
        const x = xs(1.085 * Math.sin(a));
        const y = ys(1.085 * Math.cos(a));
        return (
          <text
            key={label}
            x={x}
            y={y}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={22}
            fontWeight={700}
            fill={t.ink}
          >
            {label}
          </text>
        );
      })}
    </g>
  );
}

function Annotations() {
  const xs = useXScale() as (v: number) => number;
  const ys = useYScale() as (v: number) => number;
  const legendStart = -1.18;
  const legendStep = 0.62;
  return (
    <g>
      <text
        x={xs(0)}
        y={ys(1.34)}
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize={22}
        fontWeight={600}
        fill={t.ink}
      >
        Structural Geology Stereonet · stereonet-equal-area · javascript · muix · anyplot.ai
      </text>
      <text
        x={xs(0)}
        y={ys(1.2)}
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize={15}
        fill={t.inkSoft}
      >
        Lower-hemisphere equal-area (Schmidt) net · poles to planes with mean great circles
      </text>
      {featureNames.map((fn, i) => {
        const x = legendStart + i * legendStep;
        return (
          <g key={fn}>
            <circle
              cx={xs(x)}
              cy={ys(-1.18)}
              r={7}
              fill={t.palette[i % t.palette.length]}
            />
            <text
              x={xs(x) + 14}
              y={ys(-1.18)}
              dominantBaseline="middle"
              fontSize={15}
              fill={t.inkSoft}
            >
              {fn}
            </text>
          </g>
        );
      })}
      <text
        x={xs(0)}
        y={ys(-1.34)}
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize={14}
        fill={t.inkSoft}
      >
        Density contours: Imprint sequential ramp (exponential Kamb smoothing of pole axes)
      </text>
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  return (
    <div style={{ width, height, background: t.pageBg }}>
      <ChartsContainer
        width={width}
        height={height}
        margin={{ top: 12, right: 12, bottom: 12, left: 12 }}
        series={series}
        xAxis={[{ scaleType: "linear", min: -R, max: R, position: "none" }]}
        yAxis={[{ scaleType: "linear", min: -R, max: R, position: "none" }]}
      >
        <NetGrid />
        <DensityContours />
        <GreatCircles />
        <ScatterPlot skipAnimation />
        <Chrome />
        <Annotations />
        <ChartsTooltip trigger="item" />
      </ChartsContainer>
    </div>
  );
}
