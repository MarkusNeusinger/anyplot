// anyplot.ai
// line-timeseries-rolling: Time Series with Rolling Average Overlay
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) ------------------------------------
const WINDOW_DAYS = 7;
const NUM_DAYS = 120;

let seed = 42;
function nextRandom() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

const startDate = new Date(Date.UTC(2026, 0, 1));
const labels = [];
const dailyActiveUsers = [];

for (let i = 0; i < NUM_DAYS; i++) {
  const day = new Date(startDate);
  day.setUTCDate(day.getUTCDate() + i);
  labels.push(day.toISOString().slice(0, 10));

  const trend = 4200 + i * 9.5;
  const weekday = day.getUTCDay();
  const weekendDip = weekday === 0 || weekday === 6 ? -420 : 0;
  const noise = (nextRandom() - 0.5) * 520;
  dailyActiveUsers.push(Math.round(trend + weekendDip + noise));
}

const rollingAvg = dailyActiveUsers.map((_, i) => {
  if (i < WINDOW_DAYS - 1) return null;
  let sum = 0;
  for (let j = i - WINDOW_DAYS + 1; j <= i; j++) sum += dailyActiveUsers[j];
  return Math.round(sum / WINDOW_DAYS);
});

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -------------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    labels,
    datasets: [
      {
        label: "Raw Data",
        data: dailyActiveUsers,
        borderColor: hexToRgba(t.ink, 0.28),
        backgroundColor: hexToRgba(t.ink, 0.28),
        borderWidth: 1.5,
        pointRadius: 0,
        tension: 0,
        spanGaps: false,
      },
      {
        label: `Rolling Average (${WINDOW_DAYS}-day)`,
        data: rollingAvg,
        borderColor: t.palette[0],
        backgroundColor: t.palette[0],
        borderWidth: 4,
        pointRadius: 0,
        tension: 0.25,
        spanGaps: false,
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
        text: "line-timeseries-rolling · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 24 },
      },
      legend: {
        position: "top",
        align: "end",
        labels: { color: t.ink, font: { size: 16 }, boxWidth: 24, padding: 20 },
      },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 14 }, maxTicksLimit: 10 },
        grid: { color: t.grid },
        title: { display: true, text: "Date", color: t.ink, font: { size: 16 } },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "Daily Active Users", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
