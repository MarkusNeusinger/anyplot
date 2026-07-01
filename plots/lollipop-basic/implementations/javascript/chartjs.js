// anyplot.ai
// lollipop-basic: Basic Lollipop Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.0
// Quality: 89/100 | Created: 2026-07-01
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Data (website traffic by marketing channel, sorted descending) --------
const channels = [
  "Paid Search", "Organic", "Social Media", "Blog",
  "Direct", "Email", "Influencer", "Referral",
  "Video Ads", "Podcast"
];
const visitors = [312, 285, 198, 176, 165, 142, 118, 89, 67, 43];

// Emphasize top performer with a larger dot
const dotRadii = visitors.map((_, i) => i === 0 ? 20 : 14);

// --- Mount -----------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Inline plugin: value label above the top performer -------------------
const topLabelPlugin = {
  id: "topLabel",
  afterDraw(chart) {
    const ctx = chart.ctx;
    const meta = chart.getDatasetMeta(1); // line dataset (dots)
    const topPoint = meta.data[0];
    ctx.save();
    ctx.font = "bold 15px sans-serif";
    ctx.fillStyle = t.ink;
    ctx.textAlign = "center";
    ctx.textBaseline = "bottom";
    ctx.fillText("312K", topPoint.x, topPoint.y - dotRadii[0] - 6);
    ctx.restore();
  },
};

// --- Chart (lollipop: thin bars as stems + line points as dots) -----------
new Chart(canvas, {
  type: "bar",
  data: {
    labels: channels,
    datasets: [
      {
        // Stems: very thin bars from baseline to value
        type: "bar",
        label: "Visitors (K)",
        data: visitors,
        backgroundColor: t.palette[0],
        barThickness: 3,
        order: 1,
      },
      {
        // Dots: large circular points at each value; top performer is larger
        type: "line",
        label: "Visitors (K)",
        data: visitors,
        backgroundColor: t.palette[0],
        borderColor: t.pageBg,
        borderWidth: 2,
        pointRadius: dotRadii,
        pointHoverRadius: dotRadii.map(r => r + 2),
        showLine: false,
        order: 2,
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
        text: "lollipop-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "bold" },
        padding: { top: 20, bottom: 30 },
      },
      legend: {
        display: false,
      },
    },
    scales: {
      x: {
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
        },
        grid: { display: false },
        title: {
          display: true,
          text: "Marketing Channel",
          color: t.ink,
          font: { size: 16 },
          padding: { top: 12 },
        },
      },
      y: {
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
        },
        grid: { color: t.grid },
        beginAtZero: true,
        title: {
          display: true,
          text: "Monthly Visitors (thousands)",
          color: t.ink,
          font: { size: 16 },
          padding: { bottom: 12 },
        },
      },
    },
    layout: {
      padding: { top: 40, bottom: 20, left: 30, right: 30 },
    },
  },
  plugins: [topLabelPlugin],
});
