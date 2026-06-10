// anyplot.ai
// recurrence-basic: Recurrence Plot for Nonlinear Time Series
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 85/100 | Created: 2026-06-10
//# anyplot-orientation: square
// anyplot.ai
// recurrence-basic: Recurrence Plot for Nonlinear Time Series
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-06-10

const t = window.ANYPLOT_TOKENS;

// Lorenz attractor (σ=10, ρ=28, β=8/3): deterministic chaotic time series
const dt = 0.02;
let lx = 1.0, ly = 0.0, lz = 0.0;

// Burn-in: drive initial conditions onto the strange attractor
for (let k = 0; k < 300; k++) {
  const dxk = 10 * (ly - lx);
  const dyk = lx * (28 - lz) - ly;
  const dzk = lx * ly - (8 / 3) * lz;
  lx += dxk * dt;
  ly += dyk * dt;
  lz += dzk * dt;
}

// Time-delay embedding of the x-component: state(i) = (x[i], x[i + DELAY])
// Implements Takens' theorem reconstruction from a scalar observable
const DELAY = 8;
const NPTS = 300;
const N_TOTAL = NPTS + DELAY;

const lorenzX = [];
for (let k = 0; k < N_TOTAL; k++) {
  const dxk = 10 * (ly - lx);
  const dyk = lx * (28 - lz) - ly;
  const dzk = lx * ly - (8 / 3) * lz;
  lx += dxk * dt;
  ly += dyk * dt;
  lz += dzk * dt;
  lorenzX.push(lx);
}

const emX = lorenzX.slice(0, NPTS);
const emY = lorenzX.slice(DELAY, NPTS + DELAY);

// Pairwise Euclidean distances in the 2D embedded state space
let maxDist = 0;
const dist = new Float32Array(NPTS * NPTS);
for (let i = 0; i < NPTS; i++) {
  for (let j = i + 1; j < NPTS; j++) {
    const dx = emX[i] - emX[j];
    const dy = emY[i] - emY[j];
    const val = Math.sqrt(dx * dx + dy * dy);
    dist[i * NPTS + j] = val;
    dist[j * NPTS + i] = val;
    if (val > maxDist) maxDist = val;
  }
  // diagonal stays 0: every state recurs with itself
}

// Binary threshold ε = 12% of maximum observed distance
const epsilon = maxDist * 0.12;

// Collect [xIndex, yIndex, 1] for every recurrent pair (distance < ε)
const data = [];
for (let i = 0; i < NPTS; i++) {
  for (let j = 0; j < NPTS; j++) {
    if (dist[i * NPTS + j] < epsilon) {
      data.push([j, i, 1]);
    }
  }
}

const timeLabels = Array.from({ length: NPTS }, (_, k) => k);

const chart = echarts.init(document.getElementById("container"));
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "recurrence-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 18,
    textStyle: { color: t.ink, fontSize: 22 },
  },
  grid: { left: 90, right: 18, top: 76, bottom: 82 },
  xAxis: {
    type: "category",
    data: timeLabels,
    name: "Time Index",
    nameLocation: "center",
    nameGap: 38,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 13, interval: 49 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "category",
    data: timeLabels,
    name: "Time Index",
    nameLocation: "center",
    nameGap: 50,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 13, interval: 49 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  series: [
    {
      type: "heatmap",
      data: data,
      progressive: 0,
      itemStyle: { color: t.palette[0] },
      emphasis: { disabled: true },
    },
  ],
});
