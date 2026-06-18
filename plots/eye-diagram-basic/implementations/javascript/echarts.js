// anyplot.ai
// eye-diagram-basic: Signal Integrity Eye Diagram
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-06-18

const t = window.ANYPLOT_TOKENS;

// Seeded LCG for deterministic data generation (no Date.now / Math.random)
let _s = 42;
function lcg() {
  _s = (_s * 1664525 + 1013904223) >>> 0;
  return _s / 4294967296;
}
function gauss() {
  const u = Math.max(lcg(), 1e-10);
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * lcg());
}

// NRZ signal parameters
const NUM_TRACES  = 400;   // overlaid signal periods
const SAMPLES     = 200;   // time-samples per trace across 2 UI
const NOISE_SIGMA = 0.05;  // additive Gaussian noise (5% of amplitude)
const JITTER_SIGMA = 0.03; // timing jitter per transition (3% of UI)

// 2-D density grid
const T_BINS = 200;
const V_BINS = 100;
const T_MIN = 0,   T_MAX = 2;   // 0–2 unit intervals
const V_MIN = -0.5, V_MAX = 1.5; // -0.5 V to 1.5 V (NRZ logic levels 0 V / 1 V)

const grid = new Uint32Array(T_BINS * V_BINS);

// Sigmoid for bandwidth-limited bit transitions
function sig(x, center) {
  return 1 / (1 + Math.exp(-30 * (x - center)));
}

// Generate traces: each trace uses three random bits [b0, b1, b2] across 2 UI
for (let tr = 0; tr < NUM_TRACES; tr++) {
  const b0 = lcg() < 0.5 ? 0 : 1; // bit before the window
  const b1 = lcg() < 0.5 ? 0 : 1; // bit in first UI
  const b2 = lcg() < 0.5 ? 0 : 1; // bit in second UI
  const j0 = gauss() * JITTER_SIGMA; // timing jitter at t = 0 transition
  const j1 = gauss() * JITTER_SIGMA; // timing jitter at t = 1 transition

  for (let s = 0; s < SAMPLES; s++) {
    const tVal = T_MIN + (s / (SAMPLES - 1)) * (T_MAX - T_MIN);
    const vVal =
      b0 + (b1 - b0) * sig(tVal, 0 + j0)
         + (b2 - b1) * sig(tVal, 1 + j1)
         + gauss() * NOISE_SIGMA;

    const ti = Math.min(T_BINS - 1, Math.max(0,
      Math.floor(((tVal - T_MIN) / (T_MAX - T_MIN)) * T_BINS)));
    const vi = Math.min(V_BINS - 1, Math.max(0,
      Math.floor(((vVal - V_MIN) / (V_MAX - V_MIN)) * V_BINS)));
    grid[ti * V_BINS + vi]++;
  }
}

// Sqrt-normalize density for better perceptual dynamic range
let maxCount = 0;
for (let i = 0; i < grid.length; i++) if (grid[i] > maxCount) maxCount = grid[i];
const sqrtMax = Math.sqrt(maxCount);

const heatData = [];
for (let ti = 0; ti < T_BINS; ti++) {
  for (let vi = 0; vi < V_BINS; vi++) {
    const c = grid[ti * V_BINS + vi];
    if (c > 0) heatData.push([ti, vi, Math.sqrt(c) / sqrtMax]);
  }
}

// Bin-center label arrays for category axes
const timeLabels = Array.from({ length: T_BINS }, (_, i) =>
  (T_MIN + (i + 0.5) / T_BINS * (T_MAX - T_MIN)).toFixed(3)
);
const voltLabels = Array.from({ length: V_BINS }, (_, i) =>
  (V_MIN + (i + 0.5) / V_BINS * (V_MAX - V_MIN)).toFixed(3)
);

const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  backgroundColor: "transparent",

  title: {
    text: "eye-diagram-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 18,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "bold" }
  },

  grid: { left: 100, right: 140, top: 80, bottom: 78 },

  xAxis: {
    type: "category",
    data: timeLabels,
    name: "Time (UI)",
    nameLocation: "middle",
    nameGap: 44,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: {
      interval: (idx) => idx % 50 === 0 || idx === T_BINS - 1,
      formatter: (val) => parseFloat(val).toFixed(1),
      color: t.inkSoft,
      fontSize: 14
    },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false }
  },

  yAxis: {
    type: "category",
    data: voltLabels,
    name: "Voltage (V)",
    nameLocation: "middle",
    nameGap: 58,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: {
      interval: (idx) => idx % 25 === 0 || idx === V_BINS - 1,
      formatter: (val) => parseFloat(val).toFixed(1),
      color: t.inkSoft,
      fontSize: 14
    },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false }
  },

  visualMap: {
    type: "continuous",
    min: 0,
    max: 1,
    calculable: false,
    orient: "vertical",
    right: 18,
    top: "center",
    itemHeight: 220,
    text: ["Dense", "Sparse"],
    textStyle: { color: t.inkSoft, fontSize: 13 },
    inRange: { color: [t.pageBg, t.seq[0], t.seq[1]] }
  },

  series: [{
    type: "heatmap",
    data: heatData,
    emphasis: { disabled: true }
  }]
});
