// anyplot.ai
// pyramid-basic: Basic Pyramid Chart
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 85/100 | Created: 2026-09-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
const ageGroups = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"];
const malePopulation = [42, 45, 40, 38, 41, 35, 28, 15, 6];
const femalePopulation = [40, 43, 39, 39, 42, 37, 31, 19, 9];
const axisMax = 50;

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -------------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels: ageGroups,
    datasets: [
      {
        label: "Male",
        data: malePopulation.map((v) => -v),
        backgroundColor: t.palette[0],
        borderWidth: 0,
      },
      {
        label: "Female",
        data: femalePopulation,
        backgroundColor: t.palette[1],
        borderWidth: 0,
      },
    ],
  },
  options: {
    indexAxis: "y",
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "pyramid-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        position: "top",
        labels: { color: t.ink, font: { size: 16 } },
      },
      tooltip: {
        callbacks: {
          label: (ctx) => `${ctx.dataset.label}: ${Math.abs(ctx.parsed.x)}k`,
        },
      },
    },
    scales: {
      x: {
        stacked: true,
        min: -axisMax,
        max: axisMax,
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          stepSize: 10,
          callback: (value) => Math.abs(value),
        },
        grid: { color: t.grid },
        title: { display: true, text: "Population (thousands)", color: t.ink, font: { size: 18 } },
      },
      y: {
        stacked: true,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        title: { display: true, text: "Age Group", color: t.ink, font: { size: 18 } },
      },
    },
  },
});
