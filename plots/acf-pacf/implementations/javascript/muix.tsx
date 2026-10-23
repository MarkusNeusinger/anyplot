// anyplot.ai
// acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: pending | Created: 2026-06-10

import { BarChart } from "@mui/x-charts/BarChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";

const t = window.ANYPLOT_TOKENS;

// Constants
const MAX_LAG = 30; // number of lags shown in both panels
const Y_PAD = 0.15; // share of the value span added above and below each panel

// Columns: set these to your data's column names
const VALUE = "Observation Value"; // role: value

// Data: replace this block with your own records, one object per row
// AR(2) time series: x_t = 0.65 * x_{t-1} + 0.15 * x_{t-2} + e_t
const data = (() => {
  function lcgRng(seed: number) {
    let s = seed >>> 0;
    return () => {
      s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
      return s / 4294967296;
    };
  }

  function randn(rng: () => number) {
    const u = Math.max(rng(), 1e-10);
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rng());
  }

  const rng = lcgRng(42);
  const count = 300;
  const series = [0, randn(rng) * 0.5];
  for (let i = 2; i < count; i += 1) {
    series.push(0.65 * series[i - 1] + 0.15 * series[i - 2] + randn(rng));
  }
  return series.map((v) => ({ [VALUE]: v }));
})();

// Plot: reads only data and the constants above
const ts = data.map((d) => d[VALUE]);
const N = ts.length;

const mu = ts.reduce((a, b) => a + b, 0) / N;
const cx = ts.map((x) => x - mu);
const c0 = cx.reduce((s, v) => s + v * v, 0) / N;

function acfAt(h: number) {
  let s = 0;
  for (let i = h; i < N; i += 1) s += cx[i] * cx[i - h];
  return s / (N * c0);
}

const rho =Array.from({ length: MAX_LAG + 1 }, (_, k) => acfAt(k));

function computePACF(rhoArr: number[], maxLag: number) {
  const pacf = [1, rhoArr[1]];
  let phi = [rhoArr[1]];
  for (let k = 2; k <= maxLag; k += 1) {
    let num = rhoArr[k];
    let den = 1;
    for (let j = 0; j < k - 1; j += 1) {
      num -= phi[j] * rhoArr[k - 1 - j];
      den -= phi[j] * rhoArr[j + 1];
    }
    const pkk = den !== 0 ? num / den : 0;
    pacf.push(pkk);
    const next = Array(k).fill(0);
    next[k - 1] = pkk;
    for (let j = 0; j < k - 1; j += 1) next[j] = phi[j] - pkk * phi[k - 2 - j];
    phi = next;
  }
  return pacf;
}

const pacf = computePACF(rho, MAX_LAG);

// 95% CI: +/- 1.96 / sqrt(N)
const CI = 1.96 / Math.sqrt(N);

const round4 = (v: number) => Math.round(v * 10000) / 10000;

// Share the exact 0..MAX_LAG axis across both panels so every lag lines up
// vertically; PACF starts at lag 1 (null at lag 0).
const sharedLags = Array.from({ length: MAX_LAG + 1 }, (_, i) => String(i));
const acfData = rho.map(round4);
const pacfData: (number | null)[] = [null, ...pacf.slice(1).map(round4)];

// Each panel's y range covers its bars and the +/- CI band, padded by Y_PAD.
function paddedLimits(values: (number | null)[]) {
  const finite = values.filter((v): v is number => v != null && Number.isFinite(v));
  const lo = Math.min(-CI, ...finite);
  const hi = Math.max(CI, ...finite);
  const pad = Y_PAD * (hi - lo);
  return { min: lo - pad, max: hi + pad };
}
const acfLimits = paddedLimits(acfData);
const pacfLimits = paddedLimits(pacfData);

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;

  const TITLE_H = 54;
  const PANEL_H = Math.floor((H - TITLE_H - 6) / 2);

  const barColor = t.palette[0];

  const ciLineStyle = {
    stroke: t.inkSoft,
    strokeDasharray: "7 4",
    strokeWidth: 1.5,
    strokeOpacity: 0.85,
  };

  const zeroLineStyle = {
    stroke: t.inkSoft,
    strokeWidth: 0.9,
    strokeOpacity: 0.55,
  };

  const tickStyle = { fontSize: 12, fill: t.inkSoft };
  const labelStyle = { fontSize: 15, fill: t.ink };

  const axisLineSx = {
    "& .MuiChartsAxis-line": { stroke: t.inkSoft },
    "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
  };

  const xAxisBase = {
    scaleType: "band" as const,
    categoryGapRatio: 0.9,
    tickLabelStyle: tickStyle,
  };

  const yAxisBase = {
    width: 72,
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
          disableHitArea
          hideLegend
          colors={[barColor]}
          xAxis={[{ ...xAxisBase, height: 36, data: sharedLags }]}
          yAxis={[{ ...yAxisBase, label: "ACF", ...acfLimits }]}
          series={[{ data: acfData, label: "ACF" }]}
          margin={{ top: 18, bottom: 12, left: 60, right: 65 }}
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
          disableHitArea
          hideLegend
          colors={[barColor]}
          xAxis={[
            {
              ...xAxisBase,
              height: 54,
              data: sharedLags,
              label: "Lag",
              labelStyle,
            },
          ]}
          yAxis={[{ ...yAxisBase, label: "PACF", ...pacfLimits }]}
          series={[{ data: pacfData, label: "PACF" }]}
          margin={{ top: 12, bottom: 20, left: 60, right: 65 }}
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
