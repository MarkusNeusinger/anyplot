// anyplot.ai
// alluvial-basic: Basic Alluvial Diagram
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Cohort of 240 students tracked across four semesters as they move between
// performance tiers. Each column sums to 240 — the alluvial reads as a
// conserved population reshuffling between tiers, not independent bars.
const semesters = ["Semester 1", "Semester 2", "Semester 3", "Semester 4"];

const tiers = [
  { name: "Honors", color: t.palette[0], values: [30, 45, 65, 90] },
  { name: "Proficient", color: t.palette[2], values: [60, 70, 75, 80] },
  { name: "Developing", color: t.palette[1], values: [80, 75, 65, 50] },
  { name: "Needs Support", color: t.palette[4], values: [70, 50, 35, 20] },
];

// --- Flow ribbons: bezier bands linking each tier's segment across columns --
const alluvialFlows = {
  id: "alluvialFlows",
  beforeDatasetsDraw(chart) {
    const { ctx } = chart;
    const numColumns = chart.data.labels.length;
    ctx.save();
    chart.data.datasets.forEach((dataset, datasetIndex) => {
      const meta = chart.getDatasetMeta(datasetIndex);
      ctx.fillStyle = dataset.backgroundColor;
      ctx.globalAlpha = 0.45;
      for (let i = 0; i < numColumns - 1; i++) {
        const left = meta.data[i];
        const right = meta.data[i + 1];
        if (!left || !right) continue;

        const lx = left.x + left.width / 2;
        const rx = right.x - right.width / 2;
        const midX = (lx + rx) / 2;
        const lTop = Math.min(left.y, left.base);
        const lBot = Math.max(left.y, left.base);
        const rTop = Math.min(right.y, right.base);
        const rBot = Math.max(right.y, right.base);

        ctx.beginPath();
        ctx.moveTo(lx, lTop);
        ctx.bezierCurveTo(midX, lTop, midX, rTop, rx, rTop);
        ctx.lineTo(rx, rBot);
        ctx.bezierCurveTo(midX, rBot, midX, lBot, lx, lBot);
        ctx.closePath();
        ctx.fill();
      }
    });
    ctx.restore();
  },
};

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels: semesters,
    datasets: tiers.map((tier) => ({
      label: tier.name,
      data: tier.values,
      backgroundColor: tier.color,
      borderColor: t.pageBg,
      borderWidth: 2,
      stack: "cohort",
      barPercentage: 1.0,
      categoryPercentage: 0.32,
    })),
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 8, right: 24, bottom: 8, left: 8 } },
    plugins: {
      title: {
        display: true,
        text: "alluvial-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 20 },
      },
      legend: {
        position: "bottom",
        labels: { color: t.ink, font: { size: 16 }, boxWidth: 18, padding: 20 },
      },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        stacked: true,
        ticks: { color: t.inkSoft, font: { size: 15 } },
        grid: { display: false },
        border: { color: t.inkSoft },
        title: { display: true, text: "Semester", color: t.ink, font: { size: 16 } },
      },
      y: {
        stacked: true,
        beginAtZero: true,
        suggestedMax: 250,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        border: { display: false },
        title: {
          display: true,
          text: "Students in tier",
          color: t.ink,
          font: { size: 16 },
        },
      },
    },
  },
  plugins: [alluvialFlows],
});
