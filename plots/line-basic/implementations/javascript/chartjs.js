// anyplot.ai
// line-basic: Basic Line Plot
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-02

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// Deterministic LCG so the monthly noise is reproducible across renders (seed = 42)
let seed = 42;
const rand = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 0x100000000; };

// Data: Berlin monthly mean temperature, Jan 2024 - Dec 2025 (two full seasonal cycles)
const monthLabels = [
  "Jan '24", "Feb '24", "Mar '24", "Apr '24", "May '24", "Jun '24",
  "Jul '24", "Aug '24", "Sep '24", "Oct '24", "Nov '24", "Dec '24",
  "Jan '25", "Feb '25", "Mar '25", "Apr '25", "May '25", "Jun '25",
  "Jul '25", "Aug '25", "Sep '25", "Oct '25", "Nov '25", "Dec '25",
];
const temperatures = monthLabels.map((_, i) => {
  const seasonal = 10 + 12 * Math.cos((2 * Math.PI * (i - 6)) / 12);
  const noise = (rand() - 0.5) * 1.6;
  return +(seasonal + noise).toFixed(1);
});

// Mount canvas into the harness container
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

new Chart(canvas, {
  type: "line",
  data: {
    labels: monthLabels,
    datasets: [{
      label: "Mean temperature",
      data: temperatures,
      borderColor: t.palette[0],
      backgroundColor: t.palette[0],
      borderWidth: 3.5,
      pointRadius: 5,
      pointHoverRadius: 7,
      pointBackgroundColor: t.palette[0],
      pointBorderColor: t.pageBg,
      pointBorderWidth: 1.5,
      tension: 0,
      fill: false,
    }],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { top: 16, right: 48, bottom: 8, left: 8 } },
    plugins: {
      title: {
        display: true,
        text: "line-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 32, weight: "normal" },
        padding: { top: 8, bottom: 28 },
      },
      legend: { display: false },
    },
    scales: {
      x: {
        ticks: {
          color: t.inkSoft,
          font: { size: 18 },
          maxRotation: 0,
          autoSkip: true,
          autoSkipPadding: 24,
        },
        grid: { display: false },
        border: { color: t.inkSoft },
        title: {
          display: true,
          text: "Month",
          color: t.ink,
          font: { size: 22 },
          padding: { top: 12 },
        },
      },
      y: {
        ticks: {
          color: t.inkSoft,
          font: { size: 18 },
          callback: (v) => `${v}°C`,
        },
        grid: { color: t.grid },
        border: { color: t.inkSoft },
        title: {
          display: true,
          text: "Berlin mean temperature",
          color: t.ink,
          font: { size: 22 },
          padding: { bottom: 12 },
        },
      },
    },
  },
});
