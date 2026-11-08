// anyplot.ai
// line-stock-comparison: Stock Price Comparison Chart
// Library: muix 7.29.1 | JavaScript 22.23.2
// Quality: pending | Created: 2026-08-26
import { LineChart } from "@mui/x-charts/LineChart";
import { ChartsReferenceLine } from "@mui/x-charts/ChartsReferenceLine";

const t = window.ANYPLOT_TOKENS;

// Constants
const REBASE_TO = 100; // every series is rebased to this value on its first date (the spec's definition)
const Y_PAD_SHARE = 0.06; // share of the rebased range added below and above the lines

// Columns: set these to your data's column names
const DATE = "Trading date"; // role: date
const SYMBOL = "Symbol"; // role: symbol
const PRICE = "Adjusted close (USD)"; // role: price

// Data: replace this block with your own records, one object per row
// One trading year (252 sessions, weekends skipped) of three large-cap stocks and the S&P 500 ETF.
const data = (() => {
  const sessions = 252;
  const dates = [];
  const cursor = new Date(2025, 0, 2);
  while (dates.length < sessions) {
    if (cursor.getDay() !== 0 && cursor.getDay() !== 6) dates.push(new Date(cursor));
    cursor.setDate(cursor.getDate() + 1);
  }
  const stocks = [
    { symbol: "AAPL", start: 182, drift: 0.0009, volatility: 0.016, seed: 11 },
    { symbol: "GOOGL", start: 141, drift: 0.0004, volatility: 0.019, seed: 22 },
    { symbol: "MSFT", start: 378, drift: 0.0011, volatility: 0.014, seed: 33 },
    { symbol: "SPY", start: 468, drift: 0.0005, volatility: 0.009, seed: 44 },
  ];
  return stocks.flatMap((stock) => {
    let state = stock.seed >>> 0;
    let price = stock.start;
    return dates.map((date, i) => {
      if (i > 0) {
        state = (state * 1664525 + 1013904223) >>> 0;
        price *= 1 + stock.drift + (state / 4294967296 - 0.5) * stock.volatility;
      }
      return { [DATE]: date, [SYMBOL]: stock.symbol, [PRICE]: Math.round(price * 100) / 100 };
    });
  });
})();

// Plot: reads only data and the constants above
// Dates are sorted onto one shared time axis; each symbol is rebased on its own first date.
const dateValues = [...new Set(data.map((d) => d[DATE].getTime()))].sort((a, b) => a - b);
const dates = dateValues.map((ms) => new Date(ms));
const symbols = [...new Set(data.map((d) => d[SYMBOL]))];
const lines = symbols.map((symbol, i) => {
  const rows = data.filter((d) => d[SYMBOL] === symbol).sort((a, b) => a[DATE] - b[DATE]);
  const base = rows[0][PRICE];
  const byDate = new Map(rows.map((d) => [d[DATE].getTime(), (d[PRICE] / base) * REBASE_TO]));
  return { id: `symbol-${i}`, label: symbol, color: t.palette[i], values: dateValues.map((ms) => byDate.get(ms) ?? null) };
});

const rebased = lines.flatMap((line) => line.values).filter((v) => v != null);
const yLow = Math.min(REBASE_TO, ...rebased);
const yHigh = Math.max(REBASE_TO, ...rebased);
const yPad = (yHigh - yLow) * Y_PAD_SHARE;
const formatDay = (d: Date) => d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });

const TITLE = "line-stock-comparison · javascript · muix · anyplot.ai";
const SUBTITLE = `${symbols.length} series · ${dates.length} trading days · ${formatDay(dates[0])} to ${formatDay(dates[dates.length - 1])} · ${PRICE} rebased to ${REBASE_TO}`;
const Y_LABEL = `Performance index (first date = ${REBASE_TO})`;
const HEADER_H = 80;
const LEGEND_H = 44;

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, display: "flex", flexDirection: "column" }}>
      <div style={{ height: HEADER_H, padding: "16px 40px 0 112px", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.25 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, marginTop: 6 }}>{SUBTITLE}</div>
      </div>
      <LineChart
        width={width}
        height={height - HEADER_H - LEGEND_H}
        skipAnimation
        grid={{ horizontal: true }}
        margin={{ top: 12, right: 48, bottom: 16, left: 24 }}
        xAxis={[
          {
            data: dates,
            scaleType: "time",
            tickNumber: 12,
            valueFormatter: (v: Date, context) =>
              context.location === "tick" ? v.toLocaleDateString("en-US", { month: "short", year: "numeric" }) : formatDay(v),
            label: DATE,
            height: 64,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: yLow - yPad,
            max: yHigh + yPad,
            label: Y_LABEL,
            width: 84,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={lines.map((line) => ({
          id: line.id,
          data: line.values,
          label: line.label,
          color: line.color,
          curve: "monotoneX",
          showMark: false,
          valueFormatter: (v: number | null) => (v == null ? "" : v.toFixed(1)),
        }))}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "end" },
            sx: { fontSize: 16, color: t.ink, columnGap: 3, pr: 5 },
          },
        }}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 2.5 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <ChartsReferenceLine
          y={REBASE_TO}
          label={`Start = ${REBASE_TO}`}
          labelAlign="end"
          spacing={{ x: 8, y: 8 }}
          labelStyle={{ fontSize: 14, fill: t.inkSoft }}
          lineStyle={{ stroke: t.inkSoft, strokeDasharray: "6 5", strokeWidth: 1.5 }}
        />
      </LineChart>
    </div>
  );
}
