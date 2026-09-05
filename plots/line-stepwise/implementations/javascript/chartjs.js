// anyplot.ai
// line-stepwise: Step Line Plot
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 81/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Number of elevators actively in service, sampled hourly
const hours = [
  "06:00", "07:00", "08:00", "09:00", "10:00", "11:00", "12:00",
  "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00",
  "20:00", "21:00",
];
const activeElevators = [
  2, 2, 4, 4, 4, 3, 3,
  3, 3, 3, 4, 5, 5, 4,
  3, 2,
];
// Peak coverage window (5 elevators, 17:00-18:00) gets a larger point marker
const peakRadius = activeElevators.map((v) => (v === 5 ? 7 : 4));

// --- Mount -----------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -----------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    labels: hours,
    datasets: [
      {
        label: "Elevators in service",
        data: activeElevators,
        stepped: "before",
        borderColor: t.palette[0],
        backgroundColor: t.palette[0],
        borderWidth: 3.5,
        pointRadius: peakRadius,
        pointHoverRadius: peakRadius,
        pointBackgroundColor: t.palette[0],
        pointBorderColor: t.pageBg,
        pointBorderWidth: 1.5,
        fill: false,
        tension: 0,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 8, right: 24, bottom: 4, left: 4 } },
    plugins: {
      title: {
        display: true,
        text: "line-stepwise · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 24, weight: "500" },
        padding: { bottom: 20 },
      },
      legend: { display: false },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 14 }, maxRotation: 0, autoSkip: true, maxTicksLimit: 10 },
        grid: { display: false },
        title: { display: true, text: "Time of Day", color: t.ink, font: { size: 16 } },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 14 }, stepSize: 1 },
        grid: { color: t.grid },
        title: { display: true, text: "Elevators in Service", color: t.ink, font: { size: 16 } },
        beginAtZero: true,
        suggestedMax: 6,
      },
    },
  },
});
