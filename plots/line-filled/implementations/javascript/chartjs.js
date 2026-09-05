// anyplot.ai
// line-filled: Filled Line Plot
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 87/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Daily active users over a 30-day product launch window.
let seed = 42;
function lcg() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}

const days = Array.from({ length: 30 }, (_, i) => i + 1);
const dailyActiveUsers = [];
let level = 2400;
for (let i = 0; i < days.length; i++) {
  level += 180 + (lcg() - 0.35) * 260;
  level = Math.max(level, 1800);
  dailyActiveUsers.push(Math.round(level));
}

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------------
const title = "line-filled · javascript · chartjs · anyplot.ai";

new Chart(canvas, {
  type: "line",
  data: {
    labels: days,
    datasets: [
      {
        label: "Daily active users",
        data: dailyActiveUsers,
        borderColor: t.palette[0],
        backgroundColor: t.palette[0] + "4D", // ~30% alpha fill
        borderWidth: 3.5,
        fill: "origin",
        pointRadius: 0,
        pointHoverRadius: 0,
        tension: 0.25,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 8, right: 24, bottom: 0, left: 0 } },
    plugins: {
      title: { display: true, text: title, color: t.ink, font: { size: 22, weight: "500" } },
      legend: { display: false },
    },
    scales: {
      x: {
        title: { display: true, text: "Day since launch", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 }, maxTicksLimit: 10 },
        grid: { display: false },
      },
      y: {
        title: { display: true, text: "Daily active users", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        beginAtZero: true,
      },
    },
  },
});
