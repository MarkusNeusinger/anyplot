// anyplot.ai
// qrcode-basic: Basic QR Code Generator
// Library: highcharts 12.6.0 | JavaScript 22.23.0
// Quality: 85/100 | Created: 2026-06-24
//# anyplot-orientation: square
// anyplot.ai
// qrcode-basic: Basic QR Code Generator
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-06-24

const t = window.ANYPLOT_TOKENS;

// Pre-computed QR matrix for "https://anyplot.ai"
// Version 2 (25×25 modules), Error Correction Level M
const QR_MATRIX = [
  [1,1,1,1,1,1,1,0,1,0,0,1,1,0,1,0,0,0,1,1,1,1,1,1,1],
  [1,0,0,0,0,0,1,0,1,0,1,1,1,1,1,0,1,0,1,0,0,0,0,0,1],
  [1,0,1,1,1,0,1,0,1,0,1,0,0,1,1,1,1,0,1,0,1,1,1,0,1],
  [1,0,1,1,1,0,1,0,0,1,0,0,1,0,1,0,1,0,1,0,1,1,1,0,1],
  [1,0,1,1,1,0,1,0,1,0,1,0,1,1,1,0,1,0,1,0,1,1,1,0,1],
  [1,0,0,0,0,0,1,0,0,1,1,1,0,1,1,0,1,0,1,0,0,0,0,0,1],
  [1,1,1,1,1,1,1,0,1,0,1,0,1,0,1,0,1,0,1,1,1,1,1,1,1],
  [0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,1,1,0,0,0,0,0,0,0,0],
  [1,0,0,1,1,1,1,1,1,1,0,1,1,1,1,0,1,1,0,0,1,0,1,1,1],
  [0,0,1,0,1,0,0,1,0,0,1,0,0,0,1,1,1,0,0,1,1,1,1,1,0],
  [1,0,0,0,0,1,1,1,1,0,1,1,0,0,1,1,0,0,0,1,1,1,0,0,1],
  [0,1,1,1,1,1,0,1,0,1,0,1,0,0,1,0,0,1,0,0,0,1,1,1,1],
  [1,0,1,1,1,0,1,0,1,1,1,1,0,1,1,1,0,0,1,1,0,0,0,0,1],
  [1,0,0,0,1,0,0,0,0,0,1,0,1,0,0,1,1,1,0,0,1,0,0,1,0],
  [1,1,0,0,0,0,1,1,1,1,0,0,0,0,1,1,0,0,0,0,1,1,1,1,1],
  [1,0,0,1,0,1,0,0,1,0,0,0,1,1,1,1,0,1,1,1,0,1,1,0,1],
  [1,0,1,1,1,0,1,0,1,0,1,1,1,0,0,0,1,1,1,1,1,0,1,1,0],
  [0,0,0,0,0,0,0,0,1,1,0,1,0,0,0,0,1,0,0,0,1,0,1,1,0],
  [1,1,1,1,1,1,1,0,1,0,1,0,1,1,1,0,1,0,1,0,1,0,0,0,1],
  [1,0,0,0,0,0,1,0,1,0,1,1,0,1,0,1,1,0,0,0,1,0,0,0,0],
  [1,0,1,1,1,0,1,0,1,0,1,1,0,1,0,1,1,1,1,1,1,0,0,0,1],
  [1,0,1,1,1,0,1,0,1,1,1,0,1,1,0,0,1,1,1,0,0,0,0,1,1],
  [1,0,1,1,1,0,1,0,0,0,0,1,0,1,0,0,1,0,0,0,1,1,1,1,1],
  [1,0,0,0,0,0,1,0,0,1,0,1,1,1,0,0,0,1,1,1,1,0,1,1,1],
  [1,1,1,1,1,1,1,0,1,1,0,1,1,1,0,0,1,1,1,0,0,1,0,0,1],
];

// Title — scale font size for length
const TITLE = "qrcode-basic · javascript · highcharts · anyplot.ai";
const titleLen = TITLE.length;
const titleFontSize = titleLen > 67
  ? Math.max(Math.round(22 * 67 / titleLen), 14) + "px"
  : "22px";

// Encoded URL label
const ENCODED_URL = "https://anyplot.ai";

// Module colors: dark ink on cream (light) / near-white on near-black (dark)
const MODULE_COLOR = t.ink;       // dark (#1A1A17) on light / light (#F0EFE8) on dark
const QR_BG       = t.pageBg;    // cream (#FAF8F1) on light / near-black (#1A1A17) on dark

// Chart — square, transparent background, no axes
const chart = Highcharts.chart("container", {
  chart: {
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    margin: [90, 60, 70, 60],
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: TITLE,
    style: { color: t.ink, fontSize: titleFontSize, fontWeight: "600" },
    margin: 20,
  },
  subtitle: {
    text: "Encodes: " + ENCODED_URL + "  |  Version 2  ·  ECC Level M",
    style: { color: t.inkSoft, fontSize: "13px" },
  },
  xAxis: { visible: false },
  yAxis: { visible: false },
  legend: { enabled: false },
  plotOptions: { series: { animation: false } },
  series: [],
});

// Draw QR code using Highcharts SVG renderer
const qrSize    = QR_MATRIX.length;  // 25 modules
const quietZone = 4;                 // standard quiet zone
const totalMods = qrSize + 2 * quietZone; // 33

const plotW = chart.plotWidth;
const plotH = chart.plotHeight;

// Center a square QR area within the plot area
const qrAreaSize = Math.min(plotW, plotH);
const offsetX = chart.plotLeft + (plotW - qrAreaSize) / 2;
const offsetY = chart.plotTop  + (plotH - qrAreaSize) / 2;

const cellSize = qrAreaSize / totalMods;

// White quiet zone background
chart.renderer.rect(offsetX, offsetY, qrAreaSize, qrAreaSize)
  .attr({ fill: QR_BG, zIndex: 3 })
  .add();

// Black QR modules
for (let row = 0; row < qrSize; row++) {
  for (let col = 0; col < qrSize; col++) {
    if (QR_MATRIX[row][col]) {
      chart.renderer.rect(
        offsetX + (col + quietZone) * cellSize,
        offsetY + (row + quietZone) * cellSize,
        cellSize,
        cellSize
      ).attr({ fill: MODULE_COLOR, zIndex: 4 }).add();
    }
  }
}
