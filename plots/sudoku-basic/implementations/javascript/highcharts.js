// anyplot.ai
// sudoku-basic: Basic Sudoku Grid
// Library: highcharts 12.6.0 | JavaScript 22.23.0
// Quality: 91/100 | Created: 2026-06-25
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// Sudoku puzzle (0 = empty cell)
const puzzle = [
  [5, 3, 0, 0, 7, 0, 0, 0, 0],
  [6, 0, 0, 1, 9, 5, 0, 0, 0],
  [0, 9, 8, 0, 0, 0, 0, 6, 0],
  [8, 0, 0, 0, 6, 0, 0, 0, 3],
  [4, 0, 0, 8, 0, 3, 0, 0, 1],
  [7, 0, 0, 0, 2, 0, 0, 0, 6],
  [0, 6, 0, 0, 0, 0, 2, 8, 0],
  [0, 0, 0, 4, 1, 9, 0, 0, 5],
  [0, 0, 0, 0, 8, 0, 0, 7, 9],
];

// Build scatter data: one point per filled cell
const seriesData = [];
for (let row = 0; row < 9; row++) {
  for (let col = 0; col < 9; col++) {
    const val = puzzle[row][col];
    if (val !== 0) {
      seriesData.push({ x: col + 0.5, y: row + 0.5, val });
    }
  }
}

// Internal grid lines — thick at box boundaries (3, 6), thin at cell boundaries
const xPlotLines = [];
const yPlotLines = [];
for (let i = 1; i <= 8; i++) {
  const isBox = i % 3 === 0;
  xPlotLines.push({ value: i, color: isBox ? t.ink : t.inkSoft, width: isBox ? 3 : 1, zIndex: 4 });
  yPlotLines.push({ value: i, color: isBox ? t.ink : t.inkSoft, width: isBox ? 3 : 1, zIndex: 4 });
}

// Checkerboard shading: 5 alternate 3×3 boxes [boxRow, boxCol]
const SHADED_BOXES = [[0, 0], [0, 2], [1, 1], [2, 0], [2, 2]];

function drawBoxShades(chart) {
  if (chart._boxShades) {
    chart._boxShades.forEach((el) => el.destroy());
  }
  chart._boxShades = [];
  const boxW = chart.plotWidth / 3;
  const boxH = chart.plotHeight / 3;
  SHADED_BOXES.forEach(([boxRow, boxCol]) => {
    const el = chart.renderer
      .rect(chart.plotLeft + boxCol * boxW, chart.plotTop + boxRow * boxH, boxW, boxH)
      .attr({ fill: t.elevatedBg, zIndex: 1 })
      .add();
    chart._boxShades.push(el);
  });
}

Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
    plotBorderColor: t.ink,
    plotBorderWidth: 3,
    margin: [80, 60, 60, 60],
    events: {
      load: function () { drawBoxShades(this); },
      redraw: function () { drawBoxShades(this); },
    },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "sudoku-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  xAxis: {
    min: 0,
    max: 9,
    startOnTick: false,
    endOnTick: false,
    lineWidth: 0,
    tickLength: 0,
    gridLineWidth: 0,
    labels: { enabled: false },
    title: { enabled: false },
    plotLines: xPlotLines,
  },
  yAxis: {
    min: 0,
    max: 9,
    reversed: true,
    startOnTick: false,
    endOnTick: false,
    lineWidth: 0,
    tickLength: 0,
    gridLineWidth: 0,
    labels: { enabled: false },
    title: { enabled: false },
    plotLines: yPlotLines,
  },
  legend: { enabled: false },
  tooltip: { enabled: false },
  plotOptions: {
    scatter: {
      marker: { enabled: false },
      dataLabels: {
        enabled: true,
        allowOverlap: true,
        align: "center",
        verticalAlign: "middle",
        y: 0,
        formatter: function () {
          return this.point.val;
        },
        style: {
          color: t.ink,
          fontSize: "28px",
          fontWeight: "700",
          textOutline: "none",
        },
      },
    },
    series: { animation: false },
  },
  series: [
    {
      type: "scatter",
      name: "Numbers",
      data: seriesData,
      color: "transparent",
    },
  ],
});
