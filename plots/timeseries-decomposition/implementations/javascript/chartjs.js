// anyplot.ai
// timeseries-decomposition: Time Series Decomposition Plot
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-09

const t = window.ANYPLOT_TOKENS;

// --- Data: monthly retail sales, 2018-2025 (in-memory, deterministic) ------
const N_MONTHS = 96;
const START_YEAR = 2018;
const labels = Array.from({ length: N_MONTHS }, (_, i) => {
  const year = START_YEAR + Math.floor(i / 12);
  const month = (i % 12) + 1;
  return `${year}-${String(month).padStart(2, "0")}`;
});

// Fixed-seed LCG -> Box-Muller gaussian (browser has no seeded RNG)
let lcgSeed = 42;
function uniformRandom() {
  lcgSeed = (lcgSeed * 1103515245 + 12345) % 2147483648;
  return lcgSeed / 2147483648;
}
function gaussianNoise(std) {
  const u1 = Math.max(uniformRandom(), 1e-9);
  const u2 = uniformRandom();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2) * std;
}

// Underlying growth (steady) + holiday-season seasonality (Jan=0 .. Dec=11)
const GROWTH_BASE = 120;
const GROWTH_SLOPE = 1.15;
const SEASONAL_PATTERN = [-9, -6, -2, 1, 3, 5, 6, 4, 2, 4, 11, 18];
const NOISE_STD = 3.5;

const salesKUsd = Array.from({ length: N_MONTHS }, (_, i) => {
  const growth = GROWTH_BASE + GROWTH_SLOPE * i;
  const seasonal = SEASONAL_PATTERN[i % 12];
  return growth + seasonal + gaussianNoise(NOISE_STD);
});

// --- Classical additive decomposition (centered 2x12 moving average) -------
const HALF_PERIOD = 6;
const trend = new Array(N_MONTHS).fill(null);
for (let i = HALF_PERIOD; i < N_MONTHS - HALF_PERIOD; i++) {
  let sum = 0.5 * salesKUsd[i - HALF_PERIOD] + 0.5 * salesKUsd[i + HALF_PERIOD];
  for (let k = -(HALF_PERIOD - 1); k <= HALF_PERIOD - 1; k++) sum += salesKUsd[i + k];
  trend[i] = sum / 12;
}

const detrended = salesKUsd.map((v, i) => (trend[i] === null ? null : v - trend[i]));
const seasonalIndex = Array.from({ length: 12 }, (_, m) => {
  const vals = detrended.filter((v, i) => i % 12 === m && v !== null);
  return vals.reduce((a, b) => a + b, 0) / vals.length;
});
const seasonalMean = seasonalIndex.reduce((a, b) => a + b, 0) / 12;
const centeredSeasonalIndex = seasonalIndex.map((v) => v - seasonalMean);
const seasonal = Array.from({ length: N_MONTHS }, (_, i) => centeredSeasonalIndex[i % 12]);

const residual = salesKUsd.map((v, i) => (trend[i] === null ? null : v - trend[i] - seasonal[i]));
const zeroLine = new Array(N_MONTHS).fill(0);

// --- Layout: four stacked panels sharing one time axis ----------------------
const container = document.getElementById("container");
container.style.display = "flex";
container.style.flexDirection = "column";
container.style.boxSizing = "border-box";
container.style.padding = "10px 22px 4px";
container.style.backgroundColor = t.pageBg;

const PANELS = [
  { key: "original", title: "Original", axisLabel: "Sales ($k)", data: salesKUsd, kind: "line", showMainTitle: true },
  { key: "trend", title: "Trend", axisLabel: "Sales ($k)", data: trend, kind: "line", showMainTitle: false },
  { key: "seasonal", title: "Seasonal", axisLabel: "Effect ($k)", data: seasonal, kind: "line", showMainTitle: false },
  { key: "residual", title: "Residual", axisLabel: "Sales ($k)", data: residual, kind: "points", showMainTitle: false },
];

PANELS.forEach((panel, idx) => {
  const row = document.createElement("div");
  row.style.flex = "1 1 0";
  row.style.minHeight = "0";
  row.style.position = "relative";
  row.style.borderBottom = idx < PANELS.length - 1 ? `1px solid ${t.grid}` : "none";
  row.style.paddingBottom = idx < PANELS.length - 1 ? "4px" : "0";
  container.appendChild(row);

  const canvas = document.createElement("canvas");
  row.appendChild(canvas);

  const isBottom = idx === PANELS.length - 1;
  const datasets = [
    {
      label: panel.title,
      data: panel.data,
      borderColor: t.palette[0],
      backgroundColor: t.palette[0],
      borderWidth: panel.kind === "line" ? 3 : 0,
      showLine: panel.kind === "line",
      pointRadius: panel.kind === "line" ? 0 : 4,
      pointHoverRadius: 0,
      spanGaps: false,
      tension: 0.15,
    },
  ];
  if (panel.key === "residual") {
    datasets.push({
      label: "Zero reference",
      data: zeroLine,
      borderColor: t.ink,
      borderWidth: 1.5,
      borderDash: [6, 5],
      pointRadius: 0,
      showLine: true,
    });
  }

  new Chart(canvas, {
    type: "line",
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {
        title: {
          display: panel.showMainTitle,
          text: "timeseries-decomposition · javascript · chartjs · anyplot.ai",
          color: t.ink,
          font: { size: 22, weight: "500" },
          padding: { bottom: 8 },
        },
        subtitle: {
          display: true,
          text: panel.title,
          color: t.ink,
          align: "start",
          font: { size: 17, weight: "600" },
          padding: { bottom: 6 },
        },
        legend: { display: false },
      },
      scales: {
        x: {
          ticks: {
            display: isBottom,
            color: t.inkSoft,
            font: { size: 14 },
            maxRotation: 0,
            autoSkip: true,
            maxTicksLimit: 12,
          },
          grid: { color: t.grid, drawTicks: false },
          title: { display: isBottom, text: "Month", color: t.ink, font: { size: 16 } },
        },
        y: {
          ticks: { color: t.inkSoft, font: { size: 14 } },
          grid: { display: false },
          title: { display: true, text: panel.axisLabel, color: t.ink, font: { size: 16 } },
        },
      },
    },
  });
});
