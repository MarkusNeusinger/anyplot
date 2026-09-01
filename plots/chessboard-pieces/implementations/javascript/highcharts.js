// anyplot.ai
// chessboard-pieces: Chess Board with Pieces for Position Diagrams
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-01
//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Scholar's mate, final position after 1.e4 e5 2.Bc4 Nc6 3.Qh5 Nf6?? 4.Qxf7#
// Square -> piece code (uppercase = white, lowercase = black).
const pieces = {
  e1: "K", a1: "R", h1: "R", c1: "B", b1: "N", g1: "N",
  f7: "Q", c4: "B", a2: "P", b2: "P", c2: "P", d2: "P",
  e4: "P", f2: "P", g2: "P", h2: "P",
  e8: "k", a8: "r", h8: "r", c8: "b", f8: "b", c6: "n", f6: "n",
  d8: "q", a7: "p", b7: "p", c7: "p", d7: "p", e5: "p", g7: "p", h7: "p",
};

// Unicode chess symbols: hollow glyphs U+2654-2659 read as white pieces,
// filled glyphs U+265A-265F read as black pieces — no extra data color needed.
const GLYPHS = {
  K: "♔", Q: "♕", R: "♖", B: "♗", N: "♘", P: "♙",
  k: "♚", q: "♛", r: "♜", b: "♝", n: "♞", p: "♟",
};

const FILES = ["a", "b", "c", "d", "e", "f", "g", "h"];

// --- Chart -------------------------------------------------------------------
const title = "chessboard-pieces · javascript · highcharts · anyplot.ai";
const titleFontSize = Math.round(22 * (title.length > 67 ? 67 / title.length : 1));

const chart = Highcharts.chart("container", {
  chart: { backgroundColor: "transparent", animation: false,
           style: { fontFamily: "inherit" } },
  credits: { enabled: false },
  title: { text: title, style: { color: t.ink, fontSize: `${titleFontSize}px`, fontWeight: "600" } },
  subtitle: { text: "Scholar’s mate · final position after 4.Qxf7#",
              style: { color: t.inkSoft, fontSize: "14px" } },
  xAxis: { visible: false },
  yAxis: { visible: false, title: { text: null } },
  legend: { enabled: false },
  tooltip: { enabled: false },
  plotOptions: { series: { animation: false } },
  series: [],
});

// --- Board geometry (derived from the rendered plot area, then drawn with the
// core SVGRenderer — the heatmap module isn't loaded, so the 8x8 grid and the
// piece glyphs are custom shapes rather than a series type) -------------------
const GUTTER = 36; // reserves room for the file/rank coordinate labels
const availW = chart.plotWidth - GUTTER;
const availH = chart.plotHeight - GUTTER;
const boardSize = Math.min(availW, availH);
const boardLeft = chart.plotLeft + GUTTER + (availW - boardSize) / 2;
const boardTop = chart.plotTop + (availH - boardSize) / 2;
const cell = boardSize / 8;

const lightSquareFill = t.elevatedBg;
const darkSquareFill = Highcharts.color(t.ink).setOpacity(0.16).get();
const labelStyle = { color: t.inkSoft, fontSize: "14px" };

// Board frame
chart.renderer.rect(boardLeft, boardTop, boardSize, boardSize, 0)
  .attr({ fill: "none", stroke: t.inkSoft, "stroke-width": 1.5 })
  .add();

for (let displayRow = 0; displayRow < 8; displayRow++) {
  const rank = 8 - displayRow; // row 0 (top) is rank 8, row 7 (bottom) is rank 1

  for (let file = 0; file < 8; file++) {
    const rankIndex = rank - 1;
    const isLight = (file + rankIndex) % 2 === 1; // a1 dark, h1 light
    const x = boardLeft + file * cell;
    const y = boardTop + displayRow * cell;

    chart.renderer.rect(x, y, cell, cell)
      .attr({ fill: isLight ? lightSquareFill : darkSquareFill })
      .add();

    const square = `${FILES[file]}${rank}`;
    const piece = pieces[square];
    if (piece) {
      chart.renderer.text(GLYPHS[piece], x + cell / 2, y + cell / 2 + cell * 0.32)
        .attr({ align: "center", zIndex: 5 })
        .css({ color: t.ink, fontSize: `${Math.round(cell * 0.62)}px`,
               textOutline: `2px ${t.pageBg}` })
        .add();
    }
  }

  // Rank coordinate label (left gutter)
  chart.renderer.text(String(rank), chart.plotLeft + GUTTER / 2, boardTop + displayRow * cell + cell / 2 + 5)
    .attr({ align: "center" })
    .css(labelStyle)
    .add();
}

// File coordinate labels (bottom gutter)
FILES.forEach((file, i) => {
  chart.renderer.text(file, boardLeft + i * cell + cell / 2, boardTop + boardSize + GUTTER / 2 + 5)
    .attr({ align: "center" })
    .css(labelStyle)
    .add();
});
