// anyplot.ai
// histogram-capability: Process Capability Plot with Specification Limits
// Library: echarts 5.5.1 | JavaScript 22.22.3
// Quality: 88/100 | Created: 2026-06-20

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// Deterministic LCG (seed 42) — no seeded RNG in browser
let _seed = 42;
function rand() {
  _seed = (_seed * 1664525 + 1013904223) & 0xffffffff;
  return (_seed >>> 0) / 0x100000000;
}
function randNorm(mu, s) {
  const u1 = Math.max(rand(), 1e-12);
  return mu + s * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * rand());
}

// Process specification (shaft diameter, mm)
const LSL = 9.95;
const USL = 10.05;
const TARGET = 10.00;
const N = 200;

// Generate synthetic measurements: slightly off-center, capable process
const meas = Array.from({ length: N }, () => randNorm(10.002, 0.0085));

// Sample statistics
const mu = meas.reduce((a, b) => a + b, 0) / N;
const sigma = Math.sqrt(meas.reduce((a, v) => a + (v - mu) ** 2, 0) / (N - 1));
const cp  = (USL - LSL) / (6 * sigma);
const cpk = Math.min((USL - mu) / (3 * sigma), (mu - LSL) / (3 * sigma));

// Histogram: 20 bins over [9.91, 10.09]
const X_LO = 9.91, X_HI = 10.09, N_BINS = 20;
const BW = (X_HI - X_LO) / N_BINS;
const counts = new Array(N_BINS).fill(0);
meas.forEach(v => {
  const i = Math.floor((v - X_LO) / BW);
  if (i >= 0 && i < N_BINS) counts[i]++;
});
const barData = counts.map((c, i) => [X_LO + (i + 0.5) * BW, c]);

// Fitted normal PDF curve, scaled to match count axis
const curve = [];
for (let i = 0; i <= 400; i++) {
  const x = X_LO + (i / 400) * (X_HI - X_LO);
  const pdf = Math.exp(-0.5 * ((x - mu) / sigma) ** 2) / (sigma * Math.sqrt(2 * Math.PI));
  curve.push([x, pdf * N * BW]);
}

const yMax = Math.ceil(Math.max(...counts, ...curve.map(d => d[1])) * 1.25);

// Bar width: grid_px / N_BINS  (grid: left=90, right=80, mount=1600 → 1430px / 20 bins ≈ 71px)
const BAR_WIDTH = 71;

const chart = echarts.init(document.getElementById("container"));

const TITLE = "histogram-capability · javascript · echarts · anyplot.ai";
const titleSize = Math.max(11, Math.round(22 * Math.min(1, 67 / TITLE.length)));

chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",

  title: {
    text: TITLE,
    left: "center",
    top: 18,
    textStyle: { color: t.ink, fontSize: titleSize, fontWeight: "normal" }
  },

  grid: { left: 90, right: 80, top: 100, bottom: 110 },

  xAxis: {
    type: "value",
    min: X_LO,
    max: X_HI,
    interval: 0.02,
    name: "Shaft Diameter (mm)",
    nameLocation: "middle",
    nameGap: 50,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    axisLabel: {
      color: t.inkSoft,
      fontSize: 12,
      formatter: v => v.toFixed(2)
    },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
    axisTick: { lineStyle: { color: t.inkSoft } }
  },

  yAxis: {
    type: "value",
    name: "Count",
    nameLocation: "middle",
    nameGap: 42,
    nameTextStyle: { color: t.inkSoft, fontSize: 14 },
    max: yMax,
    axisLabel: { color: t.inkSoft, fontSize: 12 },
    axisLine: { show: true, lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
    axisTick: { show: false }
  },

  legend: {
    data: [
      { name: "Measurements", icon: "roundRect" },
      { name: "Normal Fit" }
    ],
    bottom: 14,
    left: "center",
    orient: "horizontal",
    itemGap: 30,
    textStyle: { color: t.inkSoft, fontSize: 13 }
  },

  // Cp / Cpk annotation box (upper-right — data sparse beyond USL)
  graphic: [{
    type: "group",
    right: 84,
    top: 108,
    children: [
      {
        type: "rect",
        shape: { width: 158, height: 78, r: 4 },
        style: { fill: t.elevatedBg, stroke: t.grid, lineWidth: 1 }
      },
      // Brand green left-border accent
      {
        type: "rect",
        shape: { x: 0, y: 0, width: 4, height: 78, r: [4, 0, 0, 4] },
        style: { fill: t.palette[0], lineWidth: 0 }
      },
      // "Cp" label in brand green
      {
        type: "text",
        top: 14,
        left: 18,
        style: {
          text: "Cp",
          font: "bold 16px 'Helvetica Neue', Arial, sans-serif",
          fill: t.palette[0]
        }
      },
      // Cp numeric value in ink
      {
        type: "text",
        top: 14,
        left: 62,
        style: {
          text: "= " + cp.toFixed(2),
          font: "bold 16px 'Helvetica Neue', Arial, sans-serif",
          fill: t.ink
        }
      },
      // "Cpk" label in brand green
      {
        type: "text",
        top: 44,
        left: 18,
        style: {
          text: "Cpk",
          font: "bold 16px 'Helvetica Neue', Arial, sans-serif",
          fill: t.palette[0]
        }
      },
      // Cpk numeric value in ink
      {
        type: "text",
        top: 44,
        left: 62,
        style: {
          text: "= " + cpk.toFixed(2),
          font: "bold 16px 'Helvetica Neue', Arial, sans-serif",
          fill: t.ink
        }
      }
    ]
  }],

  series: [
    {
      name: "Measurements",
      type: "bar",
      data: barData,
      barWidth: BAR_WIDTH,
      itemStyle: { color: t.palette[0], opacity: 0.72 },
      markLine: {
        symbol: ["none", "none"],
        silent: true,
        label: {
          show: true,
          fontSize: 15,
          fontWeight: "bold",
          formatter: params => params.name
        },
        data: [
          {
            name: "LSL",
            xAxis: LSL,
            lineStyle: { color: t.palette[4], type: "dashed", width: 2.5 },
            label: { color: t.palette[4], position: "insideEndTop" }
          },
          {
            name: "USL",
            xAxis: USL,
            lineStyle: { color: t.palette[4], type: "dashed", width: 2.5 },
            label: { color: t.palette[4], position: "insideEndTop" }
          },
          {
            name: "Target",
            xAxis: TARGET,
            lineStyle: { color: t.inkSoft, type: "dashed", width: 2 },
            label: { color: t.inkSoft, position: "insideEndTop" }
          }
        ]
      }
    },
    {
      name: "Normal Fit",
      type: "line",
      data: curve,
      symbol: "none",
      lineStyle: { color: t.palette[2], width: 2.5 },
      z: 10
    }
  ]
});
