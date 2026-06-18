// anyplot.ai
// eye-diagram-basic: Signal Integrity Eye Diagram
// Library: chartjs 4.4.7 | JavaScript 22.22.3
// Quality: 85/100 | Created: 2026-06-18

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// Deterministic LCG — no seeded Math.random in the browser
let _s = 42;
function rand() {
  _s = (_s * 1664525 + 1013904223) >>> 0;
  return _s / 4294967296;
}

// Box-Muller transform for Gaussian samples
function randn() {
  const u = Math.max(rand(), 1e-12);
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rand());
}

// Bandwidth-limited sigmoid transition (models realistic rise/fall)
function sigmoid(x) {
  return 1 / (1 + Math.exp(-x));
}

// Eye diagram simulation parameters
const NUM_TRACES = 300;         // overlaid 2-UI segments
const SAMPLES_PER_UI = 100;     // sample density per unit interval
const NOISE_SIGMA = 0.05;       // additive Gaussian noise (5 % of amplitude)
const JITTER_SIGMA = 0.03;      // timing jitter std-dev (3 % of UI)
const BW = 15;                  // sigmoid bandwidth (controls rise/fall steepness)

// Dashed reference lines at nominal NRZ bit levels (0 V and 1 V)
const refLine = (yVal) => ({
  data: [{ x: 0, y: yVal }, { x: 2, y: yVal }],
  borderColor: t.inkSoft,
  borderWidth: 1.5,
  borderDash: [8, 5],
  pointRadius: 0,
  fill: false,
  tension: 0,
});

// Generate 300 NRZ traces, each covering 2 UI.
// 4 consecutive bits produce 3 transitions at t = 0, 1, 2 UI;
// eyes open at t ≈ 0.5 UI and t ≈ 1.5 UI (sampling points).
const traceDatasets = [];
for (let tr = 0; tr < NUM_TRACES; tr++) {
  const b = [rand(), rand(), rand(), rand()].map(v => (v > 0.5 ? 1 : 0));
  const j = [
    randn() * JITTER_SIGMA,
    randn() * JITTER_SIGMA,
    randn() * JITTER_SIGMA,
  ];

  const pts = [];
  for (let i = 0; i <= SAMPLES_PER_UI * 2; i++) {
    const time = i / SAMPLES_PER_UI;
    // Accumulate sigmoid transitions at each bit boundary
    let v = b[0];
    v += (b[1] - b[0]) * sigmoid(BW * (time - j[0]));
    v += (b[2] - b[1]) * sigmoid(BW * (time - 1 - j[1]));
    v += (b[3] - b[2]) * sigmoid(BW * (time - 2 - j[2]));
    v += randn() * NOISE_SIGMA;
    pts.push({ x: time, y: v });
  }

  traceDatasets.push({
    data: pts,
    // Imprint palette position 1 (#009E73) at ~6 % alpha — density stacks to show hot regions
    borderColor: t.palette[0] + "0f",
    borderWidth: 1.5,
    pointRadius: 0,
    fill: false,
    tension: 0,
  });
}

// Mount
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// Chart
new Chart(canvas, {
  type: "line",
  data: {
    datasets: [refLine(0), refLine(1), ...traceDatasets],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    parsing: false,
    layout: { padding: { top: 4, right: 24, bottom: 10, left: 8 } },
    plugins: {
      title: {
        display: true,
        text: "eye-diagram-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { top: 8, bottom: 16 },
      },
      legend: { display: false },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        type: "linear",
        min: 0,
        max: 2,
        title: {
          display: true,
          text: "Time (UI)",
          color: t.ink,
          font: { size: 16, weight: "500" },
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          stepSize: 0.5,
        },
        grid: { color: t.grid },
        border: { display: false },
      },
      y: {
        min: -0.3,
        max: 1.3,
        title: {
          display: true,
          text: "Voltage (V)",
          color: t.ink,
          font: { size: 16, weight: "500" },
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          stepSize: 0.5,
        },
        grid: { color: t.grid },
        border: { display: false },
      },
    },
  },
});
