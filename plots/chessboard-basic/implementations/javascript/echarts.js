// anyplot.ai
// chessboard-basic: Chess Board Grid Visualization
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-01

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Standard algebraic notation: files a-h (columns), ranks 1-8 (rows).
// A square is light when (file index + rank index) is odd — h1 light, a1 dark.
const files = ["a", "b", "c", "d", "e", "f", "g", "h"];
const ranks = ["1", "2", "3", "4", "5", "6", "7", "8"];

const squares = [];
for (let file = 0; file < files.length; file++) {
  for (let rank = 0; rank < ranks.length; rank++) {
    const isLight = (file + rank) % 2 === 1;
    squares.push([file, rank, isLight ? 1 : 0]);
  }
}

// Wood-toned board: dark squares use the Imprint ochre hue (semantic
// exception — wood → ochre); light squares use the amber semantic anchor, a
// fixed non-theme-adaptive gold tone, so the light/dark square pair keeps the
// same identity in both themes (data colors must not flip with the theme).
const DARK_SQUARE = t.palette[3];
const LIGHT_SQUARE = t.amber;

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "chessboard-basic · javascript · echarts · anyplot.ai",
    subtext: "White's near-right square (h1) is light — standard orientation",
    left: "center",
    top: 20,
    textStyle: { color: t.ink, fontSize: 22 },
    subtextStyle: { color: t.inkSoft, fontSize: 16 },
  },
  grid: { left: 140, right: 140, top: 140, bottom: 140 },
  xAxis: {
    type: "category",
    data: files,
    position: "bottom",
    axisLabel: { color: t.inkSoft, fontSize: 20 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "category",
    data: ranks,
    position: "left",
    axisLabel: { color: t.inkSoft, fontSize: 20 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  series: [
    {
      type: "custom",
      encode: { x: 0, y: 1 },
      data: squares,
      renderItem: (params, api) => {
        const [x, y] = api.coord([api.value(0), api.value(1)]);
        const [cellWidth, cellHeight] = api.size([1, 1]);
        return {
          type: "rect",
          shape: {
            x: x - cellWidth / 2,
            y: y - cellHeight / 2,
            width: cellWidth,
            height: cellHeight,
          },
          style: {
            fill: api.value(2) === 1 ? LIGHT_SQUARE : DARK_SQUARE,
            stroke: t.grid,
            lineWidth: 1,
          },
        };
      },
    },
  ],
});
