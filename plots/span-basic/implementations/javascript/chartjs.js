// anyplot.ai
// span-basic: Basic Span Plot (Highlighted Region)
// Library: chartjs 4.4.7 | JavaScript 22.22.3
// Quality: pending | Created: 2026-07-25

const t = window.ANYPLOT_TOKENS;

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// Tiny fixed-seed LCG — the browser has no seeded RNG
function lcg(seed) {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 4294967296;
  };
}
const rand = lcg(20260725);

// --- Data: illustrative equity index, monthly, 2006-2012 -------------------
const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const START_YEAR = 2006;
const MONTHS = 84; // Jan 2006 - Dec 2012

// Two vertical spans: recession periods marking market downturns
const spans = [
  { startIdx: 24, endIdx: 41, label: "Financial Crisis" }, // Jan 2008 - Jun 2009
  { startIdx: 67, endIdx: 70, label: "Debt-Ceiling Crisis" }, // Aug 2011 - Nov 2011
];
const inAnySpan = (i) => spans.some((s) => i >= s.startIdx && i <= s.endIdx);

const labels = [];
const indexValues = [];
let index = 100;
for (let i = 0; i < MONTHS; i++) {
  const year = START_YEAR + Math.floor(i / 12);
  labels.push(`${MONTH_NAMES[i % 12]} '${String(year).slice(2)}`);

  const drift = inAnySpan(i) ? -0.018 : 0.0075;
  const noise = (rand() - 0.5) * 0.05;
  index *= 1 + drift + noise;
  indexValues.push(Math.round(index * 100) / 100);
}

// --- Mount -------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// Inline plugin: shade the crisis periods behind the line, full plot height.
// Drawn in beforeDatasetsDraw so the line renders on top of the fill.
const spanHighlight = {
  id: "spanHighlight",
  beforeDatasetsDraw(chart) {
    const { ctx, chartArea, scales } = chart;
    const xScale = scales.x;
    const step = xScale.getPixelForValue(1) - xScale.getPixelForValue(0);
    const half = step / 2;
    const fill = hexToRgba(t.palette[4], 0.22); // matte red — semantic anchor for a "bad" period

    ctx.save();
    spans.forEach((span) => {
      const left = xScale.getPixelForValue(span.startIdx) - half;
      const right = xScale.getPixelForValue(span.endIdx) + half;

      ctx.fillStyle = fill;
      ctx.fillRect(left, chartArea.top, right - left, chartArea.bottom - chartArea.top);

      ctx.fillStyle = t.inkSoft;
      ctx.font = "600 13px sans-serif";
      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.save();
      ctx.translate(left + 10, chartArea.top + 12);
      ctx.rotate(Math.PI / 2);
      ctx.fillText(span.label, 0, 0);
      ctx.restore();
    });
    ctx.restore();
  },
};

// --- Chart -----------------------------------------------------------------
const title = "Equity Index · span-basic · javascript · chartjs · anyplot.ai";
const titleFontSize = Math.round(22 * (title.length > 67 ? 67 / title.length : 1));

new Chart(canvas, {
  type: "line",
  plugins: [spanHighlight],
  data: {
    labels,
    datasets: [
      {
        label: "Equity Index",
        data: indexValues,
        borderColor: t.palette[0],
        backgroundColor: "transparent",
        borderWidth: 3,
        pointRadius: 0,
        tension: 0.15,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 8 } },
    plugins: {
      title: {
        display: true,
        text: title,
        color: t.ink,
        font: { size: titleFontSize },
        padding: { top: 12, bottom: 16 },
      },
      legend: { display: false },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 14 }, maxTicksLimit: 12, autoSkip: true },
        grid: { display: false },
        title: { display: true, text: "Date", color: t.ink, font: { size: 18 } },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: { display: true, text: "Index Value (Jan 2006 = 100)", color: t.ink, font: { size: 18 } },
      },
    },
  },
});
