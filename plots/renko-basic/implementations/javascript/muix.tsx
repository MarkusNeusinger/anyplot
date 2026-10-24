// anyplot.ai
// renko-basic: Basic Renko Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: 92/100 | Created: 2026-09-02

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsXAxis } from "@mui/x-charts/ChartsXAxis";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsGrid } from "@mui/x-charts/ChartsGrid";
import { useXScale, useYScale } from "@mui/x-charts/hooks";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "SolarGrid Energy Daily Close · renko-basic · javascript · muix · anyplot.ai";
const X_TITLE = "Brick Sequence (estimated dates)";
const BULLISH_LABEL = "Bullish brick (price up)";
const BEARISH_LABEL = "Bearish brick (price down)";
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// Columns: set these to your data's column names
const DATE = "Date"; // role: date
const CLOSE = "Price (USD)"; // role: close

// Data: replace this block with your own records
const BRICK_SIZE = 1.5;
const REGIMES = [
  { days: 60, drift: 0.34 },
  { days: 50, drift: 0.0 },
  { days: 70, drift: -0.3 },
  { days: 60, drift: 0.26 },
];

let seed = 42;
const data = [{ [DATE]: "2024-01-02", [CLOSE]: 64.0 }];
let currentDate = new Date(Date.UTC(2024, 0, 2));
for (const regime of REGIMES) {
  for (let d = 0; d < regime.days; d += 1) {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    const noise = (seed / 0x7fffffff - 0.5) * 1.6;
    const prev = Number(data[data.length - 1][CLOSE]);
    const nextPrice = Math.max(prev + regime.drift + noise, 5);
    currentDate = new Date(currentDate.getTime() + 86400000);
    const iso = currentDate.toISOString().slice(0, 10);
    data.push({ [DATE]: iso, [CLOSE]: nextPrice });
  }
}

// Plot: reads only data and the constants above
const sortedRows = [...data].sort((a, b) => String(a[DATE]).localeCompare(String(b[DATE])));
const bricks = [];
let anchor = Math.round(Number(sortedRows[0][CLOSE]) / BRICK_SIZE) * BRICK_SIZE;
for (let i = 1; i < sortedRows.length; i += 1) {
  const price = Number(sortedRows[i][CLOSE]);
  const rawDate = new Date(`${sortedRows[i][DATE]}T00:00:00Z`);
  const dateLabel = `${MONTHS[rawDate.getUTCMonth()]} ${rawDate.getUTCDate()}`;
  while (price - anchor >= BRICK_SIZE) {
    bricks.push({ base: anchor, direction: 1, dateLabel });
    anchor += BRICK_SIZE;
  }
  while (anchor - price >= BRICK_SIZE) {
    anchor -= BRICK_SIZE;
    bricks.push({ base: anchor, direction: -1, dateLabel });
  }
}

const firstRawDate = new Date(`${sortedRows[0][DATE]}T00:00:00Z`);
const lastRawDate = new Date(`${sortedRows[sortedRows.length - 1][DATE]}T00:00:00Z`);
const startDateStr = `${MONTHS[firstRawDate.getUTCMonth()]} ${firstRawDate.getUTCDate()}`;
const endDateStr = `${MONTHS[lastRawDate.getUTCMonth()]} ${lastRawDate.getUTCDate()}`;

const brickLabels = bricks.map((_, i) => `${i + 1}`);
const yMin = Math.min(...bricks.map((b) => b.base));
const yMax = Math.max(...bricks.map((b) => b.base + BRICK_SIZE));
const yPad = (yMax - yMin) * 0.08;
const tickEvery = Math.ceil(bricks.length / 10);

function Bricks() {
  const xScale = useXScale("x");
  const yScale = useYScale("y");
  const bw = xScale.bandwidth();
  const brickWidth = bw * 0.78;

  return (
    <g>
      {bricks.map((brick, i) => {
        const cx = xScale(brickLabels[i]) + bw / 2;
        const color = brick.direction === 1 ? t.palette[0] : t.palette[4];
        const yTop = yScale(brick.base + BRICK_SIZE);
        const yBottom = yScale(brick.base);
        const brickHeight = yBottom - yTop;
        const cy = (yTop + yBottom) / 2;
        const markSize = Math.min(brickWidth, brickHeight) * 0.4;
        const showMark = markSize >= 6;
        const points =
          brick.direction === 1
            ? `${cx},${cy - markSize / 2} ${cx - markSize / 2},${cy + markSize / 2} ${cx + markSize / 2},${cy + markSize / 2}`
            : `${cx},${cy + markSize / 2} ${cx - markSize / 2},${cy - markSize / 2} ${cx + markSize / 2},${cy - markSize / 2}`;
        return (
          <g key={i}>
            <rect
              x={cx - brickWidth / 2}
              y={yTop}
              width={brickWidth}
              height={brickHeight}
              fill={color}
              stroke={t.ink}
              strokeOpacity={0.3}
              strokeWidth={1}
            />
            {showMark && <polygon points={points} fill={t.ink} fillOpacity={0.8} />}
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const W = window.ANYPLOT_SIZE.width;
  const H = window.ANYPLOT_SIZE.height;
  const TITLE_H = 96;
  const LEGEND_H = 52;
  const chartH = H - TITLE_H - LEGEND_H;

  const titleSize = TITLE.length > 67 ? Math.round((22 * 67) / TITLE.length) : 22;
  const subtitle = `${startDateStr} – ${endDateStr} · $${BRICK_SIZE.toFixed(2)} brick size · ${bricks.length} bricks`;

  const legendItems = [
    { label: BULLISH_LABEL, color: t.palette[0] },
    { label: BEARISH_LABEL, color: t.palette[4] },
  ];

  return (
    <Box
      sx={{
        width: W,
        height: H,
        bgcolor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        boxSizing: "border-box",
      }}
    >
      <Box
        sx={{
          height: TITLE_H,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "6px",
        }}
      >
        <Typography sx={{ color: t.ink, fontSize: titleSize, fontWeight: 600 }}>{TITLE}</Typography>
        <Typography sx={{ color: t.inkSoft, fontSize: 13, fontWeight: 400, letterSpacing: "0.03em" }}>
          {subtitle}
        </Typography>
      </Box>

      <ChartsContainer
        width={W}
        height={chartH}
        skipAnimation
        series={[]}
        xAxis={[
          {
            id: "x",
            scaleType: "band",
            data: brickLabels,
            height: 64,
            label: X_TITLE,
            valueFormatter: (label) => bricks[Number(label) - 1].dateLabel,
            tickLabelInterval: (_value, index) => index % tickEvery === 0,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 15, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            id: "y",
            min: yMin - yPad,
            max: yMax + yPad,
            width: 88,
            label: CLOSE,
            valueFormatter: (v) => `$${v.toFixed(2)}`,
            tickLabelStyle: { fontSize: 13, fill: t.inkSoft },
            labelStyle: { fontSize: 15, fill: t.ink },
          },
        ]}
        margin={{ top: 24, bottom: 16, left: 24, right: 32 }}
        sx={{
          "& .MuiChartsAxis-line": { stroke: t.inkSoft, strokeOpacity: 0.2 },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      >
        <ChartsGrid horizontal />
        <Bricks />
        <ChartsXAxis axisId="x" />
        <ChartsYAxis axisId="y" />
      </ChartsContainer>

      <Box sx={{ height: LEGEND_H, display: "flex", alignItems: "center", justifyContent: "center", gap: "16px" }}>
        {legendItems.map((item) => (
          <Box
            key={item.label}
            sx={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "6px 16px",
              borderRadius: "999px",
              border: `1px solid ${t.grid}`,
              bgcolor: t.elevatedBg,
            }}
          >
            <Box sx={{ width: 10, height: 10, borderRadius: "2px", bgcolor: item.color }} />
            <Typography sx={{ color: t.inkSoft, fontSize: 13, fontWeight: 500 }}>{item.label}</Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
}
