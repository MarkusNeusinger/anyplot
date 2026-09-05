// anyplot.ai
// line-styled: Styled Line Plot
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 82/100 | Created: 2026-09-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ---------------------------------------
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(42);

const minutes = Array.from({ length: 60 }, (_, i) => i);

function coreTemperature(baseline, rampRate, plateau, noiseScale) {
  return minutes.map((minute) => {
    const ramp = Math.min(minute * rampRate, plateau - baseline);
    const noise = (rand() - 0.5) * noiseScale;
    return Math.round((baseline + ramp + noise) * 10) / 10;
  });
}

const series = [
  { label: "Core 1", data: coreTemperature(46, 0.75, 82, 1.2), borderDash: [] },
  { label: "Core 2", data: coreTemperature(45, 0.58, 74, 1.0), borderDash: [10, 5] },
  { label: "Core 3", data: coreTemperature(47, 0.44, 66, 1.4), borderDash: [2, 3] },
  { label: "Core 4", data: coreTemperature(44, 0.3, 58, 0.9), borderDash: [10, 5, 2, 5] },
];

// --- Mount -----------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -----------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    labels: minutes,
    datasets: series.map((s, i) => ({
      label: s.label,
      data: s.data,
      borderColor: t.palette[i],
      backgroundColor: t.palette[i],
      borderDash: s.borderDash,
      borderWidth: 3.5,
      pointRadius: 0,
      tension: 0.25,
    })),
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      title: {
        display: true,
        text: "line-styled · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { bottom: 24 },
      },
      legend: {
        position: "top",
        labels: { color: t.ink, font: { size: 16 }, boxWidth: 40 },
      },
    },
    scales: {
      x: {
        title: { display: true, text: "Stress Test Duration (minutes)", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 }, maxTicksLimit: 10 },
        grid: { display: false },
      },
      y: {
        title: { display: true, text: "Core Temperature (°C)", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
      },
    },
  },
});
