// anyplot.ai
// pie-basic: Basic Pie Chart
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-02
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// Data — global cloud-infrastructure market share (illustrative 2025 figures)
const labels = [
  "AWS",
  "Microsoft Azure",
  "Google Cloud",
  "Alibaba Cloud",
  "Oracle Cloud",
  "Others",
];
const shares = [31, 25, 11, 4, 3, 26];

// Imprint palette positions 1→6 — first slice is always brand green (#009E73).
const sliceColors = shares.map((_, i) => t.palette[i % t.palette.length]);

// Spec invites a slight explode on the largest (or smallest) slice. Pulling the
// leader out by a constant pixel offset draws the eye without distorting angle.
const maxIdx = shares.indexOf(Math.max(...shares));
const sliceOffsets = shares.map((_, i) => (i === maxIdx ? 30 : 0));

const total = shares.reduce((a, b) => a + b, 0);

// Custom plugin — percent label at each slice's geometric midpoint. Slivers
// (< 4%) defer to the legend, which spells out the percentage anyway.
const percentLabels = {
  id: "percentLabels",
  afterDatasetsDraw(chart) {
    const { ctx } = chart;
    const meta = chart.getDatasetMeta(0);
    ctx.save();
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font =
      '600 26px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';
    ctx.fillStyle = "#FAF8F1";
    meta.data.forEach((arc, i) => {
      const pct = (shares[i] / total) * 100;
      if (pct < 4) return;
      const mid = (arc.startAngle + arc.endAngle) / 2;
      const r = (arc.innerRadius + arc.outerRadius) / 2;
      const x = arc.x + Math.cos(mid) * r;
      const y = arc.y + Math.sin(mid) * r;
      ctx.fillText(`${pct.toFixed(0)}%`, x, y);
    });
    ctx.restore();
  },
};

// Mount
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

new Chart(canvas, {
  type: "pie",
  data: {
    labels,
    datasets: [
      {
        label: "Market share",
        data: shares,
        backgroundColor: sliceColors,
        borderColor: t.pageBg,
        borderWidth: 3,
        offset: sliceOffsets,
        hoverOffset: 14,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 24, right: 24, bottom: 24, left: 24 } },
    plugins: {
      title: {
        display: true,
        text: "pie-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 34, weight: "500" },
        padding: { top: 4, bottom: 36 },
      },
      legend: {
        position: "right",
        align: "center",
        labels: {
          color: t.ink,
          font: { size: 20 },
          boxWidth: 26,
          boxHeight: 20,
          padding: 20,
          generateLabels: (chart) => {
            const data = chart.data;
            const arr = data.datasets[0].data;
            return data.labels.map((label, i) => ({
              text: `${label} — ${arr[i]}%`,
              fillStyle: data.datasets[0].backgroundColor[i],
              strokeStyle: data.datasets[0].backgroundColor[i],
              lineWidth: 0,
              index: i,
            }));
          },
        },
      },
      tooltip: {
        backgroundColor: t.elevatedBg,
        titleColor: t.ink,
        bodyColor: t.inkSoft,
        borderColor: t.grid,
        borderWidth: 1,
        padding: 12,
        titleFont: { size: 14, weight: "600" },
        bodyFont: { size: 13 },
        displayColors: false,
        callbacks: {
          label: (ctx) => `${ctx.parsed}% of global spend`,
        },
      },
    },
  },
  plugins: [percentLabels],
});
