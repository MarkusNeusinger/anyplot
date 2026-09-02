// anyplot.ai
// range-interval: Range Interval Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) — Berlin monthly temperature range ----
const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const lowC = [0, 0, 2, 5, 9, 13, 15, 14, 11, 7, 3, 1];
const highC = [3, 5, 9, 14, 19, 22, 24, 24, 19, 13, 7, 4];
const ranges = months.map((_, i) => [lowC[i], highC[i]]);
const widestIdx = months.reduce((best, _, i) => (highC[i] - lowC[i] > highC[best] - lowC[best] ? i : best), 0);

// brand green fill, hardcoded rgba (t.palette[0] is always #009E73) — widest-range month gets a stronger fill
const fillColors = months.map((_, i) => (i === widestIdx ? "rgba(0, 158, 115, 0.9)" : "rgba(0, 158, 115, 0.5)"));
const borderWidths = months.map((_, i) => (i === widestIdx ? 3 : 2));

// --- Title sizing (scale down once the title exceeds the ~67-char baseline) -
const title = "Berlin Monthly Temperature Range · range-interval · javascript · chartjs · anyplot.ai";
const titleFontSize = Math.max(14, Math.round(22 * Math.min(1, 67 / title.length)));

// --- Mount -----------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -----------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels: months,
    datasets: [
      {
        label: "Temperature range",
        data: ranges,
        backgroundColor: fillColors,
        borderColor: t.palette[0],
        borderWidth: borderWidths,
        borderSkipped: false,
        borderRadius: 6,
        barPercentage: 0.6,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: { display: true, text: title, color: t.ink, font: { size: titleFontSize, weight: "500" } },
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx) => `Low ${lowC[ctx.dataIndex]}°C – High ${highC[ctx.dataIndex]}°C`,
        },
      },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        title: { display: true, text: "Month", color: t.ink, font: { size: 16 } },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 14 }, callback: (v) => `${v}°C` },
        grid: { color: t.grid },
        title: { display: true, text: "Average Temperature (°C)", color: t.ink, font: { size: 16 } },
      },
    },
  },
});
