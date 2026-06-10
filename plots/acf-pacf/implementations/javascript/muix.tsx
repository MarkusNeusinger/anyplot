// anyplot.ai
// acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: 84/100 | Created: 2026-06-10
//# anyplot-orientation: landscape
// anyplot.ai
// acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
// Library: MUI X Charts | React | Node 22
// License: @mui/x-charts — MIT (community). Pro/Premium are out of scope.
// Quality: pending | Created: 2026-06-10

import { BarChart } from "@mui/x-charts/BarChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";

const t = window.ANYPLOT_TOKENS;

// --- Deterministic LCG RNG (seed = 42) ---------------------------------------
function lcgRng(seed) {
  let s = seed >>> 0;
  return () => {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

function randn(rng) {
  const u = Math.max(rng(), 1e-10);
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rng());
}

// --- AR(2) time series: x_t = 0.65·x_{t-1} + 0.15·x_{t-2} + ε_t -----------
const rng = lcgRng(42);
const N = 300;
const ts = [0, randn(rng) * 0.5];
for (let i = 2; i < N; i++) {
  ts.push(0.65 * ts[i - 1] + 0.15 * ts[i - 2] + randn(rng));
}

// Centre and scale
const mu = ts.reduce((a, b) => a + b, 0) / N;
const cx = ts.map((x) => x - mu);
const c0 = cx.reduce((s, v) => s + v * v, 0) / N;

// ACF at lag h
function acfAt(h) {
  let s = 0;
  for (let i = h; i < N; i++) s += cx[i] * cx[i - h];
  return s / (N * c0);
}

const MAX_LAG = 30;
const rho = Array.from({ length: MAX_LAG + 1 }, (_, k) => acfAt(k));

// PACF via Durbin–Levinson recursion
function computePACF(rhoArr, maxLag) {
  const pacf = [1, rhoArr[1]];
  let phi = [rhoArr[1]];
  for (let k = 2; k <= maxLag; k++) {
    let num = rhoArr[k];
    let den = 1;
    for (let j = 0; j < k - 1; j++) {
      num -= phi[j] * rhoArr[k - 1 - j];
      den -= phi[j] * rhoArr[j + 1];
    }
    const pkk = den !== 0 ? num / den : 0;
    pacf.push(pkk);
    const next = Array(k).fill(0);
    next[k - 1] = pkk;
    for (let j = 0; j < k - 1; j++) next[j] = phi[j] - pkk * phi[k - 2 - j];
    phi = next;
  }
  return pacf;
}

const pacf = computePACF(rho, MAX_LAG);

// 95% CI: ±1.96 / √N
const CI = 1.96 / Math.sqrt(N);

const round4 = (v) => Math.round(v * 10000) / 10000;

const acfLags = Array.from({ length: MAX_LAG + 1 }, (_, i) => String(i));
const pacfLags = Array.from({ length: MAX_LAG }, (_, i) => String(i + 1));
const acfData = rho.map(round4);
const pacfData = pacf.slice(1).map(round4);

// --- Chart -------------------------------------------------------------------
export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;

  const TITLE_H = 54;
  const PANEL_H = Math.floor((H - TITLE_H - 6) / 2);

  const barColor = t.palette[0]; // #009E73 — brand green

  const ciLineStyle = {
    stroke: t.inkSoft,
    strokeDasharray: "7 4",
    strokeWidth: 1.5,
    strokeOpacity: 0.85,
  };

  const zeroLineStyle = {
    stroke: t.inkSoft,
    strokeWidth: 0.7,
    strokeOpacity: 0.45,
  };

  const tickStyle = { fontSize: 12, fill: t.inkSoft };
  const labelStyle = { fontSize: 14, fill: t.ink };

  const axisLineSx = {
    "& .MuiChartsAxis-line": { stroke: t.grid },
  };

  const xAxisBase = {
    scaleType: "band" as const,
    categoryGapRatio: 0.62,
    tickLabelStyle: tickStyle,
  };

  const yAxisBase = {
    tickMinStep: 0.25,
    tickLabelStyle: tickStyle,
    labelStyle,
  };

  return (
    <div
      style={{
        width: W,
        height: H,
        background: t.pageBg,
        display: "flex",
        flexDirection: "column",
        fontFamily: "'Roboto', 'Helvetica Neue', Arial, sans-serif",
      }}
    >
      {/* Title */}
      <div
        style={{
          height: TITLE_H,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          fontWeight: 600,
          color: t.ink,
          letterSpacing: 0.15,
        }}
      >
        AR(2) Process · acf-pacf · javascript · muix · anyplot.ai
      </div>

      {/* ACF panel */}
      <div style={{ height: PANEL_H, flexShrink: 0 }}>
        <BarChart
          width={W}
          height={PANEL_H}
          skipAnimation
          colors={[barColor]}
          xAxis={[{ ...xAxisBase, data: acfLags }]}
          yAxis={[{ ...yAxisBase, label: "ACF", min: -0.35, max: 1.05 }]}
          series={[{ data: acfData, label: "ACF" }]}
          margin={{ top: 20, bottom: 28, left: 80, right: 65 }}
          slotProps={{ legend: { hidden: true } }}
          sx={axisLineSx}
        >
          <ChartsReferenceLine
            y={CI}
            lineStyle={ciLineStyle}
            label="95% CI"
            labelStyle={{ fontSize: 11, fill: t.inkSoft }}
            labelAlign="end"
          />
          <ChartsReferenceLine y={-CI} lineStyle={ciLineStyle} />
          <ChartsReferenceLine y={0} lineStyle={zeroLineStyle} />
        </BarChart>
      </div>

      {/* PACF panel */}
      <div style={{ flex: 1 }}>
        <BarChart
          width={W}
          height={PANEL_H}
          skipAnimation
          colors={[barColor]}
          xAxis={[{
            ...xAxisBase,
            data: pacfLags,
            label: "Lag",
            labelStyle,
          }]}
          yAxis={[{ ...yAxisBase, label: "PACF" }]}
          series={[{ data: pacfData, label: "PACF" }]}
          margin={{ top: 10, bottom: 50, left: 80, right: 65 }}
          slotProps={{ legend: { hidden: true } }}
          sx={axisLineSx}
        >
          <ChartsReferenceLine y={CI} lineStyle={ciLineStyle} />
          <ChartsReferenceLine y={-CI} lineStyle={ciLineStyle} />
          <ChartsReferenceLine y={0} lineStyle={zeroLineStyle} />
        </BarChart>
      </div>
    </div>
  );
}
