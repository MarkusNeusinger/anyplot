// anyplot.ai
// heatmap-calendar: Basic Calendar Heatmap
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-07-23

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;
// Semantic "muted" anchor (other/rest/no-activity) — theme-adaptive, not part
// of window.ANYPLOT_TOKENS, so it's derived here per prompts/default-style-guide.md.
const MUTED = t.theme === "dark" ? "#A8A79F" : "#6B6A63";

// --- Data (in-memory, deterministic) ----------------------------------------
// Daily coding-commit counts across a full year, GitHub-contribution-graph style.
let seed = 42;
function nextRandom() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}

const YEAR = 2023;
const startDate = new Date(Date.UTC(YEAR, 0, 1));
const startWeekday = (startDate.getUTCDay() + 6) % 7; // Monday = 0 ... Sunday = 6
const weekdayLabels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const monthLabels = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];
const weekdayBaseline = [4, 5, 6, 6, 5, 2, 1]; // Mon..Sun commit baseline

const days = [];
for (let i = 0; i < 365; i++) {
  const date = new Date(startDate.getTime() + i * 86400000);
  const weekday = (date.getUTCDay() + 6) % 7;
  const week = Math.floor((i + startWeekday) / 7);
  let value = Math.round(weekdayBaseline[weekday] + (nextRandom() - 0.5) * 6);
  if (i % 47 === 3) value += 14; // occasional hackathon burst
  value = Math.max(0, value);
  days.push({ date, week, weekday, value });
}
const weekCount = days[days.length - 1].week + 1;

// --- Month tick positions (first week each month first appears) ------------
const monthTicks = [];
const seenMonths = new Set();
for (const day of days) {
  const monthKey = day.date.getUTCMonth();
  if (!seenMonths.has(monthKey)) {
    seenMonths.add(monthKey);
    monthTicks.push({ week: day.week, label: monthLabels[monthKey] });
  }
}
const monthLabelAt = Object.fromEntries(monthTicks.map((m) => [m.week, m.label]));

// --- Sequential color mapping (Imprint imprint_seq: brand green -> blue) ---
function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
function rgbToHex([r, g, b]) {
  return (
    "#" +
    [r, g, b].map((v) => Math.round(v).toString(16).padStart(2, "0")).join("")
  );
}
const [seqR1, seqG1, seqB1] = hexToRgb(t.seq[0]);
const [seqR2, seqG2, seqB2] = hexToRgb(t.seq[1]);
function seqColor(frac) {
  return rgbToHex([
    seqR1 + (seqR2 - seqR1) * frac,
    seqG1 + (seqG2 - seqG1) * frac,
    seqB1 + (seqB2 - seqB1) * frac,
  ]);
}

const maxValue = Math.max(...days.map((d) => d.value));
function colorForValue(value) {
  if (value === 0) return MUTED;
  return seqColor(Math.min(1, Math.sqrt(value / maxValue)));
}

// --- Legend bins (data-driven, matches the sequential scale) ---------------
const nonZeroSorted = days
  .map((d) => d.value)
  .filter((v) => v > 0)
  .sort((a, b) => a - b);
const quantile = (p) => nonZeroSorted[Math.floor(p * (nonZeroSorted.length - 1))];
const q1 = quantile(0.33);
const q2 = quantile(0.66);
const legendBins = [
  { label: "No activity", color: MUTED },
  { label: `1–${q1}`, color: colorForValue(Math.max(1, Math.round(q1 / 2))) },
  { label: `${q1 + 1}–${q2}`, color: colorForValue(Math.round((q1 + q2) / 2)) },
  { label: `${q2 + 1}+`, color: colorForValue(maxValue) },
];

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
const dateFormatter = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  year: "numeric",
  timeZone: "UTC",
});

new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      {
        label: "Commits",
        data: days.map((d) => ({ x: d.week, y: d.weekday, v: d.value, date: d.date })),
        showLine: false,
        pointStyle: "rect",
        pointBackgroundColor: (ctx) => colorForValue(ctx.raw.v),
        pointBorderColor: t.pageBg,
        pointBorderWidth: 1,
        pointRadius: (ctx) => {
          const scale = ctx.chart.scales;
          if (!scale.x || !scale.y) return 8;
          const pxPerWeek = Math.abs(scale.x.getPixelForValue(1) - scale.x.getPixelForValue(0));
          const pxPerDay = Math.abs(scale.y.getPixelForValue(1) - scale.y.getPixelForValue(0));
          return Math.max(3, Math.min(pxPerWeek, pxPerDay) / 2 - 1);
        },
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 4, right: 20, bottom: 4, left: 4 } },
    plugins: {
      title: {
        display: true,
        text: "heatmap-calendar · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 18 },
      },
      legend: {
        display: true,
        position: "bottom",
        onClick: () => {},
        labels: {
          color: t.inkSoft,
          font: { size: 14 },
          boxWidth: 18,
          boxHeight: 18,
          generateLabels: () =>
            legendBins.map((bin) => ({
              text: bin.label,
              fillStyle: bin.color,
              strokeStyle: bin.color,
              lineWidth: 0,
            })),
        },
      },
      tooltip: {
        callbacks: {
          title: () => "",
          label: (ctx) => `${dateFormatter.format(ctx.raw.date)}: ${ctx.raw.v} commits`,
        },
      },
    },
    scales: {
      x: {
        type: "linear",
        position: "top",
        min: -0.6,
        max: weekCount - 0.4,
        afterBuildTicks: (axis) => {
          axis.ticks = monthTicks.map((m) => ({ value: m.week }));
        },
        ticks: {
          callback: (value) => monthLabelAt[value] ?? "",
          color: t.inkSoft,
          font: { size: 14 },
        },
        grid: { display: false },
        border: { display: false },
      },
      y: {
        type: "linear",
        reverse: true,
        min: -0.6,
        max: 6.6,
        afterBuildTicks: (axis) => {
          axis.ticks = weekdayLabels.map((_, i) => ({ value: i }));
        },
        ticks: {
          callback: (value) => weekdayLabels[value] ?? "",
          color: t.inkSoft,
          font: { size: 14 },
        },
        grid: { display: false },
        border: { display: false },
      },
    },
  },
});
