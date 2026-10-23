// anyplot.ai
// chessboard-basic: Chess Board Grid Visualization
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-09-01
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

// Columns: set these to your data's column names
const FILE = "File"; // role: x
const RANK = "Rank"; // role: y
const TONE = "Square tone"; // role: color

// Data: replace this block with your own records, one object per row
const data = (() => {
  const files = ["a", "b", "c", "d", "e", "f", "g", "h"];
  const rows: { [key: string]: string | number }[] = [];
  for (let r = 8; r >= 1; r -= 1) {
    for (let fIdx = 0; fIdx < files.length; fIdx += 1) {
      const isLight = (fIdx + r - 1) % 2 === 1;
      rows.push({
        [FILE]: files[fIdx],
        [RANK]: r,
        [TONE]: isLight ? "Light" : "Dark",
      });
    }
  }
  return rows;
})();

// Plot: reads only data and the constants above
const files = Array.from(new Set(data.map((d) => String(d[FILE]))));
const ranksTopToBottom = Array.from(new Set(data.map((d) => Number(d[RANK]))))
  .sort((a, b) => b - a)
  .map((r) => String(r));
const tones = Array.from(new Set(data.map((d) => String(d[TONE]))));
const toneColors: { [key: string]: string } = {
  [tones[0]]: t.amber,
  [tones[1] ?? ""]: t.palette[3],
};

const squares = data.map((d) => ({
  id: `${String(d[FILE])}${String(d[RANK])}`,
  file: String(d[FILE]),
  rank: String(d[RANK]),
  tone: String(d[TONE]),
  fill: toneColors[String(d[TONE])] ?? t.palette[3],
}));

const TITLE = "chessboard-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${squares.length} squares (${files.length}×${ranksTopToBottom.length}) · Algebraic notation (${files[0]}–${files[files.length - 1]}, ${ranksTopToBottom[ranksTopToBottom.length - 1]}–${ranksTopToBottom[0]})`;

function BoardLayer() {
  const xScale = useXScale("file") as unknown as {
    (v: string): number | undefined;
    bandwidth?: () => number;
  };
  const yScale = useYScale("rank") as unknown as {
    (v: string): number | undefined;
    bandwidth?: () => number;
  };
  const { left, top, width, height } = useDrawingArea();
  if (!xScale || !yScale || !xScale.bandwidth || !yScale.bandwidth) return null;

  const cellW = xScale.bandwidth();
  const cellH = yScale.bandwidth();

  return (
    <g>
      {squares.map((sq) => {
        const x = xScale(sq.file);
        const y = yScale(sq.rank);
        if (x === undefined || y === undefined) return null;
        return (
          <rect
            key={sq.id}
            x={x}
            y={y}
            width={cellW}
            height={cellH}
            fill={sq.fill}
            stroke={t.pageBg}
            strokeWidth={1.5}
          />
        );
      })}
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
