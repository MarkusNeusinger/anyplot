// anyplot.ai
// datamatrix-basic: Basic Data Matrix 2D Barcode
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-02

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data --------------------------------------------------------------
// Chart.js has no core "matrix" chart type — chartjs-chart-matrix is a
// community plugin and is not installed. The module grid below is drawn by
// a custom plugin instead, so the data model here is the ISO/IEC 16022
// module layout itself: a solid L-shaped finder pattern (left column +
// bottom row), an alternating clock/timing track (top row + right column),
// and interior "data" modules derived deterministically from the ASCII
// bits of the encoded content string.
const content = "SERIAL:12345678";
const gridSize = 16;

const bits = [];
for (const char of content) {
  const code = char.charCodeAt(0);
  for (let b = 7; b >= 0; b--) bits.push((code >> b) & 1);
}

const modules = [];
for (let row = 0; row < gridSize; row++) {
  const line = [];
  for (let col = 0; col < gridSize; col++) {
    let dark;
    if (col === 0 || row === gridSize - 1) {
      dark = true; // solid L-shaped finder pattern
    } else if (row === 0) {
      dark = col % 2 === 0; // top timing/clock track
    } else if (col === gridSize - 1) {
      dark = row % 2 === 0; // right timing/clock track
    } else {
      const bitIndex = (row - 1) * (gridSize - 2) + (col - 1);
      dark = bits[bitIndex % bits.length] === 1;
    }
    line.push(dark);
  }
  modules.push(line);
}

// --- Mount -----------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -----------------------------------------------------------------
// An empty scatter chart provides the theme-aware title/canvas scaffolding;
// a custom plugin draws the module grid directly onto the chart area so the
// modules stay perfectly square regardless of the title's reserved height.
const moduleGridPlugin = {
  id: "datamatrixGrid",
  afterDraw(chart) {
    const { ctx, chartArea } = chart;
    const areaWidth = chartArea.right - chartArea.left;
    const areaHeight = chartArea.bottom - chartArea.top;
    const side = Math.min(areaWidth, areaHeight) * 0.84; // leaves a quiet zone
    const cell = side / gridSize;
    const originX = chartArea.left + (areaWidth - side) / 2;
    const originY = chartArea.top + (areaHeight - side) / 2;

    ctx.save();
    ctx.fillStyle = t.ink;
    for (let row = 0; row < gridSize; row++) {
      for (let col = 0; col < gridSize; col++) {
        if (modules[row][col]) {
          ctx.fillRect(originX + col * cell, originY + row * cell, cell + 0.6, cell + 0.6);
        }
      }
    }
    ctx.restore();
  },
};

new Chart(canvas, {
  type: "scatter",
  data: { datasets: [] },
  plugins: [moduleGridPlugin],
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: 40 },
    scales: {
      x: { display: false },
      y: { display: false },
    },
    plugins: {
      legend: { display: false },
      title: {
        display: true,
        text: "datamatrix-basic · javascript · chartjs · anyplot.ai",
        color: t.ink,
        font: { size: 22 },
        padding: { top: 10, bottom: 4 },
      },
      subtitle: {
        display: true,
        text: `Encodes "${content}"`,
        color: t.inkSoft,
        font: { size: 15, style: "normal" },
        padding: { bottom: 20 },
      },
    },
  },
});
