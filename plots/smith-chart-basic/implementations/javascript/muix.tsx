// anyplot.ai
// smith-chart-basic: Smith Chart for RF/Impedance
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-02
//# anyplot-orientation: square

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsText } from "@mui/x-charts/ChartsText";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "smith-chart-basic · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 70;
const RESISTANCE_VALUES = [0.2, 0.5, 1, 2, 5];
const REACTANCE_VALUES = [0.2, 0.5, 1, 2, 5];
const GAMMA_MAX = 1.15;
const CIRCLE_STEPS = 120;
const ARC_STEPS = 400;
const BASE_MARGIN = 50;
const LABEL_OFFSET_PX = 26;

// Columns: set these to your data's column names
const FREQUENCY = "Frequency (GHz)"; // role: frequency
const Z_REAL = "Resistance R (Ω)"; // role: z_real
const Z_IMAG = "Reactance X (Ω)"; // role: z_imag

// Data: replace this block with your own records
const Z0 = 50; // role: z0
const INDUCTANCE = 5e-9;
const CAPACITANCE = 0.4e-12;
const FREQ_START_GHZ = 1;
const FREQ_END_GHZ = 6;
const FREQ_STEP_GHZ = 0.125;

const data = [];
for (let f = FREQ_START_GHZ; f <= FREQ_END_GHZ + 1e-9; f += FREQ_STEP_GHZ) {
  const fGHz = Math.round(f * 1000) / 1000;
  const omega = 2 * Math.PI * fGHz * 1e9;
  const resistance = 35 + 3 * (fGHz - FREQ_START_GHZ);
  const reactance = omega * INDUCTANCE - 1 / (omega * CAPACITANCE);
  data.push({
    [FREQUENCY]: fGHz,
    [Z_REAL]: resistance,
    [Z_IMAG]: reactance,
  });
}

// Plot: reads only data and the constants above
const freqUnitMatch = /\(([^)]+)\)/.exec(FREQUENCY);
const freqUnit = freqUnitMatch ? ` ${freqUnitMatch[1]}` : "";

const gammaPoints = data.map((row) => {
  const fVal = Number(row[FREQUENCY]);
  const zReal = Number(row[Z_REAL]) / Z0;
  const zImag = Number(row[Z_IMAG]) / Z0;
  const denomReal = zReal + 1;
  const denomImag = zImag;
  const denomMagSq = denomReal * denomReal + denomImag * denomImag;
  const numReal = zReal - 1;
  const numImag = zImag;
  return {
    fVal,
    re: (numReal * denomReal + numImag * denomImag) / denomMagSq,
    im: (numImag * denomReal - numReal * denomImag) / denomMagSq,
  };
});

const labeledWaypoints = gammaPoints.filter((p) => Math.abs(p.fVal - Math.round(p.fVal)) < 1e-6);

const unitCirclePts = Array.from({ length: CIRCLE_STEPS + 1 }, (_, i) => {
  const theta = (i / CIRCLE_STEPS) * 2 * Math.PI;
  return [Math.cos(theta), Math.sin(theta)];
});

const resistanceCircles = RESISTANCE_VALUES.map((r) => {
  const cx = r / (1 + r);
  const rad = 1 / (1 + r);
  const pts = Array.from({ length: CIRCLE_STEPS + 1 }, (_, i) => {
    const theta = (i / CIRCLE_STEPS) * 2 * Math.PI;
    return [cx + rad * Math.cos(theta), rad * Math.sin(theta)];
  });
  return { r, pts };
});

const reactanceArcs = REACTANCE_VALUES.flatMap((x) => [x, -x]).map((xVal) => {
  const cx = 1;
  const cy = 1 / xVal;
  const r = Math.abs(1 / xVal);
  const theta0 = Math.atan2(-cy, 0);
  const dTheta = (2 * Math.PI) / ARC_STEPS;
  const pPlusX = cx + r * Math.cos(theta0 + dTheta);
  const pPlusY = cy + r * Math.sin(theta0 + dTheta);
  const pMinusX = cx + r * Math.cos(theta0 - dTheta);
  const pMinusY = cy + r * Math.sin(theta0 - dTheta);
  const direction =
    pPlusX * pPlusX + pPlusY * pPlusY < pMinusX * pMinusX + pMinusY * pMinusY ? 1 : -1;
  const pts = [[cx + r * Math.cos(theta0), cy + r * Math.sin(theta0)]];
  for (let i = 1; i <= ARC_STEPS; i += 1) {
    const theta = theta0 + direction * dTheta * i;
    const px = cx + r * Math.cos(theta);
    const py = cy + r * Math.sin(theta);
    if (px * px + py * py > 1.0005) break;
    pts.push([px, py]);
  }
  return { xVal, pts };
});

function SmithChartLayer() {
  const xScale = useXScale();
  const yScale = useYScale();
  const brand = t.palette[0];
  const originX = xScale(0);
  const originY = yScale(0);

  const unitCircleD = unitCirclePts
    .map(([x, y], i) => `${i === 0 ? "M" : "L"} ${xScale(x)} ${yScale(y)}`)
    .join(" ");

  const locusD = gammaPoints
    .map((p, i) => `${i === 0 ? "M" : "L"} ${xScale(p.re)} ${yScale(p.im)}`)
    .join(" ");

  return (
    <g>
      <path d={unitCircleD} fill="none" stroke={t.ink} strokeWidth={2.5} />
      <line
        x1={xScale(-1)}
        y1={originY}
        x2={xScale(1)}
        y2={originY}
        stroke={t.inkSoft}
        strokeWidth={1.5}
      />

      {resistanceCircles.map(({ r, pts }) => {
        const d = pts
          .map(([x, y], i) => `${i === 0 ? "M" : "L"} ${xScale(x)} ${yScale(y)}`)
          .join(" ");
        return (
          <path
            key={`r-${r}`}
            d={d}
            fill="none"
            stroke={t.inkSoft}
            strokeWidth={1}
            opacity={0.55}
          />
        );
      })}

      {reactanceArcs.map(({ xVal, pts }) => {
        const d = pts
          .map(([x, y], i) => `${i === 0 ? "M" : "L"} ${xScale(x)} ${yScale(y)}`)
          .join(" ");
        return (
          <path
            key={`x-${xVal}`}
            d={d}
            fill="none"
            stroke={t.inkSoft}
            strokeWidth={1}
            opacity={0.55}
          />
        );
      })}

      {RESISTANCE_VALUES.map((r) => {
        const px = xScale((r - 1) / (1 + r));
        const labelOffset = r === 1 ? 26 : 18;
        return (
          <ChartsText
            key={`rl-${r}`}
            x={px}
            y={originY + labelOffset}
            text={String(r)}
            style={{ fontSize: 13, fill: t.inkSoft, textAnchor: "middle" }}
          />
        );
      })}

      {reactanceArcs.map(({ xVal, pts }) => {
        const [ax, ay] = pts[pts.length - 1];
        const px = xScale(ax * 1.06);
        const py = yScale(ay * 1.06);
        return (
          <ChartsText
            key={`xl-${xVal}`}
            x={px}
            y={py}
            text={`${xVal > 0 ? "+j" : "−j"}${Math.abs(xVal)}`}
            style={{ fontSize: 13, fill: t.inkSoft, textAnchor: "middle", dominantBaseline: "central" }}
          />
        );
      })}

      <circle cx={originX} cy={originY} r={5} fill="none" stroke={t.ink} strokeWidth={2} />
      <ChartsText
        x={originX}
        y={originY - 26}
        text="Z0"
        style={{ fontSize: 15, fill: t.ink, textAnchor: "middle", fontWeight: 500 }}
      />

      <path
        d={locusD}
        fill="none"
        stroke={brand}
        strokeWidth={3.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {labeledWaypoints.map((p) => {
        const px = xScale(p.re);
        const py = yScale(p.im);
        const dx = px - originX;
        const dy = py - originY;
        const dist = Math.hypot(dx, dy);
        const ux = dx / dist;
        const uy = dy / dist;
        const lx = px + ux * LABEL_OFFSET_PX;
        const ly = py + uy * LABEL_OFFSET_PX;
        return (
          <g key={p.fVal}>
            <circle cx={px} cy={py} r={9} fill={brand} stroke={t.pageBg} strokeWidth={2.5} />
            <ChartsText
              x={lx}
              y={ly}
              text={`${p.fVal}${freqUnit}`}
              style={{
                fontSize: 14,
                fill: t.ink,
                fontWeight: 500,
                textAnchor: ux >= 0.15 ? "start" : ux <= -0.15 ? "end" : "middle",
                dominantBaseline: uy >= 0.15 ? "hanging" : uy <= -0.15 ? "auto" : "central",
              }}
            />
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - TITLE_HEIGHT;
  const squareSide = chartHeight - 2 * BASE_MARGIN;
  const sideMargin = (width - squareSide) / 2;
  const margin = { top: BASE_MARGIN, bottom: BASE_MARGIN, left: sideMargin, right: sideMargin };

  return (
    <div
      style={{
        width,
        height,
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
          fontWeight: 500,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <ChartsContainer
        width={width}
        height={chartHeight}
        margin={margin}
        series={[]}
        skipAnimation
        disableAxisListener
        xAxis={[{ scaleType: "linear", min: -GAMMA_MAX, max: GAMMA_MAX, position: "none" }]}
        yAxis={[{ scaleType: "linear", min: -GAMMA_MAX, max: GAMMA_MAX, position: "none" }]}
      >
        <SmithChartLayer />
      </ChartsContainer>
    </div>
  );
}
