// anyplot.ai
// streamgraph-basic: Basic Stream Graph
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-08-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
const months = [
  "Jan 24", "Feb 24", "Mar 24", "Apr 24", "May 24", "Jun 24",
  "Jul 24", "Aug 24", "Sep 24", "Oct 24", "Nov 24", "Dec 24",
  "Jan 25", "Feb 25", "Mar 25", "Apr 25", "May 25", "Jun 25",
  "Jul 25", "Aug 25", "Sep 25", "Oct 25", "Nov 25", "Dec 25",
];
const genres = ["Pop", "Hip-Hop", "Electronic", "Rock", "Jazz"];

// Smooth seasonal listening-hour trends (thousands of hours) per genre
const baseHours = [42, 35, 28, 24, 14];
const amplitude = [10, 14, 9, 6, 4];
const periodMonths = [12, 9, 6, 14, 18];
const phaseShift = [0, 2, 5, 8, 3];
const series = genres.map((_, i) =>
  months.map((_, m) =>
    Math.max(
      2,
      Math.round(
        baseHours[i] +
          amplitude[i] * Math.sin((2 * Math.PI * (m + phaseShift[i])) / periodMonths[i])
      )
    )
  )
);

// Centered (symmetric) baseline so the stack reads as a river, not a bar stack
const baseline = months.map((_, m) => {
  const total = series.reduce((sum, s) => sum + s[m], 0);
  return -total / 2;
});

let cumulative = baseline.slice();
const layerTops = series.map((s) => {
  cumulative = cumulative.map((c, m) => c + s[m]);
  return cumulative.slice();
});

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
const datasets = [
  {
    label: "",
    data: baseline,
    borderWidth: 0,
    pointRadius: 0,
    fill: false,
    tension: 0.4,
    cubicInterpolationMode: "monotone",
  },
  ...genres.map((genre, i) => ({
    label: genre,
    data: layerTops[i],
    borderColor: t.palette[i % t.palette.length],
    backgroundColor: t.palette[i % t.palette.length],
    borderWidth: 0,
    pointRadius: 0,
    fill: i,
    tension: 0.4,
    cubicInterpolationMode: "monotone",
  })),
];

new Chart(canvas, {
  type: "line",
  data: { labels: months, datasets },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    interaction: { mode: "nearest", intersect: false },
    plugins: {
      title: {
        display: true,
        text: "streamgraph-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        labels: {
          color: t.ink,
          font: { size: 16 },
          filter: (item) => item.text !== "",
        },
      },
    },
    scales: {
      x: {
        type: "category",
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          maxRotation: 0,
          autoSkip: true,
          maxTicksLimit: 12,
        },
        grid: { display: false },
        title: { display: true, text: "Month", color: t.ink, font: { size: 16 } },
      },
      y: {
        display: false,
      },
    },
  },
});
