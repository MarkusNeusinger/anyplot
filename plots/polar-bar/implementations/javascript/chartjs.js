// anyplot.ai
// polar-bar: Polar Bar Chart (Wind Rose)
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-05

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Share of observed hours the wind blew from each compass direction at a
// coastal weather station over one year.
const directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
const frequency = [8, 12, 15, 10, 14, 20, 13, 8];

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -------------------------------------------------------------------
new Chart(canvas, {
  type: "polarArea",
  data: {
    labels: directions,
    datasets: [
      {
        label: "Frequency (%)",
        data: frequency,
        backgroundColor: directions.map((_, i) => t.palette[i % t.palette.length]),
        borderColor: t.pageBg,
        borderWidth: 3,
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
        text: "Wind Rose · polar-bar · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        position: "right",
        labels: { color: t.ink, font: { size: 16 } },
      },
    },
    scales: {
      r: {
        ticks: {
          color: t.inkSoft,
          backdropColor: "transparent",
          font: { size: 14 },
        },
        grid: { color: t.grid },
        angleLines: { color: t.grid },
      },
    },
  },
});
