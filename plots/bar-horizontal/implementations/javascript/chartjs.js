// anyplot.ai
// bar-horizontal: Horizontal Bar Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.1
// Quality: 70/100 | Created: 2026-08-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Native speakers by language, descending so the largest bar sits on top.
const languages = [
  "Mandarin Chinese",
  "Spanish",
  "English",
  "Hindi",
  "Arabic",
  "Bengali",
  "Portuguese",
  "Russian",
  "Japanese",
  "Vietnamese",
];
const speakersMillions = [941, 486, 380, 345, 274, 237, 232, 154, 123, 85];

// Brand green at full strength for the top-ranked bar, muted for the rest —
// a focal-point highlight layered on top of the sort order.
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
const barColors = speakersMillions.map((_, i) => (i === 0 ? t.palette[0] : hexToRgba(t.palette[0], 0.55)));

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -------------------------------------------------------------------
const title = "World's Most Spoken Languages · bar-horizontal · javascript · chartjs · anyplot.ai";

// Custom Chart.js plugin: draw the value at the end of each bar so exact
// speaker counts are readable without a separate legend or tooltip.
const valueLabelsPlugin = {
  id: "valueLabels",
  afterDatasetsDraw(chart) {
    const { ctx } = chart;
    const meta = chart.getDatasetMeta(0);
    ctx.save();
    ctx.font = `600 13px ${Chart.defaults.font.family}`;
    ctx.fillStyle = t.ink;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    meta.data.forEach((bar, i) => {
      ctx.fillText(`${speakersMillions[i]}M`, bar.x + 8, bar.y);
    });
    ctx.restore();
  },
};

new Chart(canvas, {
  type: "bar",
  data: {
    labels: languages,
    datasets: [
      {
        label: "Native Speakers (millions)",
        data: speakersMillions,
        backgroundColor: barColors,
        borderWidth: 0,
        barPercentage: 0.7,
        categoryPercentage: 0.8,
      },
    ],
  },
  plugins: [valueLabelsPlugin],
  options: {
    indexAxis: "y",
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 8, right: 56, bottom: 8, left: 8 } },
    plugins: {
      title: { display: true, text: title, color: t.ink, font: { size: 18, weight: "500" }, padding: { bottom: 20 } },
      legend: { display: false },
    },
    scales: {
      x: {
        beginAtZero: true,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "Native Speakers (millions)", color: t.ink, font: { size: 16 } },
        border: { color: t.inkSoft },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        border: { color: t.inkSoft },
      },
    },
  },
});
