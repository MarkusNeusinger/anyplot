// anyplot.ai
// datamatrix-basic: Basic Data Matrix 2D Barcode
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-02
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// Real ECC 200 Data Matrix, 16x16 modules, encoding "SERIAL:12345678"
// (ASCII encodation: letters/':' as ASCII+1, digit pairs 12/34/56/78 as
// value+130, padded with codeword 129; GF(256) Reed-Solomon over the ISO
// 16022 field poly 0x12D with 12 correction codewords; module placement via
// the standard ISO/IEC 16022 Annex F "utah" corner-wrap algorithm). Row 0 and
// the last column carry the alternating timing pattern; column 0 and the
// last row carry the solid L-shaped finder pattern.
const DM_MATRIX = [
  [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1],
  [1,0,1,0,1,1,0,0,1,0,1,0,1,1,1,0],
  [1,0,0,0,0,1,0,1,0,1,1,0,1,0,0,1],
  [1,1,1,0,0,0,0,1,0,0,1,1,0,0,1,0],
  [1,0,0,1,0,1,0,0,0,0,0,0,1,1,0,1],
  [1,0,0,0,1,1,1,0,0,1,1,1,0,0,1,0],
  [1,0,1,0,1,0,1,0,0,1,0,1,1,0,1,1],
  [1,1,1,1,0,0,0,0,0,1,0,0,1,1,0,0],
  [1,1,1,1,1,1,0,1,0,0,1,0,1,0,0,1],
  [1,1,0,0,1,0,0,0,1,1,1,0,0,0,1,0],
  [1,1,0,0,1,0,0,0,1,0,1,0,0,0,0,1],
  [1,1,0,0,1,1,0,1,0,1,1,0,1,0,0,0],
  [1,1,0,0,0,1,1,0,0,0,0,0,0,0,0,1],
  [1,0,1,1,1,0,1,0,0,1,0,1,0,1,0,0],
  [1,0,1,0,1,0,1,0,0,1,0,0,0,0,1,1],
  [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
];

const ENCODED_CONTENT = "SERIAL:12345678";
const TITLE = "datamatrix-basic · javascript · highcharts · anyplot.ai";

// Module colors: dark ink on cream (light) / near-white on near-black (dark)
const MODULE_COLOR = t.ink;
const DM_BG = t.pageBg;

// Chart — square, transparent background, no axes
const chart = Highcharts.chart("container", {
  chart: {
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    margin: [90, 60, 30, 60],
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: TITLE,
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
    margin: 20,
  },
  subtitle: {
    text: "Encodes: " + ENCODED_CONTENT + "  |  16×16 modules  ·  ECC 200",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: { visible: false },
  yAxis: { visible: false },
  legend: { enabled: false },
  plotOptions: { series: { animation: false } },
  series: [],
});

// Draw the Data Matrix using the Highcharts SVG renderer
const dmSize = DM_MATRIX.length; // 16 modules
const quietZone = 3; // >= 1 module quiet zone required for reliable scanning
const totalMods = dmSize + 2 * quietZone;

const plotW = chart.plotWidth;
const plotH = chart.plotHeight;

// Center a square code area within the plot area
const codeAreaSize = Math.min(plotW, plotH);
const offsetX = chart.plotLeft + (plotW - codeAreaSize) / 2;
const offsetY = chart.plotTop + (plotH - codeAreaSize) / 2;

const cellSize = codeAreaSize / totalMods;

// Quiet-zone background
chart.renderer
  .rect(offsetX, offsetY, codeAreaSize, codeAreaSize)
  .attr({ fill: DM_BG, zIndex: 3, "shape-rendering": "crispEdges" })
  .add();

// Dark modules (finder L-pattern, timing pattern, and encoded data region)
for (let row = 0; row < dmSize; row++) {
  for (let col = 0; col < dmSize; col++) {
    if (DM_MATRIX[row][col]) {
      chart.renderer
        .rect(
          offsetX + (col + quietZone) * cellSize,
          offsetY + (row + quietZone) * cellSize,
          cellSize,
          cellSize
        )
        .attr({ fill: MODULE_COLOR, zIndex: 4, "shape-rendering": "crispEdges" })
        .add();
    }
  }
}
