// anyplot.ai
// step-basic: Basic Step Plot
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-07-25

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Auto-scaling group size for a web service over a 24h day. Each point marks
// a scaling event; the instance count holds constant until the next event.
const scalingEvents = [
  { hour: 0, instances: 4 },
  { hour: 2.5, instances: 8 },
  { hour: 5, instances: 14 },
  { hour: 7, instances: 22 },
  { hour: 9.5, instances: 30 },
  { hour: 12, instances: 26 },
  { hour: 14.5, instances: 20 },
  { hour: 17, instances: 24 },
  { hour: 19, instances: 16 },
  { hour: 21.5, instances: 10 },
  { hour: 24, instances: 4 },
];
const points = scalingEvents.map((e) => ({ x: e.hour, y: e.instances }));

const formatHour = (hour) => {
  const h = Math.floor(hour) % 24;
  const m = Math.round((hour - Math.floor(hour)) * 60);
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
};

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    datasets: [
      {
        label: "Active instances",
        data: points,
        stepped: "after",
        borderColor: t.palette[0],
        backgroundColor: t.palette[0],
        borderWidth: 3.5,
        pointRadius: 5,
        pointHoverRadius: 6,
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
        text: "step-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 20 },
      },
      legend: { display: false },
    },
    scales: {
      x: {
        type: "linear",
        min: 0,
        max: 24,
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          stepSize: 3,
          callback: (value) => formatHour(value),
        },
        grid: { display: false },
        title: { display: true, text: "Time of Day", color: t.ink, font: { size: 16 } },
      },
      y: {
        beginAtZero: true,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "Active Instances", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
