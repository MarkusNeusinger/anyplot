// anyplot.ai
// scatter-connected-temporal: Connected Scatter Plot with Temporal Path
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-06-09

const t = window.ANYPLOT_TOKENS;

// CO₂ concentration (ppm) vs global temperature anomaly (°C), biennial 1970–2020
const climateData = [
  { year: 1970, co2: 325.7, temp: 0.03 },
  { year: 1972, co2: 327.5, temp: 0.04 },
  { year: 1974, co2: 330.1, temp: -0.07 },
  { year: 1976, co2: 332.1, temp: -0.10 },
  { year: 1978, co2: 335.5, temp: 0.05 },
  { year: 1980, co2: 338.7, temp: 0.26 },
  { year: 1982, co2: 341.1, temp: 0.12 },
  { year: 1984, co2: 344.4, temp: 0.16 },
  { year: 1986, co2: 347.2, temp: 0.17 },
  { year: 1988, co2: 351.3, temp: 0.39 },
  { year: 1990, co2: 354.4, temp: 0.44 },
  { year: 1992, co2: 356.4, temp: 0.22 },
  { year: 1994, co2: 358.9, temp: 0.31 },
  { year: 1996, co2: 362.7, temp: 0.33 },
  { year: 1998, co2: 366.7, temp: 0.61 },
  { year: 2000, co2: 369.5, temp: 0.33 },
  { year: 2002, co2: 373.2, temp: 0.56 },
  { year: 2004, co2: 377.5, temp: 0.48 },
  { year: 2006, co2: 381.9, temp: 0.61 },
  { year: 2008, co2: 385.6, temp: 0.43 },
  { year: 2010, co2: 389.9, temp: 0.72 },
  { year: 2012, co2: 394.0, temp: 0.64 },
  { year: 2014, co2: 397.2, temp: 0.75 },
  { year: 2016, co2: 403.9, temp: 1.01 },
  { year: 2018, co2: 408.5, temp: 0.83 },
  { year: 2020, co2: 414.2, temp: 1.02 },
];

const n = climateData.length;

// Parse hex to [r, g, b]
function hexToRgb(hex) {
  return [
    parseInt(hex.slice(1, 3), 16),
    parseInt(hex.slice(3, 5), 16),
    parseInt(hex.slice(5, 7), 16),
  ];
}

// Temporal gradient: Imprint brand green → Imprint blue (via t.seq)
const [r1, g1, b1] = hexToRgb(t.seq[0]);
const [r2, g2, b2] = hexToRgb(t.seq[1]);

function lerpColor(frac) {
  const r = Math.round(r1 + (r2 - r1) * frac);
  const g = Math.round(g1 + (g2 - g1) * frac);
  const b = Math.round(b1 + (b2 - b1) * frac);
  return `rgb(${r},${g},${b})`;
}

const pointColors = climateData.map((_, i) => lerpColor(i / (n - 1)));
const pointRadius = climateData.map((_, i) => (i === 0 || i === n - 1 ? 11 : 6));
const lineColor = `rgba(${r1},${g1},${b1},0.45)`;

const labelYears = new Set([1970, 1980, 1990, 2000, 2010, 2020]);

// Fill canvas background before chart renders
Chart.register({
  id: "canvasBg",
  beforeDraw(chart) {
    const ctx = chart.ctx;
    ctx.save();
    ctx.fillStyle = t.pageBg;
    ctx.fillRect(0, 0, chart.width, chart.height);
    ctx.restore();
  },
});

// Draw year labels above annotated key points
Chart.register({
  id: "temporalLabels",
  afterDatasetsDraw(chart) {
    const ctx = chart.ctx;
    const meta = chart.getDatasetMeta(0);
    ctx.save();
    ctx.font = "bold 14px system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "bottom";
    ctx.fillStyle = t.inkSoft;
    climateData.forEach((d, i) => {
      if (!labelYears.has(d.year)) return;
      const pt = meta.data[i];
      if (!pt) return;
      ctx.fillText(String(d.year), pt.x, pt.y - 14);
    });
    ctx.restore();
  },
});

// Mount
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// Chart
new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      {
        label: "CO₂ vs Temperature",
        data: climateData.map(d => ({ x: d.co2, y: d.temp })),
        showLine: true,
        borderColor: lineColor,
        borderWidth: 2,
        pointBackgroundColor: pointColors,
        pointBorderColor: t.pageBg,
        pointBorderWidth: 1.5,
        pointRadius,
        pointHoverRadius: pointRadius.map(r => r + 2),
        tension: 0,
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
        text: "scatter-connected-temporal · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22, weight: "600" },
        padding: { top: 20, bottom: 8 },
      },
      subtitle: {
        display: true,
        text: "Color encodes time: 1970 (green) → 2020 (blue)",
        color: t.inkSoft,
        font: { size: 14 },
        padding: { bottom: 16 },
      },
      legend: { display: false },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: "CO₂ Concentration (ppm)",
          color: t.ink,
          font: { size: 16 },
        },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
      },
      y: {
        title: {
          display: true,
          text: "Temperature Anomaly (°C)",
          color: t.ink,
          font: { size: 16 },
        },
        ticks: { color: t.inkSoft, font: { size: 14 } },
        grid: { color: t.grid },
      },
    },
    layout: {
      padding: { top: 10, right: 50, bottom: 20, left: 20 },
    },
  },
});
