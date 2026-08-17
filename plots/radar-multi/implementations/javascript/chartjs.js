// anyplot.ai
// radar-multi: Multi-Series Radar Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-08-17

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Wireless headphone models scored on a 0-100 scale across six attributes.
const categories = [
  "Sound Quality",
  "Battery Life",
  "Comfort",
  "Noise Cancelling",
  "Build Quality",
  "Value",
];

const models = [
  { name: "AuraSound Studio", scores: [88, 72, 80, 90, 75, 65] },
  { name: "PulseWave Air", scores: [70, 95, 85, 60, 82, 78] },
  { name: "EchoFit Sport", scores: [65, 60, 92, 55, 68, 90] },
];

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "radar",
  data: {
    labels: categories,
    datasets: models.map((model, i) => {
      const color = t.palette[i % t.palette.length];
      return {
        label: model.name,
        data: model.scores,
        backgroundColor: hexToRgba(color, 0.25),
        borderColor: color,
        borderWidth: 3,
        pointBackgroundColor: color,
        pointBorderColor: t.pageBg,
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
      };
    }),
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "radar-multi · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { bottom: 24 },
      },
      legend: {
        position: "bottom",
        labels: { color: t.ink, font: { size: 16 }, padding: 20 },
      },
    },
    scales: {
      r: {
        min: 0,
        max: 100,
        ticks: {
          stepSize: 20,
          color: t.inkSoft,
          font: { size: 12 },
          backdropColor: "transparent",
        },
        grid: { color: t.grid },
        angleLines: { color: t.grid },
        pointLabels: { color: t.ink, font: { size: 16 } },
      },
    },
  },
});
