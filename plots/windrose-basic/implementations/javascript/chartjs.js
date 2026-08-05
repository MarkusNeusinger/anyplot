// anyplot.ai
// windrose-basic: Wind Rose Chart
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-08-05
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// One year of hourly wind observations from a coastal weather station,
// binned into 8 compass sectors × 4 speed classes. Values are % of all
// observations and sum to 100 (calm-sector totals show the prevailing
// westerly/south-westerly wind with a secondary north-westerly lobe from
// post-frontal outflow).
const directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
const speedBinLabels = ["0–5 m/s", "5–10 m/s", "10–15 m/s", "15+ m/s"];

const frequencyCalm = [2.5, 2.2, 2.2, 2.8, 3.5, 5.0, 5.0, 4.0];
const frequencyLight = [2.0, 1.8, 1.8, 2.5, 3.8, 8.0, 8.5, 6.0];
const frequencyModerate = [1.0, 0.7, 0.7, 1.2, 2.5, 7.0, 7.5, 4.5];
const frequencyStrong = [0.5, 0.3, 0.3, 0.5, 1.2, 4.0, 4.0, 2.5];
const frequencyBySpeedBin = [
  frequencyCalm,
  frequencyLight,
  frequencyModerate,
  frequencyStrong,
];

// Chart.js polarArea draws dataset 0 last (on top). Feeding it the running
// cumulative sum per bin — smallest (calm) first, total last — turns the
// overlapping wedges into an honest stacked ring per direction: each dataset's
// arc reaches exactly its own cumulative frequency, so the visible band width
// between two rings equals that bin's real share, not an approximation.
const cumulativeBySpeedBin = frequencyBySpeedBin.map((_, bin) =>
  directions.map((_, dir) =>
    frequencyBySpeedBin
      .slice(0, bin + 1)
      .reduce((sum, series) => sum + series[dir], 0),
  ),
);

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "polarArea",
  data: {
    labels: directions,
    datasets: frequencyBySpeedBin.map((_, bin) => ({
      data: cumulativeBySpeedBin[bin],
      backgroundColor: t.palette[bin],
      borderColor: t.pageBg,
      borderWidth: 2,
    })),
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "windrose-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
      },
      subtitle: {
        display: true,
        text: "Frequency of observations (%)",
        color: t.inkSoft,
        font: { size: 15 },
        padding: { bottom: 16 },
      },
      legend: {
        position: "bottom",
        labels: {
          color: t.inkSoft,
          font: { size: 14 },
          boxWidth: 20,
          boxHeight: 14,
          // Default polarArea legend lists one entry per direction, all colored
          // from dataset 0 — not useful here. Build one entry per speed bin instead.
          generateLabels: (chart) =>
            speedBinLabels.map((label, bin) => ({
              text: label,
              fillStyle: t.palette[bin],
              strokeStyle: t.palette[bin],
              fontColor: t.inkSoft,
              index: bin,
              hidden: !chart.isDatasetVisible(bin),
            })),
        },
        onClick: (evt, item, legend) => {
          const chart = legend.chart;
          chart.setDatasetVisibility(
            item.index,
            !chart.isDatasetVisible(item.index),
          );
          chart.update();
        },
      },
    },
    scales: {
      r: {
        beginAtZero: true,
        angleLines: { color: t.grid },
        grid: { color: t.grid, circular: true },
        pointLabels: {
          display: true,
          color: t.ink,
          font: { size: 16, weight: "500" },
        },
        ticks: {
          color: t.ink,
          // z > 0 draws tick labels after the datasets (see Chart.js core.scale
          // _layers()) — without it the opaque wedges paint over the numbers
          // wherever a wedge's radius exceeds a gridline.
          z: 1,
          showLabelBackdrop: true,
          backdropColor: t.elevatedBg,
          backdropPadding: 4,
          font: { size: 13 },
          callback: (value) => value + "%",
        },
      },
    },
  },
});
