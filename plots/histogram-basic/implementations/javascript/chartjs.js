// anyplot.ai
// histogram-basic: Basic Histogram
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-08-26

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
function makeLcg(seed) {
  let state = seed >>> 0;
  return function lcg() {
    state = (1664525 * state + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

function normal(rand, mean, stdDev) {
  let sum = 0;
  for (let i = 0; i < 12; i++) sum += rand();
  return mean + (sum - 6) * stdDev;
}

const rand = makeLcg(42);
const examScores = [];
for (let i = 0; i < 400; i++) {
  // Most students cluster near a strong score; a smaller group struggles,
  // producing the left-skewed tail typical of exam-score distributions.
  const score = rand() < 0.85 ? normal(rand, 78, 9) : normal(rand, 48, 12);
  examScores.push(Math.max(0, Math.min(100, score)));
}

// --- Binning -----------------------------------------------------------------
const binCount = 20;
const minScore = Math.min(...examScores);
const maxScore = Math.max(...examScores);
const binWidth = (maxScore - minScore) / binCount;
const counts = new Array(binCount).fill(0);
examScores.forEach((score) => {
  const idx = Math.min(binCount - 1, Math.floor((score - minScore) / binWidth));
  counts[idx]++;
});
const labels = counts.map((_, i) => Math.round(minScore + i * binWidth));

// --- Mount -----------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -----------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels,
    datasets: [
      {
        label: "Frequency",
        data: counts,
        backgroundColor: t.palette[0],
        borderColor: t.pageBg,
        borderWidth: 1,
        categoryPercentage: 1.0,
        barPercentage: 1.0,
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
        text: "histogram-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: { display: false },
    },
    scales: {
      x: {
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          autoSkip: true,
          maxTicksLimit: 10,
        },
        grid: { display: false },
        title: {
          display: true,
          text: "Exam Score",
          color: t.ink,
          font: { size: 16 },
        },
      },
      y: {
        beginAtZero: true,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Frequency",
          color: t.ink,
          font: { size: 16 },
        },
      },
    },
  },
});
