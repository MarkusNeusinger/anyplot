// anyplot.ai
// stem-basic: Basic Stem Plot
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-07-25

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Poisson probability mass function, lambda = 6 emails/hour, k = 0..19.
const LAMBDA = 6;
const counts = Array.from({ length: 20 }, (_, k) => k);
const probabilities = [];
let p = Math.exp(-LAMBDA);
for (const k of counts) {
  if (k > 0) p = (p * LAMBDA) / k;
  probabilities.push(p);
}
const labels = counts.map((k) => k.toString());

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart (bar stems + point-only line dataset draws the markers) ----------
new Chart(canvas, {
  data: {
    labels,
    datasets: [
      {
        type: "bar",
        label: "Probability",
        data: probabilities,
        backgroundColor: t.palette[0],
        borderWidth: 0,
        barThickness: 5,
      },
      {
        type: "line",
        label: "Probability",
        data: probabilities,
        showLine: false,
        pointRadius: 9,
        pointBackgroundColor: t.palette[0],
        pointBorderColor: t.pageBg,
        pointBorderWidth: 2,
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
        text: "stem-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { bottom: 24 },
      },
      legend: { display: false },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        title: { display: true, text: "Emails Received per Hour (k)", color: t.ink, font: { size: 16 } },
      },
      y: {
        beginAtZero: true,
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: (v) => v.toFixed(2),
        },
        grid: { color: t.grid },
        title: { display: true, text: "P(X = k)", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
