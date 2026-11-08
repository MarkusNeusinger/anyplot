// anyplot.ai
// kagi-basic: Basic Kagi Chart
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 87/100 | Updated: 2026-11-08
import { LineChart } from "@mui/x-charts/LineChart";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const t = window.ANYPLOT_TOKENS;

// Constants
const REVERSAL_SHARE = 0.04; // a move of 4 % against the running extreme turns the line
const Y_PAD_SHARE = 0.06; // share of the price range added above and below the outermost turn
const X_PAD_LINES = 0.5; // half a column of room beside the first and the last vertical line
const YANG = "Yang: thick, rising above the previous shoulder";
const YIN = "Yin: thin, falling below the previous waist";

// Columns: set these to your data's column names
const DATE = "Trading date"; // role: date
const CLOSE = "Close (USD)"; // role: close

// Data: replace this block with your own records, one object per observation
// 240 weekday closes of a mid-cap stock from 2 Jan 2024: a random walk of daily returns
// with a mild upward drift and a daily volatility of 1.6 %.
const data = (() => {
  let state = 42;
  const rand = () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
  const records: { [DATE]: string; [CLOSE]: number }[] = [];
  const cursor = new Date(Date.UTC(2024, 0, 2));
  let price = 180;
  while (records.length < 240) {
    if (cursor.getUTCDay() % 6 !== 0) {
      if (records.length > 0) {
        const z = Math.sqrt(-2 * Math.log(Math.max(rand(), 1e-9))) * Math.cos(2 * Math.PI * rand());
        price *= 1 + 0.0006 + 0.016 * z;
      }
      records.push({ [DATE]: cursor.toISOString().slice(0, 10), [CLOSE]: Math.round(price * 100) / 100 });
    }
    cursor.setUTCDate(cursor.getUTCDate() + 1);
  }
  return records;
})();

// Plot: reads only data and the constants above
const rows = [...data].sort((a, b) => Date.parse(a[DATE]) - Date.parse(b[DATE]));
const closes = rows.map((d) => d[CLOSE]).filter((v) => v != null);

// Turning points: the line extends while the price keeps its direction and turns only
// after a move of REVERSAL_SHARE against the running extreme
const turns = [closes[0]];
let direction = 0;
let extreme = closes[0];
for (const price of closes.slice(1)) {
  if (direction === 0) {
    const change = (price - extreme) / extreme;
    if (Math.abs(change) >= REVERSAL_SHARE) {
      direction = Math.sign(change);
      extreme = price;
      turns.push(price);
    }
  } else if ((price - extreme) * direction > 0) {
    extreme = price;
    turns[turns.length - 1] = price;
  } else if (Math.abs(price - extreme) / extreme >= REVERSAL_SHARE) {
    direction = -direction;
    extreme = price;
    turns.push(price);
  }
}
const lineCount = turns.length - 1;

// Path: vertical line k runs from turn k to turn k + 1 in column k, and a horizontal
// shoulder or waist joins it to column k + 1. The line turns yang where a rise passes the
// previous shoulder and yin where a fall passes the previous waist, so a vertical that
// breaks out is split at that level.
const pathX = [0];
const pathY = [turns[0]];
const edgeYang: boolean[] = [];
let yang = turns[1] > turns[0];
let priorShoulder: number | null = null;
let priorWaist: number | null = null;
for (let k = 0; k < lineCount; k += 1) {
  const from = turns[k];
  const to = turns[k + 1];
  const rising = to > from;
  const level = rising ? priorShoulder : priorWaist;
  if (level != null && yang !== rising && (rising ? to > level : to < level)) {
    pathX.push(k);
    pathY.push(level);
    edgeYang.push(yang);
    yang = rising;
  }
  pathX.push(k);
  pathY.push(to);
  edgeYang.push(yang);
  if (rising) priorShoulder = to;
  else priorWaist = to;
  if (k < lineCount - 1) {
    pathX.push(k + 1);
    pathY.push(to);
    edgeYang.push(yang);
  }
}

// One series per state; a vertex carries a value when an edge of that state touches it, so
// the thick and the thin line meet at every change
const yangY = pathY.map((y, i) => (edgeYang[i - 1] === true || edgeYang[i] === true ? y : null));
const yinY = pathY.map((y, i) => (edgeYang[i - 1] === false || edgeYang[i] === false ? y : null));

const yLow = Math.min(...turns);
const yHigh = Math.max(...turns);
const yPad = (yHigh - yLow) * Y_PAD_SHARE;

const dateFormat = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });
const TITLE = "kagi-basic · javascript · muix · anyplot.ai";
const SUBTITLE =
  `${closes.length} closes, ${dateFormat.format(new Date(rows[0][DATE]))} – ` +
  `${dateFormat.format(new Date(rows[rows.length - 1][DATE]))} · reversal amount ${REVERSAL_SHARE * 100} % · ` +
  `${lineCount} vertical lines`;
const HEADER_H = 84;
const LEGEND_H = 48;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <Box sx={{ width, height, bgcolor: t.pageBg, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <Box sx={{ height: HEADER_H, pt: "14px", textAlign: "center", boxSizing: "border-box" }}>
        <Typography sx={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.3 }}>{TITLE}</Typography>
        <Typography sx={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.6 }}>{SUBTITLE}</Typography>
      </Box>
      <LineChart
        width={width}
        height={height - HEADER_H - LEGEND_H}
        skipAnimation
        grid={{ horizontal: true }}
        margin={{ top: 16, right: 40, bottom: 8, left: 20 }}
        axisHighlight={{ x: "none" }}
        series={[
          {
            id: "yang",
            data: yangY,
            label: YANG,
            color: t.palette[0],
            curve: "linear",
            showMark: false,
            labelMarkType: "line",
          },
          {
            id: "yin",
            data: yinY,
            label: YIN,
            color: t.palette[4],
            curve: "linear",
            showMark: false,
            labelMarkType: "line",
          },
        ]}
        xAxis={[
          {
            data: pathX,
            scaleType: "linear",
            min: -X_PAD_LINES,
            max: lineCount - 1 + X_PAD_LINES,
            tickMinStep: 1,
            valueFormatter: (v: number) => String(Math.round(v) + 1),
            label: "Kagi line (one column per reversal)",
            height: 64,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: yLow - yPad,
            max: yHigh + yPad,
            width: 84,
            label: CLOSE,
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "bottom", horizontal: "center" },
            sx: {
              fontSize: 15,
              color: t.ink,
              gap: "36px",
              pt: "8px",
              "& .MuiChartsLabelMark-line": { width: 28, height: 10 },
              '& [data-series="yang"] path': { strokeWidth: 6 },
              '& [data-series="yin"] path': { strokeWidth: 2 },
            },
          },
        }}
        sx={{
          '& .MuiLineChart-line[data-series="yang"]': { strokeWidth: 6 },
          '& .MuiLineChart-line[data-series="yin"]': { strokeWidth: 2 },
          "& .MuiChartsGrid-line": { stroke: t.grid },
        }}
      />
    </Box>
  );
}
