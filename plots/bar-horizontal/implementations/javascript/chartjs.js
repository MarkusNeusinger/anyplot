// anyplot.ai
// bar-horizontal: World's Most Spoken Languages
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-08-05

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

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -------------------------------------------------------------------
const title = "World's Most Spoken Languages · bar-horizontal · javascript · chartjs · anyplot.ai";

new Chart(canvas, {
  type: "bar",
  data: {
    labels: languages,
    datasets: [
      {
        label: "Native Speakers (millions)",
        data: speakersMillions,
        backgroundColor: t.palette[0],
        borderWidth: 0,
        barPercentage: 0.7,
        categoryPercentage: 0.8,
      },
    ],
  },
  options: {
    indexAxis: "y",
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 8, right: 32, bottom: 8, left: 8 } },
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
