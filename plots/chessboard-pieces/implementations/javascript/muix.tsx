// anyplot.ai
// chessboard-pieces: Chess Board with Pieces for Position Diagrams
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 94/100 | Created: 2026-09-01
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const FILES = ["a", "b", "c", "d", "e", "f", "g", "h"];
const RANKS = ["1", "2", "3", "4", "5", "6", "7", "8"];
const SQUARE_COLOR = { light: t.amber, dark: t.palette[3] }; // light and dark wood, the same in both themes
// Pieces keep fixed inks so white and black read the same on both square colors in both themes
const PIECE_LIGHT = "#FAF8F1";
const PIECE_DARK = "#1A1A17";
const MARK_COLOR = t.palette[4]; // semantic: matte red frames the squares the position marks
const PIECE_ORDER = "KQRBNP"; // white glyphs U+2654-2659 and black glyphs U+265A-265F follow this order
const TEXT_STYLE = "︎"; // asks for the text glyph, not an emoji
const GLYPH_SHARE = 0.8; // glyph size as a share of the square, leaves an inset to the edges
const HEADER_H = 96;
const AXIS_SIZE = 48;
const PAD = 20;

// Data: replace this block with your own parameters
// Position after Scholar's Mate (1.e4 e5 2.Qh5 Nc6 3.Bc4 Nf6?? 4.Qxf7#); uppercase is white, lowercase black
const POSITION = "Scholar's Mate"; // role: extra
const PIECES: Record<string, string> = {
  e1: "K", f7: "Q", a1: "R", h1: "R", c1: "B", c4: "B", b1: "N", g1: "N",
  a2: "P", b2: "P", c2: "P", d2: "P", e4: "P", f2: "P", g2: "P", h2: "P",
  e8: "k", d8: "q", a8: "r", h8: "r", c8: "b", f8: "b", c6: "n", f6: "n",
  a7: "p", b7: "p", c7: "p", d7: "p", e5: "p", g7: "p", h7: "p",
}; // role: pieces
const MARKED = ["f7", "e8"]; // role: extra
const MARK_NOTE = "Qxf7#: the white queen on f7 checkmates the black king on e8"; // role: extra

// Plot: reads only the parameters and the constants above
const ranksTopToBottom = [...RANKS].reverse();
const marked = new Set(MARKED);
// a1 is dark, so a square is light when file index + rank number is even (h1 and a8 light)
const squares = ranksTopToBottom.flatMap((rank) =>
  FILES.map((file, fIdx) => ({
    id: `${file}${rank}`,
    file,
    rank,
    fill: (fIdx + Number(rank)) % 2 === 0 ? SQUARE_COLOR.light : SQUARE_COLOR.dark,
  })),
);
const pieces = Object.entries(PIECES).map(([square, code]) => {
  const index = PIECE_ORDER.indexOf(code.toUpperCase());
  return {
    square,
    file: square[0],
    rank: square.slice(1),
    white: code === code.toUpperCase(),
    outline: String.fromCodePoint(0x2654 + index) + TEXT_STYLE,
    solid: String.fromCodePoint(0x265a + index) + TEXT_STYLE,
  };
});
const whiteCount = pieces.filter((p) => p.white).length;

const TITLE = `${POSITION} · chessboard-pieces · javascript · muix · anyplot.ai`;
const subtitle = `${whiteCount} white and ${pieces.length - whiteCount} black pieces · framed: ${MARK_NOTE}`;

function BoardLayer() {
  const xScale = useXScale("file");
  const yScale = useYScale("rank");
  const { left, top, width, height } = useDrawingArea();
  const cell = xScale.bandwidth();
  return (
    <g>
      {squares.map((sq) => (
        <rect key={sq.id} x={xScale(sq.file)} y={yScale(sq.rank)} width={cell} height={cell} fill={sq.fill} />
      ))}
      {squares
        .filter((sq) => marked.has(sq.id))
        .map((sq) => (
          <rect
            key={`mark-${sq.id}`}
            x={xScale(sq.file) + 3}
            y={yScale(sq.rank) + 3}
            width={cell - 6}
            height={cell - 6}
            fill="none"
            stroke={MARK_COLOR}
            strokeWidth={5}
          />
        ))}
      <rect x={left} y={top} width={width} height={height} fill="none" stroke={t.ink} strokeWidth={3} />
    </g>
  );
}

// White pieces: the white glyph's outline over a light fill of the solid shape; black pieces: the solid glyph
function PieceLayer() {
  const xScale = useXScale("file");
  const yScale = useYScale("rank");
  const cell = xScale.bandwidth();
  const glyph = {
    textAnchor: "middle" as const,
    dominantBaseline: "central" as const,
    fontSize: cell * GLYPH_SHARE,
    fontFamily: "'DejaVu Sans', 'Noto Sans Symbols 2', 'Segoe UI Symbol', sans-serif",
  };
  return (
    <g pointerEvents="none">
      {pieces.map((p) => {
        const x = xScale(p.file) + cell / 2;
        const y = yScale(p.rank) + cell / 2;
        return p.white ? (
          <g key={p.square}>
            <text x={x} y={y} fill={PIECE_LIGHT} stroke={PIECE_LIGHT} strokeWidth={cell * 0.06} strokeLinejoin="round" {...glyph}>
              {p.solid}
            </text>
            <text x={x} y={y} fill={PIECE_DARK} {...glyph}>
              {p.outline}
            </text>
          </g>
        ) : (
          <text key={p.square} x={x} y={y} fill={PIECE_DARK} {...glyph}>
            {p.solid}
          </text>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const containerSide = Math.min(width, height - HEADER_H);

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column", alignItems: "center" }}>
      <div style={{ height: HEADER_H, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6, paddingTop: 6 }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{subtitle}</div>
      </div>
      <ChartsContainer
        width={containerSide}
        height={containerSide}
        margin={{ top: PAD, right: PAD, bottom: PAD, left: PAD }}
        skipAnimation
        series={[]}
        xAxis={[
          {
            id: "file",
            scaleType: "band",
            data: FILES,
            categoryGapRatio: 0,
            height: AXIS_SIZE,
            disableLine: true,
            disableTicks: true,
            tickLabelStyle: { fontSize: 16, fontWeight: 600, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            id: "rank",
            scaleType: "band",
            data: ranksTopToBottom,
            categoryGapRatio: 0,
            width: AXIS_SIZE,
            disableLine: true,
            disableTicks: true,
            tickLabelStyle: { fontSize: 16, fontWeight: 600, fill: t.inkSoft },
          },
        ]}
      >
        <BoardLayer />
        <PieceLayer />
        <ChartsXAxis axisId="file" />
        <ChartsYAxis axisId="rank" />
      </ChartsContainer>
    </div>
  );
}
