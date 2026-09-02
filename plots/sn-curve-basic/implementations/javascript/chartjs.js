// anyplot.ai
// sn-curve-basic: S-N Curve (Wöhler Curve)
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 81/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Fatigue test results for a steel alloy: stress amplitude (MPa) vs. cycles to
// failure (N). Basquin's equation: sigma_a = A * N^b, plus scatter typical of
// multiple coupon specimens tested at the same stress level.
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(42);

const basquinA = 950; // MPa, fatigue strength coefficient
const basquinB = -0.11; // fatigue strength exponent

const stressLevels = [520, 480, 440, 400, 360, 320, 290, 260, 240, 220];
const specimensPerLevel = 4;
const testPoints = [];
stressLevels.forEach((stress) => {
  const meanLogN = Math.log10(stress / basquinA) / basquinB;
  for (let i = 0; i < specimensPerLevel; i++) {
    const scatter = (rand() - 0.5) * 0.42; // log10(N) scatter band
    const logN = meanLogN + scatter;
    testPoints.push({ x: Math.pow(10, logN), y: stress });
  }
});

const fitCycles = [1e3, 1e7];
const fitLine = fitCycles.map((n) => ({ x: n, y: basquinA * Math.pow(n, basquinB) }));

const ultimateStrength = 780; // MPa
const yieldStrength = 620; // MPa
const enduranceLimit = 230; // MPa
const enduranceStart = 1e6; // cycles beyond which the endurance limit applies

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------------
new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      {
        label: "Test specimens",
        data: testPoints,
        backgroundColor: t.palette[0],
        borderColor: t.pageBg,
        borderWidth: 1,
        pointRadius: 6,
        pointHoverRadius: 6,
        showLine: false,
        order: 1,
      },
      {
        label: "Basquin fit",
        data: fitLine,
        type: "line",
        borderColor: t.palette[1],
        backgroundColor: t.palette[1],
        borderWidth: 3,
        pointRadius: 0,
        tension: 0,
        order: 2,
      },
      {
        label: "Ultimate strength (780 MPa)",
        data: [
          { x: 1e3, y: ultimateStrength },
          { x: 1e7, y: ultimateStrength },
        ],
        type: "line",
        borderColor: t.palette[2],
        backgroundColor: t.palette[2],
        borderWidth: 2,
        borderDash: [12, 4, 2, 4],
        pointRadius: 0,
        tension: 0,
        order: 3,
      },
      {
        label: "Yield strength (620 MPa)",
        data: [
          { x: 1e3, y: yieldStrength },
          { x: 1e7, y: yieldStrength },
        ],
        type: "line",
        borderColor: t.palette[3],
        backgroundColor: t.palette[3],
        borderWidth: 2,
        borderDash: [10, 6],
        pointRadius: 0,
        tension: 0,
        order: 4,
      },
      {
        label: "Endurance limit (230 MPa)",
        data: [
          { x: enduranceStart, y: enduranceLimit },
          { x: 1e7, y: enduranceLimit },
        ],
        type: "line",
        borderColor: t.palette[5],
        backgroundColor: t.palette[5],
        borderWidth: 2,
        borderDash: [3, 5],
        pointRadius: 0,
        tension: 0,
        order: 5,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "sn-curve-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 20 },
      },
      legend: {
        position: "top",
        align: "end",
        labels: { color: t.inkSoft, font: { size: 14 }, boxWidth: 24, usePointStyle: true },
      },
    },
    scales: {
      x: {
        type: "logarithmic",
        min: 1e3,
        max: 1e7,
        title: { display: true, text: "Cycles to Failure (N)", color: t.ink, font: { size: 16 } },
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: (value) => {
            const log10 = Math.log10(value);
            return Number.isInteger(log10) ? `10^${log10}` : null;
          },
        },
        grid: { color: t.grid },
      },
      y: {
        type: "logarithmic",
        min: 150,
        max: 850,
        title: { display: true, text: "Stress Amplitude (MPa)", color: t.ink, font: { size: 16 } },
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: (value) => {
            if ([150, 200, 300, 400, 500, 600, 700, 800].includes(value)) return value;
            return null;
          },
        },
        grid: { color: t.grid },
      },
    },
  },
});
