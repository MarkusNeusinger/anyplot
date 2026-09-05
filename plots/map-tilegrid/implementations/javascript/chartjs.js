// anyplot.ai
// map-tilegrid: Tile Grid Map for Equal-Area Geographic Comparison
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-05
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Renewable share of electricity generation (%) across European countries.
// Every country gets an equally-sized tile, so a small nation (Iceland) reads
// with the same visual weight as a large one (France) — the point of a tile
// grid map. Row/col positions approximate each country's real position
// (row 0 = north, col 0 = west); values are illustrative, not official stats.
const countries = [
  { region: "IS", name: "Iceland", value: 85, row: 0, col: 0 },
  { region: "NO", name: "Norway", value: 98, row: 0, col: 4 },
  { region: "SE", name: "Sweden", value: 65, row: 0, col: 5 },
  { region: "FI", name: "Finland", value: 55, row: 0, col: 6 },
  { region: "IE", name: "Ireland", value: 40, row: 1, col: 0 },
  { region: "GB", name: "United Kingdom", value: 43, row: 1, col: 1 },
  { region: "DK", name: "Denmark", value: 62, row: 1, col: 4 },
  { region: "BE", name: "Belgium", value: 24, row: 2, col: 1 },
  { region: "NL", name: "Netherlands", value: 37, row: 2, col: 2 },
  { region: "DE", name: "Germany", value: 46, row: 2, col: 3 },
  { region: "CZ", name: "Czechia", value: 18, row: 2, col: 4 },
  { region: "PL", name: "Poland", value: 16, row: 2, col: 5 },
  { region: "FR", name: "France", value: 25, row: 3, col: 1 },
  { region: "CH", name: "Switzerland", value: 74, row: 3, col: 2 },
  { region: "AT", name: "Austria", value: 78, row: 3, col: 3 },
  { region: "RO", name: "Romania", value: 43, row: 3, col: 5 },
  { region: "PT", name: "Portugal", value: 61, row: 4, col: 0 },
  { region: "ES", name: "Spain", value: 42, row: 4, col: 1 },
  { region: "IT", name: "Italy", value: 37, row: 4, col: 3 },
  { region: "GR", name: "Greece", value: 44, row: 5, col: 4 },
];
const maxRow = Math.max(...countries.map((c) => c.row));
const maxCol = Math.max(...countries.map((c) => c.col));
const values = countries.map((c) => c.value);
const domainMin = Math.min(...values);
const domainMax = Math.max(...values);

// --- Color helpers (Imprint imprint_seq, single-polarity) -------------------
function hexToRgb(hex) {
  const num = parseInt(hex.replace("#", ""), 16);
  return [(num >> 16) & 255, (num >> 8) & 255, num & 255];
}
function lerp(a, b, f) {
  return Math.round(a + (b - a) * f);
}
function lerpColor(hexA, hexB, f) {
  const a = hexToRgb(hexA);
  const b = hexToRgb(hexB);
  return [lerp(a[0], b[0], f), lerp(a[1], b[1], f), lerp(a[2], b[2], f)];
}
function sequentialRgb(value) {
  const f = (value - domainMin) / (domainMax - domainMin);
  return lerpColor(t.seq[0], t.seq[1], f);
}
function rgbToCss(rgb) {
  return `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
}
function relativeLuminance(rgb) {
  return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2];
}
function textColorFor(rgb) {
  return relativeLuminance(rgb) > 140 ? "#1A1A17" : "#F0EFE8";
}

// --- Mount -------------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart --------------------------------------------------------------
// Chart.js has no native tile-grid/geo type; a scatter chart supplies the
// row/col coordinate system while a custom plugin paints each equal-area
// tile, its region label, and a colorbar directly on the canvas.
const tilePlugin = {
  id: "tileGrid",
  afterDraw(chart) {
    const { ctx, chartArea, scales } = chart;
    const xScale = scales.x;
    const yScale = scales.y;
    const tileW = xScale.getPixelForValue(1) - xScale.getPixelForValue(0);
    const tileH = Math.abs(
      yScale.getPixelForValue(1) - yScale.getPixelForValue(0),
    );
    const gap = 6;

    ctx.save();
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    for (const country of countries) {
      const rgb = sequentialRgb(country.value);
      const cx = xScale.getPixelForValue(country.col);
      const cy = yScale.getPixelForValue(country.row);
      const left = cx - tileW / 2 + gap / 2;
      const top = cy - tileH / 2 + gap / 2;
      const size = Math.min(tileW, tileH) - gap;

      ctx.fillStyle = rgbToCss(rgb);
      ctx.fillRect(left, top, size, size);

      ctx.fillStyle = textColorFor(rgb);
      ctx.font = "700 26px sans-serif";
      ctx.fillText(country.region, cx, cy);
    }

    // --- Colorbar (data-range domain) ---------------------------------------
    const barW = 34;
    const barX = chartArea.right + 60;
    const barTop = chartArea.top;
    const barBottom = chartArea.bottom;
    const topColor = rgbToCss(sequentialRgb(domainMax));
    const bottomColor = rgbToCss(sequentialRgb(domainMin));

    const gradient = ctx.createLinearGradient(0, barTop, 0, barBottom);
    gradient.addColorStop(0, topColor);
    gradient.addColorStop(1, bottomColor);
    ctx.fillStyle = gradient;
    ctx.fillRect(barX, barTop, barW, barBottom - barTop);
    ctx.strokeStyle = t.inkSoft;
    ctx.lineWidth = 1.5;
    ctx.strokeRect(barX, barTop, barW, barBottom - barTop);

    ctx.font = "16px sans-serif";
    ctx.fillStyle = t.inkSoft;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText(`${domainMax}%`, barX + barW + 10, barTop);
    ctx.fillText(`${domainMin}%`, barX + barW + 10, barBottom);

    ctx.save();
    ctx.translate(barX + barW + 58, (barTop + barBottom) / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = "center";
    ctx.font = "18px sans-serif";
    ctx.fillStyle = t.ink;
    ctx.fillText("Renewable Share of Electricity (%)", 0, 0);
    ctx.restore();

    ctx.restore();
  },
};

new Chart(canvas, {
  type: "scatter",
  data: {
    datasets: [
      {
        data: countries.map((c) => ({ x: c.col, y: c.row })),
        pointStyle: false,
        showLine: false,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: {
      padding: { top: 10, right: 140, bottom: 10, left: 10 },
    },
    plugins: {
      title: {
        display: true,
        text: "Renewable Energy in Europe · map-tilegrid · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 19 },
        padding: { bottom: 20 },
      },
      legend: { display: false },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        type: "linear",
        min: -0.5,
        max: maxCol + 0.5,
        display: false,
      },
      y: {
        type: "linear",
        min: -0.5,
        max: maxRow + 0.5,
        reverse: true,
        display: false,
      },
    },
  },
  plugins: [tilePlugin],
});
