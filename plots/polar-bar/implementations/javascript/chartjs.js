// anyplot.ai
// polar-bar: Polar Bar Chart (Wind Rose)
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 82/100 | Created: 2026-09-05

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
// Share of observed hours the wind blew from each compass direction at a
// coastal weather station over one year.
const directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
const frequency = [8, 12, 15, 10, 14, 20, 13, 8];
const dominantIndex = frequency.indexOf(Math.max(...frequency));

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
        borderWidth: directions.map((_, i) => (i === dominantIndex ? 5 : 3)),
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: 8 },
    plugins: {
      title: {
        display: true,
        text: "Wind Rose · polar-bar · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      subtitle: {
        display: true,
        text: "Radial axis: frequency (% of hours)",
        color: t.inkSoft,
        font: { size: 14 },
        padding: { bottom: 12 },
      },
      legend: {
        position: "bottom",
        align: "center",
        labels: { color: t.ink, font: { size: 14 }, boxWidth: 16, padding: 12 },
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
