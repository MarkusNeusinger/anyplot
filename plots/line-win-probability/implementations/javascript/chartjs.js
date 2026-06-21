// anyplot.ai
// line-win-probability: Win Probability Chart
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-21

const t = window.ANYPLOT_TOKENS;

// Deterministic LCG for reproducible pseudo-random data
let seed = 42;
function lcg() {
  seed = (seed * 1664525 + 1013904223) >>> 0;
  return seed / 4294967295;
}

// NBA game: Lakers (home) vs Celtics (away), 48 minutes
// Narrative: home team trails in Q2, stages comeback, seals win in Q4
const TOTAL_MINUTES = 48;
const N = 97; // ~one point per 30 seconds

function trendAt(m) {
  if (m < 4)  return 0.500 + m * 0.010;
  if (m < 12) return 0.540 + (m - 4) * 0.004;
  if (m < 18) return 0.572 - (m - 12) * 0.042;
  if (m < 24) return 0.320 - (m - 18) * 0.005;
  if (m < 30) return 0.290 + (m - 24) * 0.038;
  if (m < 36) return 0.518 + (m - 30) * 0.008;
  if (m < 42) return 0.566 + (m - 36) * 0.038;
  return 0.794 + (m - 42) * 0.017;
}

const points = Array.from({ length: N }, (_, i) => {
  const m = (i / (N - 1)) * TOTAL_MINUTES;
  const trend = trendAt(m);
  const noise = (lcg() - 0.5) * 0.055;
  const prob = Math.min(0.98, Math.max(0.02, trend + noise));
  return { x: +m.toFixed(2), y: +(prob * 100).toFixed(1) };
});

const refLine = points.map(p => ({ x: p.x, y: 50 }));

// Imprint palette: home team = brand green, away team = matte red (semantic: win/loss)
const homeColor = t.palette[0]; // #009E73
const awayColor = t.palette[4]; // #AE3030
const HOME_FILL = "rgba(0, 158, 115, 0.22)";
const AWAY_FILL = "rgba(174, 48, 48, 0.22)";

// Quarter boundary + annotation plugin
const quarterPlugin = {
  id: "quarters",
  afterDraw(chart) {
    const { ctx, chartArea: ca, scales } = chart;
    ctx.save();

    // Quarter dividers
    [12, 24, 36].forEach((q, i) => {
      const x = scales.x.getPixelForValue(q);
      ctx.beginPath();
      ctx.setLineDash([7, 5]);
      ctx.strokeStyle = t.inkSoft + "70";
      ctx.lineWidth = 1.5;
      ctx.moveTo(x, ca.top);
      ctx.lineTo(x, ca.bottom);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = t.inkSoft;
      ctx.font = "bold 13px sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(`Q${i + 2}`, x + 5, ca.top + 20);
    });

    // Q1 label
    ctx.setLineDash([]);
    ctx.fillStyle = t.inkSoft;
    ctx.font = "bold 13px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText("Q1", scales.x.getPixelForValue(0) + 5, ca.top + 20);

    // HOME / AWAY directional labels
    ctx.font = "bold 14px sans-serif";
    ctx.textAlign = "right";
    ctx.fillStyle = homeColor;
    ctx.fillText("HOME WINS ↑", ca.right - 10, ca.top + 22);
    ctx.fillStyle = awayColor;
    ctx.fillText("AWAY WINS ↓", ca.right - 10, ca.bottom - 10);

    // Final score
    ctx.fillStyle = t.ink;
    ctx.font = "bold 15px sans-serif";
    ctx.textAlign = "right";
    ctx.fillText("Final: Lakers 112 – Celtics 101", ca.right - 10, ca.top + 44);

    ctx.restore();
  },
};

const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

new Chart(canvas, {
  type: "line",
  data: {
    datasets: [
      {
        label: "Home Win Probability",
        data: points,
        borderColor: homeColor,
        borderWidth: 2.5,
        pointRadius: 0,
        fill: {
          target: { value: 50 },
          above: HOME_FILL,
          below: AWAY_FILL,
        },
        tension: 0.3,
      },
      {
        label: "_ref50",
        data: refLine,
        borderColor: t.inkSoft + "90",
        borderWidth: 1.5,
        borderDash: [8, 5],
        pointRadius: 0,
        fill: false,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 30, right: 24, bottom: 10, left: 10 } },
    plugins: {
      title: {
        display: true,
        text: "line-win-probability · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "600" },
        padding: { bottom: 20 },
      },
      legend: {
        labels: {
          color: t.ink,
          font: { size: 14 },
          filter: item => !item.text.startsWith("_"),
        },
      },
    },
    scales: {
      x: {
        type: "linear",
        min: 0,
        max: 48,
        ticks: {
          color: t.inkSoft,
          font: { size: 13 },
          stepSize: 6,
          callback: v => `${v}'`,
        },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Game Time (minutes)",
          color: t.ink,
          font: { size: 15 },
        },
      },
      y: {
        min: 0,
        max: 100,
        ticks: {
          color: t.inkSoft,
          font: { size: 13 },
          stepSize: 25,
          callback: v => `${v}%`,
        },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Home Team Win Probability",
          color: t.ink,
          font: { size: 15 },
        },
      },
    },
  },
  plugins: [quarterPlugin],
});
