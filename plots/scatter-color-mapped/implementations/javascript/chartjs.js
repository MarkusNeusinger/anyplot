// anyplot.ai
// scatter-color-mapped: Color-Mapped Scatter Plot
// Library: chartjs 4.4.7 | JavaScript 22.23.2
// Quality: 86/100 | Created: 2026-09-05

//# anyplot-orientation: landscape
const t = window.ANYPLOT_TOKENS;

// --- Data: simulated sensor readings across a monitoring grid ---------------
// Temperature drifts cooler to the north and warmer to the east, plus noise.
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(42);

const n = 180;
const readings = [];
for (let i = 0; i < n; i++) {
  const distanceEast = rand() * 100;
  const distanceNorth = rand() * 100;
  const temperature =
    24 - 0.09 * distanceNorth + 0.03 * distanceEast + (rand() - 0.5) * 4;
  readings.push({ x: distanceEast, y: distanceNorth, temperature });
}

const temperatures = readings.map((r) => r.temperature);
const tempMin = Math.min(...temperatures);
const tempMax = Math.max(...temperatures);

// --- Color mapping: imprint_seq (brand green -> blue), single-polarity data
function hexToRgb(hex) {
  const value = parseInt(hex.slice(1), 16);
  return [(value >> 16) & 255, (value >> 8) & 255, value & 255];
}
const seqLow = hexToRgb(t.seq[0]);
const seqHigh = hexToRgb(t.seq[1]);

function colorForTemperature(value) {
  const ratio = (value - tempMin) / (tempMax - tempMin);
  const r = Math.round(seqLow[0] + ratio * (seqHigh[0] - seqLow[0]));
  const g = Math.round(seqLow[1] + ratio * (seqHigh[1] - seqLow[1]));
  const b = Math.round(seqLow[2] + ratio * (seqHigh[2] - seqLow[2]));
  return `rgba(${r}, ${g}, ${b}, 0.85)`;
}

const pointColors = readings.map((r) => colorForTemperature(r.temperature));

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Colorbar plugin: draws the imprint_seq gradient as a reference scale ---
const colorbarPlugin = {
  id: "colorbar",
  afterDraw(chart) {
    const { ctx, chartArea } = chart;
    const { top, bottom, right } = chartArea;
    const barX = right + 24;
    const barWidth = 26;

    const gradient = ctx.createLinearGradient(0, bottom, 0, top);
    gradient.addColorStop(0, t.seq[0]);
    gradient.addColorStop(1, t.seq[1]);

    ctx.save();
    ctx.fillStyle = gradient;
    ctx.fillRect(barX, top, barWidth, bottom - top);
    ctx.strokeStyle = t.inkSoft;
    ctx.lineWidth = 1;
    ctx.strokeRect(barX, top, barWidth, bottom - top);

    ctx.fillStyle = t.ink;
    ctx.font = "14px sans-serif";
    ctx.textBaseline = "middle";
    ctx.textAlign = "left";
    ctx.fillText(`${tempMax.toFixed(1)}°C`, barX + barWidth + 8, top);
    ctx.fillText(`${tempMin.toFixed(1)}°C`, barX + barWidth + 8, bottom);

    ctx.translate(barX + barWidth + 68, (top + bottom) / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = "center";
    ctx.fillText("Temperature (°C)", 0, 0);
    ctx.restore();
  },
};

// --- Chart -------------------------------------------------------------------
new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      {
        label: "Sensor reading",
        data: readings,
        backgroundColor: pointColors,
        borderColor: t.pageBg,
        borderWidth: 1,
        pointRadius: 9,
        pointHoverRadius: 9,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: { right: 150 } },
    plugins: {
      title: {
        display: true,
        text: "scatter-color-mapped · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
      },
      legend: { display: false },
    },
    scales: {
      x: {
        title: { display: true, text: "Distance East (km)", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
      },
      y: {
        title: { display: true, text: "Distance North (km)", color: t.ink, font: { size: 16 } },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
      },
    },
  },
  plugins: [colorbarPlugin],
});
