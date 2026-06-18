// anyplot.ai
// scatter-constellation-diagram: Digital Modulation Constellation Diagram
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 90/100 | Created: 2026-06-18
//# anyplot-orientation: square
// anyplot.ai
// scatter-constellation-diagram: Digital Modulation Constellation Diagram
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-06-18

const t = window.ANYPLOT_TOKENS;

// Seeded LCG PRNG — reproducible data without Math.random()
function mkRng(seed) {
  let s = seed >>> 0;
  return function () {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

// Box-Muller: uniform → Gaussian
function gaussian(rng, sigma) {
  const u1 = rng() + 1e-10;
  const u2 = rng();
  return sigma * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// 16-QAM ideal constellation: 16 points on {-3, -1, +1, +3}² grid
const ampLevels = [-3, -1, 1, 3];
const idealPoints = [];
for (const q of ampLevels) {
  for (const i of ampLevels) {
    idealPoints.push([i, q]);
  }
}

// Received symbols: 32 per ideal point (512 total) with AWGN noise (noiseStd = 0.12)
const rng = mkRng(42);
const noiseStd = 0.12;
const symbolsPerPoint = 32;
const received = [];
let totalErrorPower = 0;

for (const [i0, q0] of idealPoints) {
  for (let k = 0; k < symbolsPerPoint; k++) {
    const ni = gaussian(rng, noiseStd);
    const nq = gaussian(rng, noiseStd);
    received.push([i0 + ni, q0 + nq]);
    totalErrorPower += ni * ni + nq * nq;
  }
}

// EVM = sqrt(mean error power / mean symbol power) × 100%
// 16-QAM mean symbol power: mean(I²+Q²) for I,Q ∈ {±1,±3} = 2×(1+9)/2 = 10
const evm = (Math.sqrt(totalErrorPower / received.length / 10) * 100).toFixed(1);

// Decision boundary lines at ±2 and 0 (midpoints between adjacent symbol levels)
const boundaryLines = [
  { xAxis: -2 }, { xAxis: 0 }, { xAxis: 2 },
  { yAxis: -2 }, { yAxis: 0 }, { yAxis: 2 },
];

const chart = echarts.init(document.getElementById("container"));

chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",

  title: {
    text: "scatter-constellation-diagram · javascript · echarts · anyplot.ai",
    left: "center",
    top: 22,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "bold" },
  },

  legend: {
    data: ["Received Symbols", "Ideal Points"],
    top: 58,
    left: "center",
    orient: "horizontal",
    textStyle: { color: t.inkSoft, fontSize: 14 },
    itemGap: 32,
  },

  // Square grid: left+right = top+bottom = 200 → 1000×1000 CSS plot area
  // Equal I/Q range [-4.5, 4.5] on a 1000×1000 area ensures equal aspect ratio
  grid: { left: 120, right: 80, top: 100, bottom: 100 },

  xAxis: {
    type: "value",
    name: "In-Phase (I)",
    nameLocation: "middle",
    nameGap: 50,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    min: -4.5,
    max: 4.5,
    interval: 1,
    axisLabel: { color: t.inkSoft, fontSize: 13 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
  },

  yAxis: {
    type: "value",
    name: "Quadrature (Q)",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    min: -4.5,
    max: 4.5,
    interval: 1,
    axisLabel: { color: t.inkSoft, fontSize: 13 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
  },

  series: [
    {
      name: "Received Symbols",
      type: "scatter",
      data: received,
      symbolSize: 7,
      itemStyle: {
        color: t.palette[0],  // #009E73 brand green — always first series (Imprint palette)
        opacity: 0.55,
      },
      // Decision boundary grid overlaid on the received-symbols series
      markLine: {
        silent: true,
        symbol: "none",
        label: { show: false },
        lineStyle: { type: "dashed", color: t.grid, width: 1.5 },
        data: boundaryLines,
      },
    },
    {
      name: "Ideal Points",
      type: "scatter",
      data: idealPoints,
      symbol: "rect",
      symbolSize: [18, 18],
      itemStyle: {
        color: t.palette[4],  // #AE3030 matte red — engineering convention for ideal I/Q reference points
        opacity: 1,
      },
    },
  ],

  // EVM annotation placed in the upper-right quadrant of the constellation
  graphic: [
    {
      type: "text",
      left: "72%",
      top: "11%",
      style: {
        text: `EVM = ${evm}%`,
        fill: t.ink,
        font: "bold 16px sans-serif",
      },
    },
  ],
});
