// anyplot.ai
// bar-diverging: Diverging Bar Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-08-18

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Employee engagement survey: net agreement score (% agree − % disagree) per
// topic, sorted descending so the pattern (strong positives to strong
// negatives) reads at a glance.
const topics = [
  "Career Growth",
  "Work-Life Balance",
  "Team Collaboration",
  "Remote Flexibility",
  "Job Security",
  "Training & Development",
  "Management Support",
  "Compensation",
];
const netScores = [62, 48, 31, 14, -8, -19, -33, -45];

const positiveColor = t.palette[0]; // #009E73 brand green — sentiment: agree
const negativeColor = t.palette[4]; // #AE3030 matte red — sentiment: disagree

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Title (fontsize scaled for length beyond the 67-char baseline) ---------
const title = "Employee Engagement Survey · bar-diverging · javascript · chartjs · anyplot.ai";
const titleFontSize = Math.round(22 * Math.min(1, 67 / title.length));

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels: topics,
    datasets: [
      {
        label: "Net agreement",
        data: netScores,
        backgroundColor: netScores.map((v) => (v >= 0 ? positiveColor : negativeColor)),
        borderWidth: 0,
        borderRadius: 3,
      },
    ],
  },
  options: {
    indexAxis: "y",
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 8, right: 24, bottom: 8, left: 8 } },
    plugins: {
      title: { display: true, text: title, color: t.ink, font: { size: titleFontSize, weight: "500" } },
      legend: { display: false },
    },
    scales: {
      x: {
        min: -70,
        max: 70,
        title: { display: true, text: "Net Agreement Score (%)", color: t.ink, font: { size: 15 } },
        ticks: { color: t.inkSoft, font: { size: 13 } },
        grid: {
          color: (ctx) => (ctx.tick.value === 0 ? t.ink : t.grid),
          lineWidth: (ctx) => (ctx.tick.value === 0 ? 2 : 1),
        },
        border: { display: false },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        border: { display: false },
      },
    },
  },
});
