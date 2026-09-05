//# anyplot-orientation: square
// anyplot.ai
// polar-line: Polar Line Plot
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data: average wind speed (mph) by compass direction, morning vs afternoon ---
// Chart.js has no continuous polar-line primitive; the "radar" chart type is a
// line plot in polar coordinates with evenly-spaced angular axes, which is
// exactly the spec's shape (theta = direction, radius = magnitude, line
// connects points in theta order, closing the loop back to 0 degrees).
const N_DIRECTIONS = 36;
const directionLabels = [];
const morningSpeed = [];
const afternoonSpeed = [];

// Tiny fixed-seed LCG for deterministic jitter (browser has no seeded RNG).
let seed = 42;
function nextRandom() {
  seed = (seed * 1103515245 + 12345) % 2147483648;
  return seed / 2147483648;
}

for (let i = 0; i < N_DIRECTIONS; i++) {
  const degrees = i * (360 / N_DIRECTIONS);
  directionLabels.push(`${degrees}°`);
  const morningJitter = (nextRandom() - 0.5) * 1.2;
  const afternoonJitter = (nextRandom() - 0.5) * 1.2;
  morningSpeed.push(
    Math.max(2, 8 + 6 * Math.cos((degrees - 225) * (Math.PI / 180)) + morningJitter)
  );
  afternoonSpeed.push(
    Math.max(2, 10 + 7 * Math.cos((degrees - 90) * (Math.PI / 180)) + afternoonJitter)
  );
}

// --- Mount -----------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -------------------------------------------------------------------
new Chart(canvas, {
  type: "radar",
  data: {
    labels: directionLabels,
    datasets: [
      {
        label: "Morning avg (mph)",
        data: morningSpeed,
        borderColor: t.palette[0],
        pointBackgroundColor: t.palette[0],
        pointRadius: 4,
        borderWidth: 3,
        fill: false,
        tension: 0,
      },
      {
        label: "Afternoon avg (mph)",
        data: afternoonSpeed,
        borderColor: t.palette[1],
        pointBackgroundColor: t.palette[1],
        pointRadius: 4,
        borderWidth: 3,
        fill: false,
        tension: 0,
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
        text: "polar-line · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        labels: {
          color: t.ink,
          font: { size: 16 },
          usePointStyle: true,
          pointStyle: "circle",
        },
      },
    },
    scales: {
      r: {
        beginAtZero: true,
        angleLines: { color: t.grid },
        grid: { color: t.grid },
        pointLabels: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: (label, index) => (index % 3 === 0 ? label : ""),
        },
        ticks: {
          color: t.inkSoft,
          backdropColor: "transparent",
          font: { size: 12 },
        },
      },
    },
  },
});
