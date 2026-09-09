// anyplot.ai
// sparkline-basic: Basic Sparkline
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-09-09
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic LCG) ------------------------------------
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1103515245 + 12345) % 2147483648;
    return state / 2147483648;
  };
}
const rand = lcg(42);

const POINTS = 45;
const dailySessions = [];
let sessions = 8200;
for (let i = 0; i < POINTS; i++) {
  sessions += (rand() - 0.42) * 260;
  sessions = Math.max(sessions, 4000);
  dailySessions.push(Math.round(sessions));
}
const labels = dailySessions.map((_, i) => `Day ${i + 1}`);

const lastIndex = dailySessions.length - 1;
const pointRadii = dailySessions.map((_, i) => (i === lastIndex ? 10 : 0));

const dataMin = Math.min(...dailySessions);
const dataMax = Math.max(...dailySessions);
const dataRange = dataMax - dataMin;
const yPad = dataRange * 3.2;

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
        data: dailySessions,
        borderColor: t.palette[0],
        borderWidth: 3.5,
        fill: false,
        tension: 0.35,
        pointRadius: pointRadii,
        pointHoverRadius: pointRadii,
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
    layout: { padding: { top: 10, right: 70, bottom: 20, left: 30 } },
    plugins: {
      title: {
        display: true,
        text: "sparkline-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { bottom: 30 },
      },
      legend: { display: false },
      tooltip: { enabled: false },
    },
    scales: {
      x: { display: false },
      y: { display: false, suggestedMin: dataMin - yPad, suggestedMax: dataMax + yPad },
    },
  },
});
