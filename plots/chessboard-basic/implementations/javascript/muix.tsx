// anyplot.ai
// chessboard-basic: Chess Board Grid Visualization
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-09-01
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const HEADER_H = 96;
const AXIS_SIZE = 48;
const PAD = 20;
const SQUARE_COLOR = { light: t.amber, dark: t.palette[3] }; // light and dark wood

// Data: board size, files are labelled a, b, c, … and ranks 1, 2, 3, …
const N_FILES = 8;
const N_RANKS = 8;

// Plot: reads only the parameters and the constants above
const files = Array.from({ length: N_FILES }, (_, i) => String.fromCharCode(97 + i));
const ranksTopToBottom = Array.from({ length: N_RANKS }, (_, i) => String(N_RANKS - i));

// a1 is dark, so a square is light when file index + rank is even (h1 and a8 light)
const squares = ranksTopToBottom.flatMap((rank) =>
  files.map((file, fIdx) => ({
    id: `${file}${rank}`,
    file,
    rank,
    fill: (fIdx + Number(rank)) % 2 === 0 ? SQUARE_COLOR.light : SQUARE_COLOR.dark,
  })),
);

const TITLE = "chessboard-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${squares.length} squares (${files.length}×${ranksTopToBottom.length}) · Algebraic notation (${files[0]}–${files[files.length - 1]}, ${ranksTopToBottom[ranksTopToBottom.length - 1]}–${ranksTopToBottom[0]})`;

function BoardLayer() {
  const xScale = useXScale("file");
  const yScale = useYScale("rank");
  const { left, top, width, height } = useDrawingArea();
  const cellW = xScale.bandwidth();
  const cellH = yScale.bandwidth();

  return (
    <g>
      {squares.map((sq) => (
        <rect
          key={sq.id}
          x={xScale(sq.file)}
          y={yScale(sq.rank)}
          width={cellW}
          height={cellH}
          fill={sq.fill}
          stroke={t.pageBg}
          strokeWidth={1.5}
        />
      ))}
      <rect
        x={left}
        y={top}
        width={width}
        height={height}
        fill="none"
        stroke={t.ink}
        strokeWidth={3}
      />
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const availH = height - HEADER_H;
  const containerSide = Math.min(width, availH);

  return (
    <div
      style={{
        width,
        height,
        background: t.pageBg,
        fontFamily: "Inter, system-ui, sans-serif",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <div
        style={{
          height: HEADER_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 6,
          paddingTop: 6,
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink }}>
          {TITLE}
        </div>
        <div style={{ fontSize: 15, color: t.inkSoft }}>{SUBTITLE}</div>
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
            data: files,
            categoryGapRatio: 0,
            height: AXIS_SIZE,
            disableLine: true,
            disableTicks: true,
            tickLabelStyle: {
              fontSize: 16,
              fontWeight: 600,
              fill: t.inkSoft,
            },
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
            tickLabelStyle: {
              fontSize: 16,
              fontWeight: 600,
              fill: t.inkSoft,
            },
          },
        ]}
      >
        <BoardLayer />
        <ChartsXAxis axisId="file" />
        <ChartsYAxis axisId="rank" />
      </ChartsContainer>
    </div>
  );
}
