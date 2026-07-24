// anyplot.ai
// polar-basic: Basic Polar Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.1
// Quality: 83/100 | Created: 2026-07-24

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic): average wind speed by compass direction
const directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
const windSpeeds = [8.2, 6.5, 5.1, 7.8, 11.4, 14.2, 12.6, 9.3];
const maxSpeed = Math.max(...windSpeeds);
const prevailingIndex = windSpeeds.indexOf(maxSpeed);

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
        borderColor: directions.map((_, i) => (i === prevailingIndex ? t.ink : t.pageBg)),
        borderWidth: directions.map((_, i) => (i === prevailingIndex ? 3 : 2)),
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
        font: { size: 22, weight: "600" },
      },
      subtitle: {
        display: true,
        text: "Average Wind Speed (km/h) by Compass Direction — SW prevails",
        color: t.inkSoft,
        font: { size: 14, style: "italic" },
        padding: { bottom: 12 },
      },
      legend: { display: false },
    },
    scales: {
      r: {
        beginAtZero: true,
        max: 15,
        ticks: {
          color: t.inkSoft,
          backdropColor: "transparent",
          font: { size: 14 },
          stepSize: 5,
        },
        grid: { color: t.grid },
        angleLines: { color: t.grid },
        pointLabels: { display: true, color: t.ink, font: { size: 16 } },
      },
    },
  },
});
