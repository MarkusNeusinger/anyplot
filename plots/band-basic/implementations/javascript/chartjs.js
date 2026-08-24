// anyplot.ai
// band-basic: Basic Band Plot
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-08-24

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// 30-day revenue forecast with a widening 95% confidence interval — the
// classic fan-chart shape: uncertainty compounds the further out the
// forecast reaches.
let seed = 42;
const rand = () => {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
};

const days = Array.from({ length: 45 }, (_, i) => i + 1);
const revenueCenter = days.map(
  (day) => 100 + 2.4 * day + 14 * Math.sin(day / 6)
);
const revenueUpper = days.map((day, i) => {
  const spread = 3 + 0.85 * day + (rand() - 0.5) * 2.5;
  return revenueCenter[i] + spread;
});
const revenueLower = days.map((day, i) => {
  const spread = 3 + 0.85 * day + (rand() - 0.5) * 2.5;
  return revenueCenter[i] - spread;
});

// --- Mount -----------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -----------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    labels: days,
    datasets: [
      {
        label: "",
        data: revenueLower,
        borderWidth: 0,
        pointRadius: 0,
        fill: false,
        tension: 0.35,
      },
      {
        label: "95% Confidence Interval",
        data: revenueUpper,
        borderWidth: 0,
        pointRadius: 0,
        backgroundColor: `${t.palette[0]}33`,
        fill: "-1",
        tension: 0.35,
      },
      {
        label: "Forecast",
        data: revenueCenter,
        borderColor: t.palette[0],
        backgroundColor: t.palette[0],
        borderWidth: 3,
        pointRadius: 0,
        fill: false,
        tension: 0.35,
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
        text: "band-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        labels: {
          color: t.ink,
          font: { size: 16 },
          filter: (item) => item.text,
        },
      },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        title: { display: true, text: "Day", color: t.ink, font: { size: 16 } },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Revenue ($K)",
          color: t.ink,
          font: { size: 16 },
        },
      },
    },
  },
});
