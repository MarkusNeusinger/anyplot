// anyplot.ai
// forest-basic: Meta-Analysis Forest Plot
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-09-05

const t = window.ANYPLOT_TOKENS;
const MUTED = window.ANYPLOT_THEME === "dark" ? "#A8A79F" : "#6B6A63";

// --- Data (in-memory, deterministic) ----------------------------------------
// Meta-analysis of 11 randomized controlled trials comparing a new therapy
// against placebo on treatment response (odds ratio > 1 favors the therapy).
const studies = [
  { study: "Anderson 2014", effect: 1.35, ciLower: 0.82, ciUpper: 2.22, weight: 5.4 },
  { study: "Bianchi 2015", effect: 1.62, ciLower: 1.05, ciUpper: 2.5, weight: 6.8 },
  { study: "Castillo 2016", effect: 0.95, ciLower: 0.58, ciUpper: 1.56, weight: 5.1 },
  { study: "Dubois 2017", effect: 1.88, ciLower: 1.2, ciUpper: 2.94, weight: 7.2 },
  { study: "Eriksson 2018", effect: 1.41, ciLower: 1.02, ciUpper: 1.95, weight: 11.5 },
  { study: "Fujimoto 2018", effect: 2.05, ciLower: 1.18, ciUpper: 3.56, weight: 4.6 },
  { study: "Gupta 2019", effect: 1.22, ciLower: 0.88, ciUpper: 1.69, weight: 10.3 },
  { study: "Haddad 2020", effect: 1.55, ciLower: 1.15, ciUpper: 2.09, weight: 12.7 },
  { study: "Ivanov 2021", effect: 1.1, ciLower: 0.71, ciUpper: 1.7, weight: 6.9 },
  { study: "Jensen 2022", effect: 1.78, ciLower: 1.28, ciUpper: 2.48, weight: 9.8 },
  { study: "Kowalski 2023", effect: 1.48, ciLower: 1.18, ciUpper: 1.86, weight: 19.7 },
];
const pooled = { study: "Pooled Effect", effect: 1.45, ciLower: 1.28, ciUpper: 1.65 };
const nullEffect = 1;

const labels = [...studies.map((s) => s.study), pooled.study];

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart --------------------------------------------------------------------
const title = "forest-basic · javascript · chartjs · anyplot.ai";

new Chart(canvas, {
  type: "bar",
  data: {
    labels,
    datasets: [
      {
        label: "Null effect (OR = 1)",
        type: "line",
        data: labels.map((label) => ({ x: nullEffect, y: label })),
        borderColor: MUTED,
        borderDash: [8, 5],
        borderWidth: 2,
        pointRadius: 0,
        fill: false,
        tension: 0,
      },
      {
        label: "95% confidence interval",
        data: [...studies.map((s) => [s.ciLower, s.ciUpper]), [pooled.ciLower, pooled.ciUpper]],
        backgroundColor: MUTED,
        barThickness: 4,
        borderSkipped: false,
      },
      {
        label: "Study OR (marker size ∝ weight)",
        type: "scatter",
        data: studies.map((s) => ({ x: s.effect, y: s.study })),
        pointStyle: "rect",
        pointRadius: studies.map((s) => 5 + s.weight * 0.75),
        pointHoverRadius: studies.map((s) => 5 + s.weight * 0.75),
        backgroundColor: t.palette[0],
        borderWidth: 0,
      },
      {
        label: "Pooled OR",
        type: "scatter",
        data: [{ x: pooled.effect, y: pooled.study }],
        pointStyle: "rectRot",
        pointRadius: 20,
        pointHoverRadius: 20,
        backgroundColor: t.ink,
        borderWidth: 0,
      },
    ],
  },
  options: {
    indexAxis: "y",
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 10, right: 40, bottom: 10, left: 10 } },
    plugins: {
      title: { display: true, text: title, color: t.ink, font: { size: 22 } },
      subtitle: {
        display: true,
        text: "Drug A vs. placebo · square markers sized by study weight · diamond = pooled estimate",
        color: t.inkSoft,
        font: { size: 14, style: "italic" },
        padding: { bottom: 12 },
      },
      legend: {
        position: "bottom",
        labels: { color: t.ink, font: { size: 14 }, boxHeight: 10, boxWidth: 10 },
      },
    },
    scales: {
      x: {
        type: "logarithmic",
        min: 0.4,
        max: 4,
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback: (value) => {
            const allowed = [0.4, 0.5, 1, 2, 4];
            const rounded = Math.round(value * 100) / 100;
            return allowed.includes(rounded) ? rounded : null;
          },
        },
        grid: { color: t.grid },
        title: { display: true, text: "Odds Ratio (log scale)", color: t.ink, font: { size: 16 } },
      },
      y: {
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
      },
    },
  },
});
