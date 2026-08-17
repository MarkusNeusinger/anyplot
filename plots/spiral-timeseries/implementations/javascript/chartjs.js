// anyplot.ai
// spiral-timeseries: Spiral Time Series Chart
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-08-17
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data: daily average temperature over 5 years, one revolution = one year ---
const CYCLE_LENGTH_DAYS = 365;
const CYCLES = 5;
const DAY_STRIDE = 2;
const R_INNER = 0.6;
const R_GROWTH = 0.8; // radius added per full revolution
const MAX_R = R_INNER + R_GROWTH * CYCLES;
const SCALE_MAX = MAX_R + 0.8; // margin for spokes and month labels
const LEGEND_MARGIN = 1.6; // dedicated right-hand gutter for the color legend

const MONTH_NAMES = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

// Tiny fixed-seed LCG so the noise is deterministic across renders.
let lcgState = 42;
function nextRandom() {
  lcgState = (lcgState * 1664525 + 1013904223) % 4294967296;
  return lcgState / 4294967296;
}

const points = [];
for (let cycle = 0; cycle < CYCLES; cycle++) {
  for (let day = 0; day < CYCLE_LENGTH_DAYS; day += DAY_STRIDE) {
    const dayFraction = day / CYCLE_LENGTH_DAYS;
    const totalTurns = cycle + dayFraction;
    const angle = totalTurns * 2 * Math.PI;
    const r = R_INNER + R_GROWTH * totalTurns;
    // angle=0 (cycle start) sits at the top; time advances clockwise.
    const x = r * Math.sin(angle);
    const y = r * Math.cos(angle);

    const seasonal =
      14 + 11 * Math.sin((2 * Math.PI * (day - 80)) / CYCLE_LENGTH_DAYS);
    const warmingTrend = cycle * 0.5;
    const noise = (nextRandom() - 0.5) * 3;
    const value = seasonal + warmingTrend + noise;
    const month = MONTH_NAMES[Math.min(11, Math.floor(day / 30.44))];

    points.push({ x, y, value, cycle, month });
  }
}
// One marker per revolution, at the cycle's starting point (top of the spiral).
const cycleMarkers = [];
for (let cycle = 0; cycle < CYCLES; cycle++) {
  cycleMarkers.push({
    x: 0,
    y: R_INNER + R_GROWTH * cycle,
    cycle,
    month: "Jan",
  });
}

const values = points.map((p) => p.value);
const valueMin = Math.min(...values);
const valueMax = Math.max(...values);

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
const seqStart = hexToRgb(t.seq[0]);
const seqEnd = hexToRgb(t.seq[1]);
function valueColor(value) {
  const f = (value - valueMin) / (valueMax - valueMin);
  const r = Math.round(seqStart[0] + (seqEnd[0] - seqStart[0]) * f);
  const g = Math.round(seqStart[1] + (seqEnd[1] - seqStart[1]) * f);
  const b = Math.round(seqStart[2] + (seqEnd[2] - seqStart[2]) * f);
  return `rgb(${r}, ${g}, ${b})`;
}

// --- Plugins: radial grid (month spokes + year rings) and cycle labels ------
const radialGridPlugin = {
  id: "radialGrid",
  beforeDatasetsDraw(chart) {
    const { ctx, scales } = chart;
    const cx = scales.x.getPixelForValue(0);
    const cy = scales.y.getPixelForValue(0);
    const pxPerUnit = Math.abs(scales.x.getPixelForValue(1) - cx);

    ctx.save();
    ctx.strokeStyle = t.grid;
    ctx.lineWidth = 1;

    // Month spokes, radiating from the center to the outer edge.
    for (let m = 0; m < 12; m++) {
      const angle = (2 * Math.PI * m) / 12;
      const outerX = scales.x.getPixelForValue(MAX_R * Math.sin(angle));
      const outerY = scales.y.getPixelForValue(MAX_R * Math.cos(angle));
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(outerX, outerY);
      ctx.stroke();
    }

    // Year-boundary rings.
    for (let cycle = 1; cycle <= CYCLES; cycle++) {
      const r = R_INNER + R_GROWTH * cycle;
      ctx.beginPath();
      ctx.arc(cx, cy, r * pxPerUnit, 0, 2 * Math.PI);
      ctx.stroke();
    }

    // Month labels around the outer ring.
    ctx.fillStyle = t.inkSoft;
    ctx.font = "400 15px system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    for (let m = 0; m < 12; m++) {
      const angle = (2 * Math.PI * m) / 12;
      const labelX = scales.x.getPixelForValue(
        (MAX_R + 0.35) * Math.sin(angle),
      );
      const labelY = scales.y.getPixelForValue(
        (MAX_R + 0.35) * Math.cos(angle),
      );
      ctx.fillText(MONTH_NAMES[m], labelX, labelY);
    }

    ctx.restore();
  },
};

const cycleLabelPlugin = {
  id: "cycleLabels",
  afterDatasetsDraw(chart) {
    const { ctx, scales } = chart;
    ctx.save();
    ctx.font = "600 17px system-ui, sans-serif";
    ctx.fillStyle = t.ink;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    for (let cycle = 0; cycle < CYCLES; cycle++) {
      const r = R_INNER + R_GROWTH * cycle;
      const labelX = scales.x.getPixelForValue(0) + 14;
      const labelY = scales.y.getPixelForValue(r);
      ctx.fillText(`Year ${cycle + 1}`, labelX, labelY);
    }
    ctx.restore();
  },
};

const valueLegendPlugin = {
  id: "valueLegend",
  afterDraw(chart) {
    const { ctx, chartArea, scales } = chart;
    const barWidth = 26;
    const barHeight = 240;
    // Anchored in the dedicated right-hand gutter (see LEGEND_MARGIN) — clear
    // of the spiral, the radial grid and the month labels by construction.
    const x0 = scales.x.getPixelForValue(MAX_R) + 55;
    const y0 = (chartArea.top + chartArea.bottom) / 2 - barHeight / 2;

    const gradient = ctx.createLinearGradient(0, y0 + barHeight, 0, y0);
    gradient.addColorStop(0, t.seq[0]);
    gradient.addColorStop(1, t.seq[1]);

    ctx.save();
    ctx.fillStyle = gradient;
    ctx.fillRect(x0, y0, barWidth, barHeight);
    ctx.strokeStyle = t.grid;
    ctx.lineWidth = 1;
    ctx.strokeRect(x0, y0, barWidth, barHeight);

    ctx.fillStyle = t.inkSoft;
    ctx.font = "400 16px system-ui, sans-serif";
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText(`${valueMax.toFixed(0)}°C`, x0 + barWidth + 10, y0);
    ctx.fillText(
      `${valueMin.toFixed(0)}°C`,
      x0 + barWidth + 10,
      y0 + barHeight,
    );

    ctx.font = "600 15px system-ui, sans-serif";
    ctx.fillStyle = t.ink;
    ctx.textAlign = "center";
    ctx.fillText("Avg", x0 + barWidth / 2, y0 - 34);
    ctx.fillText("Temp", x0 + barWidth / 2, y0 - 16);
    ctx.restore();
  },
};

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart ---------------------------------------------------------------
new Chart(canvas, {
  type: "line",
  data: {
    datasets: [
      {
        data: points,
        showLine: true,
        fill: false,
        tension: 0,
        borderWidth: 3,
        pointRadius: 0,
        segment: {
          borderColor: (ctx) => {
            const p0 = points[ctx.p0DataIndex];
            const p1 = points[ctx.p1DataIndex];
            return valueColor((p0.value + p1.value) / 2);
          },
        },
      },
      {
        type: "scatter",
        data: cycleMarkers,
        showLine: false,
        pointRadius: 9,
        pointBackgroundColor: t.palette[0],
        pointBorderColor: t.pageBg,
        pointBorderWidth: 2,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    parsing: false,
    plugins: {
      title: {
        display: true,
        text: "spiral-timeseries · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { top: 4, bottom: 18 },
      },
      legend: { display: false },
      tooltip: {
        callbacks: {
          title: () => "",
          label: (ctx) =>
            `Year ${ctx.raw.cycle + 1}, ${ctx.raw.month}: ${ctx.raw.value.toFixed(1)}°C`,
        },
      },
    },
    scales: {
      // x gets extra room on the right for the color legend; y is expanded
      // symmetrically by the same total span so the spiral stays circular.
      x: {
        type: "linear",
        min: -SCALE_MAX,
        max: SCALE_MAX + LEGEND_MARGIN,
        display: false,
        grid: { display: false },
      },
      y: {
        type: "linear",
        min: -(SCALE_MAX + LEGEND_MARGIN / 2),
        max: SCALE_MAX + LEGEND_MARGIN / 2,
        display: false,
        grid: { display: false },
      },
    },
  },
  plugins: [radialGridPlugin, cycleLabelPlugin, valueLegendPlugin],
});
