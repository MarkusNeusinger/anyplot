// anyplot.ai
// audiogram-clinical: Clinical Audiogram
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-15
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data -------------------------------------------------------------------
// Pure-tone audiometry: high-frequency sensorineural notch (occupational noise)
const frequencies = [125, 250, 500, 1000, 2000, 4000, 8000];
const rightEarThresholds = [15, 20, 25, 30, 50, 75, 80];
const leftEarThresholds  = [10, 15, 20, 25, 40, 65, 70];

// Semantic color exception: red/blue are universal audiogram conventions
const RIGHT_COLOR = "#AE3030"; // matte red — right-ear clinical convention
const LEFT_COLOR  = "#4467A3"; // Imprint blue — left-ear clinical convention

// Severity bands per WHO audiometric classification
const severityBands = [
  { min: -10, max: 25,  fill: "rgba(0,158,115,0.07)",   label: "Normal"      },
  { min: 25,  max: 40,  fill: "rgba(221,204,119,0.13)", label: "Mild"        },
  { min: 40,  max: 55,  fill: "rgba(189,130,51,0.13)",  label: "Moderate"    },
  { min: 55,  max: 70,  fill: "rgba(189,130,51,0.21)",  label: "Mod. Severe" },
  { min: 70,  max: 90,  fill: "rgba(174,48,48,0.13)",   label: "Severe"      },
  { min: 90,  max: 120, fill: "rgba(174,48,48,0.22)",   label: "Profound"    },
];

// --- Plugin: severity band fills (behind grid) and labels (in right margin) -
const severityPlugin = {
  id: "severityPlugin",
  beforeDraw(chart) {
    const { ctx, chartArea, scales } = chart;
    if (!chartArea || !scales.y) return;
    const yScale = scales.y;
    ctx.save();
    ctx.beginPath();
    ctx.rect(chartArea.left, chartArea.top, chartArea.width, chartArea.height);
    ctx.clip();
    severityBands.forEach(({ min, max, fill }) => {
      const y1     = yScale.getPixelForValue(min);
      const y2     = yScale.getPixelForValue(max);
      const top    = Math.min(y1, y2);
      const height = Math.abs(y2 - y1);
      ctx.fillStyle = fill;
      ctx.fillRect(chartArea.left, top, chartArea.width, height);
    });
    ctx.restore();
  },
  afterDatasetsDraw(chart) {
    const { ctx, chartArea, scales } = chart;
    if (!chartArea || !scales.y) return;
    const yScale = scales.y;
    ctx.save();
    ctx.font = "13px system-ui, sans-serif";
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillStyle = t.inkSoft;
    severityBands.forEach(({ min, max, label }) => {
      const y1   = yScale.getPixelForValue(min);
      const y2   = yScale.getPixelForValue(max);
      const midY = (y1 + y2) / 2;
      ctx.fillText(label, chartArea.right + 10, midY);
    });
    ctx.restore();
  },
};

// --- Mount ------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ------------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  plugins: [severityPlugin],
  data: {
    datasets: [
      {
        label: "Right Ear (O)",
        data: rightEarThresholds.map((y, i) => ({ x: frequencies[i], y })),
        borderColor: RIGHT_COLOR,
        backgroundColor: RIGHT_COLOR,
        pointStyle: "circle",
        pointRadius: 9,
        pointHoverRadius: 11,
        pointBorderColor: RIGHT_COLOR,
        pointBorderWidth: 2.5,
        pointBackgroundColor: t.pageBg,
        borderWidth: 2.5,
        tension: 0,
      },
      {
        label: "Left Ear (X)",
        data: leftEarThresholds.map((y, i) => ({ x: frequencies[i], y })),
        borderColor: LEFT_COLOR,
        backgroundColor: LEFT_COLOR,
        pointStyle: "crossRot",
        pointRadius: 10,
        pointHoverRadius: 12,
        pointBorderColor: LEFT_COLOR,
        pointBorderWidth: 3,
        pointBackgroundColor: LEFT_COLOR,
        borderWidth: 2.5,
        borderDash: [7, 4],
        tension: 0,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: {
      padding: { top: 16, right: 120, bottom: 24, left: 10 },
    },
    plugins: {
      title: {
        display: true,
        text: "audiogram-clinical · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "500" },
        padding: { top: 8, bottom: 14 },
      },
      legend: {
        display: true,
        position: "top",
        labels: {
          color: t.ink,
          font: { size: 16 },
          usePointStyle: true,
          pointStyleWidth: 16,
          padding: 24,
        },
      },
    },
    scales: {
      x: {
        type: "logarithmic",
        min: 100,
        max: 10000,
        title: {
          display: true,
          text: "Frequency (Hz)",
          color: t.ink,
          font: { size: 16, weight: "500" },
          padding: { top: 10 },
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          callback(value) {
            const map = { 125: "125", 250: "250", 500: "500", 1000: "1k", 2000: "2k", 4000: "4k", 8000: "8k" };
            return map[value] !== undefined ? map[value] : null;
          },
        },
        afterBuildTicks(scale) {
          scale.ticks = [125, 250, 500, 1000, 2000, 4000, 8000].map(v => ({ value: v }));
        },
        grid: {
          color: t.grid,
        },
      },
      y: {
        reverse: true,
        min: -10,
        max: 120,
        title: {
          display: true,
          text: "Hearing Level (dB HL)",
          color: t.ink,
          font: { size: 16, weight: "500" },
          padding: { bottom: 10 },
        },
        ticks: {
          color: t.inkSoft,
          font: { size: 14 },
          stepSize: 10,
        },
        grid: {
          color: t.grid,
        },
      },
    },
  },
});
