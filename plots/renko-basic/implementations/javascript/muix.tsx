// anyplot.ai
// renko-basic: Basic Renko Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-09-02

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const BRICK_SHARE = 0.055; // brick size as a share of the close-price range, rounded to two significant digits
const PAD_SHARE = 0.06; // price-axis padding, share of the brick span
const BRICK_WIDTH_SHARE = 0.78; // brick width as a share of its column; the rest is the gap
const TICK_COUNT = 10; // about this many brick-index labels on the x axis
const DIRECTIONS = [
  { sign: 1, label: "Bullish brick (price up)", color: t.palette[0] },
  { sign: -1, label: "Bearish brick (price down)", color: t.palette[4] },
]; // finance up/down semantics: brand green up, the palette's red down
const TITLE_H = 48;
const SUBTITLE_H = 28;
const LEGEND_H = 44;

// Columns: set these to your data's column names
const DATE = "Date"; // role: date
const CLOSE = "Close (USD)"; // role: close

// Data: replace this block with your own records, one object per row
// Daily closes of a fictional solar-energy stock through four regimes (uptrend, consolidation,
// downtrend, recovery), 241 days from 2 Jan 2024, from a fixed-seed LCG
const data = (() => {
  let seed = 42;
  const rand = () => {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  };
  const drifts = [...Array(60).fill(0.34), ...Array(50).fill(0), ...Array(70).fill(-0.3), ...Array(60).fill(0.26)];
  const rows = [{ [DATE]: new Date(2024, 0, 2), [CLOSE]: 64 }];
  drifts.forEach((drift, i) => {
    const prev = rows[rows.length - 1][CLOSE];
    rows.push({ [DATE]: new Date(2024, 0, 3 + i), [CLOSE]: Math.max(prev + drift + (rand() - 0.5) * 1.6, 5) });
  });
  return rows.map((r) => ({ ...r, [CLOSE]: Math.round(r[CLOSE] * 100) / 100 }));
})();

// Plot: reads only data and the constants above
const rows = data.filter((d) => Number.isFinite(d[CLOSE])).sort((a, b) => a[DATE] - b[DATE]);
const closes = rows.map((d) => d[CLOSE]);
const brickSize = Number(((Math.max(...closes) - Math.min(...closes)) * BRICK_SHARE).toPrecision(2));

// A brick is drawn each time the close moves one full brick above the last brick's top or below
// its bottom, so a reversal starts one brick beyond the previous brick, never level with it
const bricks = [];
let bottom = Math.round(closes[0] / brickSize) * brickSize;
let top = bottom;
rows.slice(1).forEach((d) => {
  while (d[CLOSE] >= top + brickSize) {
    bricks.push({ base: top, sign: 1, date: d[DATE] });
    bottom = top;
    top += brickSize;
  }
  while (d[CLOSE] <= bottom - brickSize) {
    bricks.push({ base: bottom - brickSize, sign: -1, date: d[DATE] });
    top = bottom;
    bottom -= brickSize;
  }
});
const columns = bricks.map((_, i) => i + 1);
const low = Math.min(...bricks.map((b) => b.base));
const high = Math.max(...bricks.map((b) => b.base)) + brickSize;
const pad = (high - low) * PAD_SHARE;
const tickEvery = Math.max(1, Math.ceil(bricks.length / TICK_COUNT));

const unit = CLOSE.match(/\(([^)]+)\)/)?.[1] ?? "";
const dateFormat = { month: "short", day: "numeric", year: "numeric" };
const firstDate = rows[0][DATE].toLocaleDateString("en-US", dateFormat);
const lastDate = rows[rows.length - 1][DATE].toLocaleDateString("en-US", dateFormat);
const TITLE = "SolarGrid Energy · renko-basic · javascript · muix · anyplot.ai";
const SUBTITLE = `${rows.length} closes ${firstDate} – ${lastDate} · brick size ${brickSize} ${unit} · ${bricks.length} bricks`;

function Bricks() {
  const xScale = useXScale();
  const yScale = useYScale();
  const column = xScale.bandwidth();
  const width = column * BRICK_WIDTH_SHARE;

  return (
    <g>
      {bricks.map((b, i) => (
        <rect
          key={i}
          x={xScale(columns[i]) + (column - width) / 2}
          y={yScale(b.base + brickSize)}
          width={width}
          height={yScale(b.base) - yScale(b.base + brickSize)}
          fill={DIRECTIONS.find((dir) => dir.sign === b.sign).color}
        />
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, display: "flex", alignItems: "flex-end", justifyContent: "center", fontSize: 22, fontWeight: 600, color: t.ink }}>
        {TITLE}
      </div>
      <div style={{ height: SUBTITLE_H, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15, color: t.inkSoft }}>
        {SUBTITLE}
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_H - SUBTITLE_H - LEGEND_H}
        skipAnimation
        series={[]}
        margin={{ top: 16, right: 40, bottom: 8, left: 16 }}
        xAxis={[
          {
            scaleType: "band",
            data: columns,
            label: "Brick sequence (date the brick formed)",
            height: 64,
            valueFormatter: (n) => bricks[n - 1].date.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
            tickLabelInterval: (_value, index) => index % tickEvery === 0,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        yAxis={[
          {
            scaleType: "linear",
            min: low - pad,
            max: high + pad,
            label: CLOSE,
            width: 76,
            labelStyle: { fontSize: 16, fill: t.ink },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
          },
        ]}
        sx={{
          "& .MuiChartsGrid-line": { stroke: t.grid },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
        }}
      >
        <ChartsGrid horizontal />
        <Bricks />
        <ChartsXAxis />
        <ChartsYAxis />
      </ChartsContainer>
      <div style={{ height: LEGEND_H, display: "flex", alignItems: "center", justifyContent: "center", gap: 32 }}>
        {DIRECTIONS.map((dir) => (
          <div key={dir.sign} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 15, color: t.ink }}>
            <div style={{ width: 16, height: 16, borderRadius: 2, background: dir.color }} />
            {dir.label}
          </div>
        ))}
      </div>
    </div>
  );
}
