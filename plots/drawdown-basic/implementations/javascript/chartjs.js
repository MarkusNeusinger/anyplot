// anyplot.ai
// drawdown-basic: Drawdown Chart
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-08-24

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic fixed-seed LCG) -------------------------
let seed = 42;
function nextUniform() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
function nextGaussian() {
  const u1 = Math.max(nextUniform(), 1e-9);
  const u2 = nextUniform();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

const TRADING_DAYS = 504; // ~2 years of daily data
const DRIFT = 0.00035; // ~9%/yr annualized
const VOLATILITY = 0.011; // ~17.5%/yr annualized

const dates = [];
const cursor = new Date(2024, 0, 2);
while (dates.length < TRADING_DAYS) {
  const weekday = cursor.getDay();
  if (weekday !== 0 && weekday !== 6) dates.push(new Date(cursor));
  cursor.setDate(cursor.getDate() + 1);
}

const portfolioValue = [100];
for (let i = 1; i < TRADING_DAYS; i++) {
  const dailyReturn = DRIFT + VOLATILITY * nextGaussian();
  portfolioValue.push(portfolioValue[i - 1] * (1 + dailyReturn));
}

const runningMax = [];
const drawdown = [];
let peak = portfolioValue[0];
for (let i = 0; i < TRADING_DAYS; i++) {
  peak = Math.max(peak, portfolioValue[i]);
  runningMax.push(peak);
  drawdown.push(((portfolioValue[i] - peak) / peak) * 100);
}

let troughIndex = 0;
for (let i = 1; i < TRADING_DAYS; i++) {
  if (drawdown[i] < drawdown[troughIndex]) troughIndex = i;
}
let peakIndex = troughIndex;
while (peakIndex > 0 && drawdown[peakIndex] < -1e-9) peakIndex--;
let recoveryIndex = -1;
for (let i = troughIndex + 1; i < TRADING_DAYS; i++) {
  if (drawdown[i] >= -1e-9) {
    recoveryIndex = i;
    break;
  }
}

const durationDays = troughIndex - peakIndex;
const recoveryText =
  recoveryIndex === -1
    ? "not yet recovered"
    : `recovered in ${recoveryIndex - troughIndex} trading days`;
const subtitleText = `Max drawdown ${drawdown[troughIndex].toFixed(1)}% · ${durationDays} trading days to trough · ${recoveryText}`;

const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const labels = dates.map((d) => `${monthNames[d.getMonth()]} ${d.getFullYear()}`);

const maxDrawdownPoint = drawdown.map((v, i) => (i === troughIndex ? v : null));
const recoveryPoint = drawdown.map((v, i) => (i === recoveryIndex ? v : null));

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    labels,
    datasets: [
      {
        label: "Portfolio Value",
        data: portfolioValue,
        borderColor: t.inkSoft,
        backgroundColor: "transparent",
        borderWidth: 1.5,
        pointRadius: 0,
        tension: 0,
        fill: false,
        yAxisID: "y1",
        order: 0,
      },
      {
        label: "Drawdown",
        data: drawdown,
        borderColor: t.palette[4],
        backgroundColor: `${t.palette[4]}33`,
        borderWidth: 2.5,
        pointRadius: 0,
        tension: 0,
        fill: "origin",
        yAxisID: "y",
        order: 1,
      },
      {
        label: "Max Drawdown",
        data: maxDrawdownPoint,
        borderColor: "transparent",
        backgroundColor: t.amber,
        pointRadius: 8,
        pointBorderColor: t.ink,
        pointBorderWidth: 1.5,
        pointStyle: "rectRot",
        showLine: false,
        yAxisID: "y",
        order: 2,
      },
      {
        label: "Recovery",
        data: recoveryPoint,
        borderColor: "transparent",
        backgroundColor: t.palette[0],
        pointRadius: 8,
        pointBorderColor: t.ink,
        pointBorderWidth: 1.5,
        pointStyle: "circle",
        showLine: false,
        yAxisID: "y",
        order: 2,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    interaction: { mode: "nearest", intersect: false },
    plugins: {
      title: {
        display: true,
        text: "drawdown-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 6 },
      },
      subtitle: {
        display: true,
        text: subtitleText,
        color: t.inkSoft,
        font: { size: 15 },
        padding: { bottom: 16 },
      },
      legend: {
        labels: { color: t.ink, font: { size: 14 }, usePointStyle: true, boxWidth: 10 },
      },
    },
    scales: {
      x: {
        ticks: { color: t.inkSoft, font: { size: 13 }, maxTicksLimit: 10, autoSkip: true },
        grid: { display: false },
        title: { display: true, text: "Date", color: t.ink, font: { size: 15 } },
      },
      y: {
        position: "left",
        max: 0,
        ticks: {
          color: t.inkSoft,
          font: { size: 13 },
          callback: (value) => `${value}%`,
        },
        grid: { color: t.grid },
        title: { display: true, text: "Drawdown (%)", color: t.ink, font: { size: 15 } },
      },
      y1: {
        position: "right",
        ticks: { color: t.inkSoft, font: { size: 13 } },
        grid: { display: false },
        title: { display: true, text: "Portfolio Value", color: t.ink, font: { size: 15 } },
      },
    },
  },
});
