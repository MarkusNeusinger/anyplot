// anyplot.ai
// polar-basic: Basic Polar Chart
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-07-24

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic): average wind speed by compass direction
const directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
const windSpeeds = [8.2, 6.5, 5.1, 7.8, 11.4, 14.2, 12.6, 9.3];

// --- Mount -----------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -----------------------------------------------------------------
new Chart(canvas, {
  type: "polarArea",
  data: {
    labels: directions,
    datasets: [
      {
        data: windSpeeds,
        backgroundColor: directions.map((_, i) => t.palette[i % t.palette.length]),
        borderColor: t.pageBg,
        borderWidth: 2,
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
        text: "polar-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
      },
      legend: { display: false },
    },
    scales: {
      r: {
        beginAtZero: true,
        ticks: { color: t.inkSoft, backdropColor: "transparent", font: { size: 14 } },
        grid: { color: t.grid },
        angleLines: { color: t.grid },
        pointLabels: { display: true, color: t.ink, font: { size: 16 } },
      },
    },
  },
});
