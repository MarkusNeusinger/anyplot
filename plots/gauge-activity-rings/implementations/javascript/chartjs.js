// anyplot.ai
// gauge-activity-rings: Activity Rings Progress Chart
// Library: chartjs 4.4.7 | JavaScript 22.22.3
// Quality: 88/100 | Created: 2026-06-14
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Helpers ---
function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// --- Data (daily fitness summary) ---
const rings = [
  { label: "Move",     value: 420, goal: 600, unit: "kcal" },
  { label: "Exercise", value: 38,  goal: 30,  unit: "min"  },
  { label: "Stand",    value: 9,   goal: 12,  unit: "hr"   },
];

const datasets = rings.map((ring, i) => {
  const fraction = Math.min(ring.value / ring.goal, 1.0);
  const color = t.palette[i];
  return {
    label: ring.label,
    data: [fraction, 1 - fraction],
    backgroundColor: [color, hexToRgba(color, 0.15)],
    borderWidth: 0,
    borderRadius: (ctx) => (ctx.dataIndex === 0 ? 32 : 0),
  };
});

const avgPct = Math.round(
  rings.reduce((sum, r) => sum + Math.min(r.value / r.goal, 1), 0) / rings.length * 100
);

// --- Mount ---
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Plugin: center summary text ---
const centerTextPlugin = {
  id: "centerText",
  afterDraw(chart) {
    const { ctx, chartArea } = chart;
    const cx = (chartArea.left + chartArea.right) / 2;
    const cy = (chartArea.top + chartArea.bottom) / 2;
    ctx.save();
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font = `bold 62px system-ui, sans-serif`;
    ctx.fillStyle = t.ink;
    ctx.fillText(`${avgPct}%`, cx, cy - 30);
    ctx.font = `20px system-ui, sans-serif`;
    ctx.fillStyle = t.inkSoft;
    ctx.fillText("avg. complete", cx, cy + 30);
    ctx.restore();
  },
};

// --- Chart ---
new Chart(canvas, {
  type: "doughnut",
  plugins: [centerTextPlugin],
  data: {
    labels: ["Progress", "Remaining"],
    datasets,
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    rotation: -90,
    circumference: 360,
    cutout: "42%",
    plugins: {
      title: {
        display: true,
        text: "gauge-activity-rings · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { top: 16, bottom: 16 },
      },
      legend: {
        display: true,
        position: "bottom",
        labels: {
          color: t.ink,
          font: { size: 14 },
          padding: 28,
          usePointStyle: true,
          pointStyle: "circle",
          generateLabels() {
            return rings.map((ring, i) => {
              const fraction = ring.value / ring.goal;
              const pct = Math.round(fraction * 100);
              const prefix = fraction > 1 ? ">" : "";
              return {
                text: `${ring.label}  ·  ${ring.value} / ${ring.goal} ${ring.unit}  ·  ${prefix}${pct}%`,
                fillStyle: t.palette[i],
                strokeStyle: "transparent",
                lineWidth: 0,
                hidden: false,
                datasetIndex: i,
                pointStyle: "circle",
              };
            });
          },
        },
      },
      tooltip: { enabled: false },
    },
  },
});
