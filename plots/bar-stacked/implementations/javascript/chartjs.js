// anyplot.ai
// bar-stacked: Stacked Bar Chart
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Monthly energy consumption by source (GWh) — renewables rising, gas falling.
const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"];
const solar = [18, 22, 30, 38, 45, 50];
const wind = [35, 32, 28, 25, 20, 18];
const hydro = [40, 38, 36, 34, 32, 30];
const naturalGas = [52, 48, 44, 38, 30, 22];
const totals = months.map(
  (_, i) => solar[i] + wind[i] + hydro[i] + naturalGas[i]
);

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Total-above-stack labels (own plugin, no external dependency) ----------
const totalLabelsPlugin = {
  id: "totalLabels",
  afterDatasetsDraw(chart) {
    const {
      ctx,
      data,
      scales: { x: xScale, y: yScale },
    } = chart;
    ctx.save();
    ctx.fillStyle = t.ink;
    ctx.font = "600 15px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "bottom";
    data.labels.forEach((_, i) => {
      const total = data.datasets.reduce((sum, ds) => sum + ds.data[i], 0);
      const xPixel = xScale.getPixelForValue(i);
      const yPixel = yScale.getPixelForValue(total);
      ctx.fillText(`${total} GWh`, xPixel, yPixel - 8);
    });
    ctx.restore();
  },
};

// --- Chart --------------------------------------------------------------------
new Chart(canvas, {
  type: "bar",
  data: {
    labels: months,
    datasets: [
      {
        label: "Solar",
        data: solar,
        backgroundColor: t.palette[0],
        stack: "energy",
        borderColor: t.pageBg,
        borderWidth: 1,
      },
      {
        label: "Wind",
        data: wind,
        backgroundColor: t.palette[1],
        stack: "energy",
        borderColor: t.pageBg,
        borderWidth: 1,
      },
      {
        label: "Hydro",
        data: hydro,
        backgroundColor: t.palette[2],
        stack: "energy",
        borderColor: t.pageBg,
        borderWidth: 1,
      },
      {
        label: "Natural Gas",
        data: naturalGas,
        backgroundColor: t.palette[3],
        stack: "energy",
        borderColor: t.pageBg,
        borderWidth: 1,
      },
    ],
  },
  plugins: [totalLabelsPlugin],
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 30 } },
    plugins: {
      title: {
        display: true,
        text: "bar-stacked · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: {
        position: "top",
        labels: { color: t.ink, font: { size: 16 } },
      },
    },
    scales: {
      x: {
        stacked: true,
        categoryPercentage: 0.8,
        barPercentage: 0.6,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { display: false },
        title: {
          display: true,
          text: "Month",
          color: t.ink,
          font: { size: 16 },
        },
      },
      y: {
        stacked: true,
        beginAtZero: true,
        suggestedMax: Math.max(...totals) * 1.15,
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
        title: {
          display: true,
          text: "Energy Consumption (GWh)",
          color: t.ink,
          font: { size: 16 },
        },
      },
    },
  },
});
