// anyplot.ai
// line-filled: Filled Line Plot
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-09-05

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
  let value = Math.round(level);
  // Weekend-style lull around day 20 breaks the otherwise steady climb.
  if (days[i] === 20) value = Math.round(value * 0.9);
  dailyActiveUsers.push(value);
}
const peakIndex = dailyActiveUsers.length - 1;

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------------
const title = "line-filled · javascript · chartjs · anyplot.ai";

// Vertical gradient: brand green at the line fading to transparent at the baseline.
function fillGradient(context) {
  const { chart } = context;
  const { ctx, chartArea } = chart;
  if (!chartArea) return t.palette[0] + "4D";
  const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
  gradient.addColorStop(0, t.palette[0] + "80");
  gradient.addColorStop(1, t.palette[0] + "00");
  return gradient;
}

new Chart(canvas, {
  type: "line",
  data: {
    labels: days,
    datasets: [
      {
        label: "Daily active users",
        data: dailyActiveUsers,
        borderColor: t.palette[0],
        backgroundColor: fillGradient,
        borderWidth: 3.5,
        borderCapStyle: "round",
        borderJoinStyle: "round",
        fill: "origin",
        pointRadius: (context) => (context.dataIndex === peakIndex ? 6 : 0),
        pointHoverRadius: 0,
        pointBackgroundColor: t.palette[0],
        pointBorderColor: t.pageBg,
        pointBorderWidth: 2,
        tension: 0.25,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 8, right: 28, bottom: 4, left: 4 } },
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
