// anyplot.ai
// crossword-basic: Crossword Puzzle Grid
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 84/100 | Created: 2026-09-02

//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;
const mount = window.ANYPLOT_SIZE || { width: 1200, height: 1200 };

// --- Data: 15x15 grid with 180-degree rotational symmetry -------------------
// 0 = white entry cell, 1 = black blocking cell.
// Only the top 7 rows + the palindromic middle row are authored by hand; the
// bottom 7 rows are derived by rotating the top half 180 degrees so the
// traditional newspaper-style symmetry is guaranteed by construction.
const gridSize = 15;
const topHalf = [
  [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
  [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
  [1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1],
  [0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
  [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
  [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1],
  [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
];
const middleRow = [0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0];

const grid = [];
for (let row = 0; row < gridSize; row += 1) {
  if (row < topHalf.length) {
    grid.push(topHalf[row].slice());
  } else if (row === Math.floor(gridSize / 2)) {
    grid.push(middleRow.slice());
  } else {
    grid.push(topHalf[gridSize - 1 - row].slice().reverse());
  }
}

// --- Numbering: standard across/down word-start scan -------------------------
const cells = [];
let nextNumber = 1;
for (let row = 0; row < gridSize; row += 1) {
  for (let col = 0; col < gridSize; col += 1) {
    const blocked = grid[row][col] === 1;
    let number = null;
    if (!blocked) {
      const startsAcross =
        (col === 0 || grid[row][col - 1] === 1) &&
        col < gridSize - 1 &&
        grid[row][col + 1] === 0;
      const startsDown =
        (row === 0 || grid[row - 1][col] === 1) &&
        row < gridSize - 1 &&
        grid[row + 1][col] === 0;
      if (startsAcross || startsDown) {
        number = nextNumber;
        nextNumber += 1;
      }
    }
    cells.push({ col, row, blocked, number });
  }
}

// --- Square plotting area, regardless of exact mount pixel size -------------
const titleSpace = 130;
const margin = 60;
const available = Math.min(
  mount.width - margin * 2,
  mount.height - titleSpace - margin
);
const gridLeft = (mount.width - available) / 2;
const gridTop = titleSpace + (mount.height - titleSpace - margin - available) / 2;

// The grid itself is content (like a heatmap's cell colors), not UI chrome —
// it reads as a printed puzzle card, so its paper/ink tones stay fixed
// instead of flipping with ANYPLOT_THEME (which would invert the black/white
// cell metaphor and crush entry-cell contrast against a dark page).
const entryFill = "#FFFDF6";
const blockedFill = "#1A1A17";
const cellStroke = "#4A4A44";
const outerFrameStroke = "#1A1A17";
const numberFill = "#1A1A17";

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "crossword-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 40,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  grid: { left: gridLeft, top: gridTop, width: available, height: available },
  xAxis: {
    type: "value",
    min: -0.5,
    max: gridSize - 0.5,
    show: false,
  },
  yAxis: {
    type: "value",
    min: -0.5,
    max: gridSize - 0.5,
    inverse: true,
    show: false,
  },
  series: [
    {
      type: "custom",
      coordinateSystem: "cartesian2d",
      data: cells.map((cell) => [cell.col, cell.row]),
      encode: { x: 0, y: 1 },
      renderItem: (params, api) => {
        const cell = cells[params.dataIndex];
        const topLeft = api.coord([cell.col - 0.5, cell.row - 0.5]);
        const size = api.size([1, 1]);
        const children = [
          {
            type: "rect",
            shape: { x: topLeft[0], y: topLeft[1], width: size[0], height: size[1] },
            style: {
              fill: cell.blocked ? blockedFill : entryFill,
              stroke: cellStroke,
              lineWidth: 1.5,
            },
          },
        ];
        if (cell.number !== null) {
          children.push({
            type: "text",
            style: {
              text: String(cell.number),
              x: topLeft[0] + 6,
              y: topLeft[1] + 4,
              fill: numberFill,
              fontSize: 15,
              fontWeight: 600,
              textVerticalAlign: "top",
              textAlign: "left",
            },
          });
        }
        return { type: "group", children };
      },
    },
  ],
  // Bolder outer frame vs. the thinner inner dividers gives the printed card a
  // typographic hierarchy instead of one uniform line weight throughout.
  graphic: [
    {
      type: "rect",
      shape: { x: gridLeft, y: gridTop, width: available, height: available },
      style: { fill: "none", stroke: outerFrameStroke, lineWidth: 5 },
      z: 100,
      silent: true,
    },
  ],
});
