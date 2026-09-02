// anyplot.ai
// crossword-basic: Crossword Puzzle Grid
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-09-02

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;
const size = window.ANYPLOT_SIZE;

// Crossword cell colors — fixed regardless of theme (contrast IS the data):
// blocked squares stay near-black and entry squares stay near-white in both
// light and dark renders, matching the traditional newspaper-crossword
// convention instead of flipping with the page chrome.
const CELL_BLOCK = "#1A1A17";
const CELL_ENTRY = "#FAF8F1";

// --- Data: symmetric 15x15 crossword grid (180-degree rotational symmetry) -
const N = 15;

// Only the "first half" of blocked cells is listed; the mirrored partner
// (N-1-row, N-1-col) is added below, which is how newspaper crosswords keep
// their traditional 180-degree rotational symmetry.
const blockedHalf = [
  [0, 3], [0, 10],
  [1, 3], [1, 10],
  [2, 6], [2, 8],
  [3, 0], [3, 6], [3, 11],
  [4, 4], [4, 9],
  [5, 2], [5, 6], [5, 8], [5, 12],
  [6, 0], [6, 5], [6, 9], [6, 14],
  [7, 7],
];
const blocked = new Set();
blockedHalf.forEach(([row, col]) => {
  blocked.add(`${row},${col}`);
  blocked.add(`${N - 1 - row},${N - 1 - col}`);
});
const isBlocked = (row, col) => blocked.has(`${row},${col}`);

// Standard crossword numbering: a cell is numbered when it starts an across
// and/or a down entry (no open cell to its left/above, and an open cell
// follows to its right/below).
let nextNumber = 1;
const numberedCells = [];
for (let row = 0; row < N; row += 1) {
  for (let col = 0; col < N; col += 1) {
    if (isBlocked(row, col)) continue;
    const startsAcross = (col === 0 || isBlocked(row, col - 1)) &&
      col + 1 < N && !isBlocked(row, col + 1);
    const startsDown = (row === 0 || isBlocked(row - 1, col)) &&
      row + 1 < N && !isBlocked(row + 1, col);
    if (startsAcross || startsDown) {
      numberedCells.push({ row, col, number: nextNumber });
      nextNumber += 1;
    }
  }
}

// --- Layout: fixed margins keep the plot area an exact square so grid cells
// stay 1:1, independent of Highcharts' auto layout for title/axes -----------
const MARGIN_TOP = 100;
const MARGIN_BOTTOM = 40;
const MARGIN_SIDE = 70;
const cellPx = (size.width - MARGIN_SIDE * 2) / N;

const blockedCells = [...blocked].map((key) => {
  const [row, col] = key.split(",").map(Number);
  return { x: col + 0.5, y: row + 0.5 };
});

const entryCells = [];
for (let row = 0; row < N; row += 1) {
  for (let col = 0; col < N; col += 1) {
    if (!isBlocked(row, col)) entryCells.push({ x: col + 0.5, y: row + 0.5 });
  }
}

const numberPoints = numberedCells.map(({ row, col, number }) => ({
  x: col,
  y: row,
  name: String(number),
}));

// --- Chart -------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    spacing: [0, 0, 0, 0],
    marginTop: MARGIN_TOP,
    marginBottom: MARGIN_BOTTOM,
    marginLeft: MARGIN_SIDE,
    marginRight: MARGIN_SIDE,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: "crossword-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  tooltip: { enabled: false },
  legend: { enabled: false },
  xAxis: {
    min: 0,
    max: N,
    tickInterval: 1,
    gridLineWidth: 1,
    gridLineColor: t.grid,
    lineWidth: 0,
    tickLength: 0,
    labels: { enabled: false },
    title: { text: null },
  },
  yAxis: {
    min: 0,
    max: N,
    reversed: true,
    tickInterval: 1,
    gridLineWidth: 1,
    gridLineColor: t.grid,
    lineWidth: 0,
    tickLength: 0,
    labels: { enabled: false },
    title: { text: null },
  },
  plotOptions: {
    series: { animation: false, enableMouseTracking: false },
  },
  series: [
    {
      name: "Entry cells",
      type: "scatter",
      data: entryCells,
      marker: {
        symbol: "square",
        radius: cellPx / 2 + 0.5,
        fillColor: CELL_ENTRY,
        lineWidth: 0,
      },
      dataLabels: { enabled: false },
    },
    {
      name: "Blocked cells",
      type: "scatter",
      data: blockedCells,
      marker: {
        symbol: "square",
        radius: cellPx / 2 + 0.5,
        fillColor: CELL_BLOCK,
        lineWidth: 0,
      },
      dataLabels: { enabled: false },
    },
    {
      name: "Clue numbers",
      type: "scatter",
      data: numberPoints,
      marker: { enabled: false },
      dataLabels: {
        enabled: true,
        format: "{point.name}",
        align: "left",
        verticalAlign: "top",
        x: 3,
        y: 2,
        padding: 0,
        crop: false,
        overflow: "allow",
        allowOverlap: true,
        style: {
          color: CELL_BLOCK,
          fontSize: "14px",
          fontWeight: "600",
          textOutline: "none",
        },
      },
    },
  ],
});
