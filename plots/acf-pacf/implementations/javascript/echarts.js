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

// Compute sample ACF at lags 0..maxLag
function sampleACF(data, maxLag) {
  const n = data.length;
  const mean = data.reduce((s, v) => s + v, 0) / n;
  const denom = data.reduce((s, v) => s + (v - mean) ** 2, 0);
  const acf = [];
  for (let k = 0; k <= maxLag; k++) {
    let num = 0;
    for (let i = k; i < n; i++) num += (data[i] - mean) * (data[i - k] - mean);
    acf.push(num / denom);
  }
  return acf;
}

// Compute sample PACF at lags 1..maxLag via Durbin-Levinson recursion
function samplePACF(acf, maxLag) {
  const pacf = [null]; // pacf[0] unused; pacf[k] = PACF at lag k
  let phi = [acf[1]];
  pacf.push(acf[1]);
  for (let k = 2; k <= maxLag; k++) {
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
  return pacf.slice(1); // [PACF(1), PACF(2), ..., PACF(maxLag)]
}

const MAX_LAG = 35;
const acf = sampleACF(series, MAX_LAG);
const pacf = samplePACF(acf, MAX_LAG);
const ci = 1.96 / Math.sqrt(N); // 95% confidence bound ≈ ±0.113

// Color code bars: significant vs insignificant
const SIG_ACF   = t.palette[0];               // #009E73
const INSIG_ACF  = "rgba(0,158,115,0.28)";
const SIG_PACF  = t.palette[2];               // #4467A3
const INSIG_PACF = "rgba(68,103,163,0.28)";

const acfLags  = Array.from({ length: MAX_LAG + 1 }, (_, i) => i);
const pacfLags = Array.from({ length: MAX_LAG }, (_, i) => i + 1);

const acfBarData = acf.map((v, i) => ({
  value: +v.toFixed(4),
  itemStyle: { color: (i === 0 || Math.abs(v) > ci) ? SIG_ACF : INSIG_ACF }
}));
const pacfBarData = pacf.map((v, i) => ({
  value: +v.toFixed(4),
  itemStyle: { color: Math.abs(v) > ci ? SIG_PACF : INSIG_PACF }
}));

// Shared confidence interval markLine (amber dashed) + zero baseline
function ciMarkLine() {
  return {
    silent: true,
    symbol: "none",
    label: { show: false },
    data: [
      { yAxis: 0,   lineStyle: { color: t.inkSoft, type: "solid",  width: 1.5 } },
      { yAxis: ci,  lineStyle: { color: t.amber,   type: "dashed", width: 2   } },
      { yAxis: -ci, lineStyle: { color: t.amber,   type: "dashed", width: 2   } }
    ]
  };
}

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
      data: acfLags.map(String),
      axisLabel: { show: false },
      axisLine:  { lineStyle: { color: t.inkSoft } },
      axisTick:  { show: false },
      splitLine: { show: false }
    },
    {
      gridIndex: 1,
      type: "category",
      data: pacfLags.map(String),
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
      markLine: ciMarkLine()
    },
    {
      type: "bar",
      xAxisIndex: 1,
      yAxisIndex: 1,
      data: pacfBarData,
      barWidth: 3,
      markLine: ciMarkLine()
    }
  ]
});
