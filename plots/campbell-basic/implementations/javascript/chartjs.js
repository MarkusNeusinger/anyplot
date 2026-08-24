// anyplot.ai
// campbell-basic: Campbell Diagram
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 82/100 | Created: 2026-08-24

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Natural frequency curves are modeled as linear functions of speed, matching
// the mild stiffening/softening gyroscopic behavior the spec calls for.
const SPEED_MAX = 6000;
const SPEED_STEP = 100;
const FREQ_MAX = 150;

const speeds = [];
for (let speed = 0; speed <= SPEED_MAX; speed += SPEED_STEP) speeds.push(speed);

const modes = [
  { name: "1st Bending", a: 25, b: 0.0012, color: t.palette[0] },
  { name: "2nd Bending", a: 62, b: -0.0015, color: t.palette[1] },
  { name: "1st Torsional", a: 85, b: 0.0002, color: t.palette[2] },
  { name: "Axial", a: 112, b: 0.0008, color: t.palette[3] },
];

const engineOrders = [
  { order: 1, dash: [3, 3] },
  { order: 2, dash: [10, 4] },
  { order: 3, dash: [14, 4, 2, 4] },
];

// Critical speeds: exact intersection of an engine-order line
// (freq = order/60 * speed) with a mode's linear frequency curve
// (freq = a + b * speed), solved algebraically.
const criticalSpeeds = [];
engineOrders.forEach(({ order }) => {
  modes.forEach((mode) => {
    const slope = order / 60;
    if (slope === mode.b) return;
    const speed = mode.a / (slope - mode.b);
    if (speed > 0 && speed <= SPEED_MAX) {
      criticalSpeeds.push({ x: speed, y: slope * speed });
    }
  });
});
criticalSpeeds.sort((p1, p2) => p1.x - p2.x);
const shownCriticalSpeeds = criticalSpeeds.slice(0, 10);

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Datasets ------------------------------------------------------------
const modeDatasets = modes.map((mode) => ({
  label: mode.name,
  data: speeds.map((speed) => ({ x: speed, y: mode.a + mode.b * speed })),
  borderColor: mode.color,
  backgroundColor: mode.color,
  borderWidth: 3.5,
  pointRadius: 0,
  tension: 0,
}));

const orderDatasets = engineOrders.map(({ order, dash }) => ({
  label: `${order}x Engine Order`,
  data: [
    { x: 0, y: 0 },
    { x: SPEED_MAX, y: (order * SPEED_MAX) / 60 },
  ],
  borderColor: t.ink,
  backgroundColor: t.ink,
  borderWidth: 2,
  borderDash: dash,
  pointRadius: 0,
  tension: 0,
}));

const criticalDataset = {
  label: "Critical Speeds",
  data: shownCriticalSpeeds,
  showLine: false,
  pointStyle: "rectRot",
  pointRadius: 9,
  pointBorderWidth: 2,
  backgroundColor: "#AE3030",
  borderColor: t.pageBg,
};

// --- Chart -----------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: { datasets: [...modeDatasets, ...orderDatasets, criticalDataset] },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "campbell-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
      },
      legend: {
        position: "bottom",
        labels: { color: t.ink, font: { size: 14 }, usePointStyle: true, boxWidth: 20, padding: 16 },
      },
    },
    scales: {
      x: {
        type: "linear",
        min: 0,
        max: SPEED_MAX,
        title: { display: true, text: "Rotational Speed (RPM)", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 }, stepSize: 1000 },
        grid: { color: t.grid },
      },
      y: {
        min: 0,
        max: FREQ_MAX,
        title: { display: true, text: "Natural Frequency (Hz)", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 }, stepSize: 25 },
        grid: { color: t.grid },
      },
    },
  },
});
