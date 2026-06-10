// anyplot.ai
// acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 87/100 | Created: 2026-06-10

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// Seeded LCG for deterministic data generation
let _seed = 42;
function _lcg() {
  _seed = (Math.imul(_seed, 1664525) + 1013904223) >>> 0;
  return _seed / 0x100000000;
}
function _randn() {
  const u1 = _lcg() + 1e-10, u2 = _lcg();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// Generate AR(2) time series: x_t = 0.6*x_{t-1} + 0.25*x_{t-2} + ε_t
// Represents daily temperature anomaly residuals (°C)
const N = 300;
const series = new Array(N).fill(0);
for (let i = 2; i < N; i++) {
  series[i] = 0.6 * series[i - 1] + 0.25 * series[i - 2] + _randn();
}

const MAX_LAG = 35;
const ci = 1.96 / Math.sqrt(N);

// Sample ACF at lags 0..MAX_LAG
const acfMean = series.reduce((s, v) => s + v, 0) / N;
const acfDenom = series.reduce((s, v) => s + (v - acfMean) ** 2, 0);
const acf = Array.from({ length: MAX_LAG + 1 }, (_, k) => {
  let num = 0;
  for (let i = k; i < N; i++) num += (series[i] - acfMean) * (series[i - k] - acfMean);
  return num / acfDenom;
});

// Sample PACF at lags 1..MAX_LAG via Durbin-Levinson recursion
const pacf = [acf[1]];
let phi = [acf[1]];
for (let k = 2; k <= MAX_LAG; k++) {
  let num = acf[k], den = 1;
  for (let j = 0; j < k - 1; j++) {
    num -= phi[j] * acf[k - 1 - j];
    den -= phi[j] * acf[j + 1];
  }
  const pkk = num / den;
  const next = new Array(k);
  for (let j = 0; j < k - 1; j++) next[j] = phi[j] - pkk * phi[k - 2 - j];
  next[k - 1] = pkk;
  phi = next;
  pacf.push(pkk);
}

// Color tokens: palette[0] = ACF green #009E73, palette[1] = PACF lavender #C475FD
const SIG_ACF    = t.palette[0];
const INSIG_ACF  = "rgba(0,158,115,0.28)";
const SIG_PACF   = t.palette[1];
const INSIG_PACF = "rgba(196,117,253,0.28)";

// Shared 36-slot category axis (lags 0–35) for both panels so bars align vertically
const lagLabels = Array.from({ length: MAX_LAG + 1 }, (_, i) => String(i));

const acfBarData = acf.map((v, i) => ({
  value: +v.toFixed(4),
  itemStyle: { color: (i === 0 || Math.abs(v) > ci) ? SIG_ACF : INSIG_ACF }
}));

// Prepend null at lag-0 slot so PACF panel columns align with ACF panel
const pacfBarData = [{ value: null, itemStyle: { color: "transparent" } }].concat(
  pacf.map((v) => ({
    value: +v.toFixed(4),
    itemStyle: { color: Math.abs(v) > ci ? SIG_PACF : INSIG_PACF }
  }))
);

// Init chart
const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",

  title: {
    text: "acf-pacf · javascript · echarts · anyplot.ai",
    subtext: "AR(2) daily temperature anomalies  ·  N = 300  ·  95% CI shown",
    left: "center",
    top: 16,
    textStyle:    { color: t.ink,     fontSize: 22, fontWeight: "600" },
    subtextStyle: { color: t.inkSoft, fontSize: 14  }
  },

  // Two stacked grids (1600 × 900 CSS canvas)
  grid: [
    { left: 85, right: 50, top: 78,  bottom: 472 }, // ACF
    { left: 85, right: 50, top: 470, bottom: 62  }  // PACF
  ],

  xAxis: [
    {
      gridIndex: 0,
      type: "category",
      data: lagLabels,
      axisLabel: { show: false },
      axisLine:  { lineStyle: { color: t.inkSoft } },
      axisTick:  { show: false },
      splitLine: { show: false }
    },
    {
      gridIndex: 1,
      type: "category",
      data: lagLabels,
      name: "Lag",
      nameLocation: "middle",
      nameGap: 38,
      nameTextStyle: { color: t.ink, fontSize: 15, fontWeight: "500" },
      axisLabel: { color: t.inkSoft, fontSize: 13 },
      axisLine:  { lineStyle: { color: t.inkSoft } },
      axisTick:  { show: false },
      splitLine: { show: false }
    }
  ],

  yAxis: [
    {
      gridIndex: 0,
      type: "value",
      name: "ACF",
      nameLocation: "middle",
      nameGap: 52,
      nameTextStyle: { color: t.ink, fontSize: 15, fontWeight: "500" },
      min: -0.35,
      max: 1.05,
      interval: 0.25,
      axisLabel: { color: t.inkSoft, fontSize: 13, formatter: v => v.toFixed(2) },
      axisLine:  { show: true, lineStyle: { color: t.inkSoft } },
      splitLine: { lineStyle: { color: t.grid } }
    },
    {
      gridIndex: 1,
      type: "value",
      name: "PACF",
      nameLocation: "middle",
      nameGap: 52,
      nameTextStyle: { color: t.ink, fontSize: 15, fontWeight: "500" },
      min: -0.40,
      max: 0.85,
      interval: 0.25,
      axisLabel: { color: t.inkSoft, fontSize: 13, formatter: v => v.toFixed(2) },
      axisLine:  { show: true, lineStyle: { color: t.inkSoft } },
      splitLine: { lineStyle: { color: t.grid } }
    }
  ],

  series: [
    {
      type: "bar",
      xAxisIndex: 0,
      yAxisIndex: 0,
      data: acfBarData,
      barWidth: 3,
      markLine: {
        silent: true,
        symbol: "none",
        label: { show: false },
        data: [
          { yAxis: 0,   lineStyle: { color: t.inkSoft, type: "solid",  width: 1.5 } },
          { yAxis: ci,  lineStyle: { color: t.amber,   type: "dashed", width: 2   } },
          { yAxis: -ci, lineStyle: { color: t.amber,   type: "dashed", width: 2   } }
        ]
      }
    },
    {
      type: "bar",
      xAxisIndex: 1,
      yAxisIndex: 1,
      data: pacfBarData,
      barWidth: 3,
      markLine: {
        silent: true,
        symbol: "none",
        label: { show: false },
        data: [
          { yAxis: 0,   lineStyle: { color: t.inkSoft, type: "solid",  width: 1.5 } },
          { yAxis: ci,  lineStyle: { color: t.amber,   type: "dashed", width: 2   } },
          { yAxis: -ci, lineStyle: { color: t.amber,   type: "dashed", width: 2   } }
        ]
      }
    }
  ]
});
