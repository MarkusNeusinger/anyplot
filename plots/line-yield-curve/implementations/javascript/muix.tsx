// anyplot.ai
// line-yield-curve: Yield Curve (Interest Rate Term Structure)
// Library: muix 7.29.1 | JavaScript 22.23.3
// Quality: 87/100 | Updated: 2026-10-09
import { LineChart } from "@mui/x-charts/LineChart";
import { useDrawingArea, useXScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const X_PAD_SHARE = 0.04; // share of the log maturity range added on both sides so the end markers stay whole
const Y_PAD_SHARE = 0.12; // share of the yield range added below and above the curves

// Columns: set these to your data's column names
const MATURITY = "Maturity"; // role: maturity
const MATURITY_YEARS = "Maturity (years)"; // role: maturity_years
const YIELD = "Yield (%)"; // role: yield_pct
const DATE = "Curve date"; // role: date

// Data: replace this block with your own records, one object per row
// Approximate U.S. Treasury par yields on three dates: the early-1990s recovery, the dot-com peak, pre-crisis 2007.
const data = (() => {
  const maturities = [
    ["1M", 0.083], ["3M", 0.25], ["6M", 0.5], ["1Y", 1], ["2Y", 2], ["3Y", 3],
    ["5Y", 5], ["7Y", 7], ["10Y", 10], ["20Y", 20], ["30Y", 30],
  ];
  const curves = {
    "1993-06-15": [3.0, 3.1, 3.2, 3.4, 3.9, 4.4, 5.2, 5.8, 5.9, 6.6, 6.8],
    "2000-03-15": [5.7, 5.9, 6.1, 6.3, 6.5, 6.4, 6.3, 6.3, 6.2, 6.3, 5.9],
    "2007-01-16": [5.2, 5.2, 5.1, 5.0, 4.8, 4.7, 4.7, 4.8, 4.8, 5.0, 4.9],
  };
  return Object.entries(curves).flatMap(([date, yields]) =>
    maturities.map(([label, years], i) => ({ [MATURITY]: label, [MATURITY_YEARS]: years, [YIELD]: yields[i], [DATE]: date })),
  );
})();

// Plot: reads only data and the constants above
const unit = YIELD.match(/\(([^)]+)\)/)?.[1] ?? "";
const dates = [...new Set(data.map((d) => d[DATE]))];
const maturityYears = [...new Set(data.map((d) => d[MATURITY_YEARS]))].sort((a, b) => a - b);
const labelByYears = new Map(data.map((d) => [d[MATURITY_YEARS], d[MATURITY]]));

// Shape of each curve by rule: inverted when its shortest maturity yields more than its longest,
// humped when an interior maturity tops the long end, normal otherwise
const curves = dates.map((date, i) => {
  const rows = data.filter((d) => d[DATE] === date).sort((a, b) => a[MATURITY_YEARS] - b[MATURITY_YEARS]);
  const ys = rows.map((d) => d[YIELD]);
  const shape = ys[0] > ys[ys.length - 1] ? "inverted" : Math.max(...ys.slice(1, -1)) > ys[ys.length - 1] ? "humped" : "normal";
  return {
    id: `curve-${i}`,
    label: `${date} · ${shape}`,
    color: t.palette[i],
    rows,
    ys,
    shape,
    values: maturityYears.map((m) => rows.find((d) => d[MATURITY_YEARS] === m)?.[YIELD] ?? null),
  };
});

// Inversion region of an inverted curve: from its shortest maturity down to its trough
const inversions = curves
  .filter((c) => c.shape === "inverted")
  .map((c) => {
    const trough = c.ys.lastIndexOf(Math.min(...c.ys));
    const first = c.rows[0];
    const lastRow = c.rows[c.rows.length - 1];
    return {
      id: c.id,
      from: first[MATURITY_YEARS],
      to: c.rows[trough][MATURITY_YEARS],
      text: `Inversion on ${c.rows[0][DATE]}: ${first[MATURITY]} at ${first[YIELD]}${unit} above ${lastRow[MATURITY]} at ${lastRow[YIELD]}${unit}`,
    };
  });

const allYields = data.map((d) => d[YIELD]).filter((v) => v != null);
const yLow = Math.min(...allYields);
const yHigh = Math.max(...allYields);
const yPad = (yHigh - yLow) * Y_PAD_SHARE;
const xFactor = (maturityYears[maturityYears.length - 1] / maturityYears[0]) ** X_PAD_SHARE;

const TITLE = "U.S. Treasury Yield Curves · line-yield-curve · javascript · muix · anyplot.ai";
const SUBTITLE = `${curves.length} curves × ${maturityYears.length} maturities, ${labelByYears.get(maturityYears[0])} to ${labelByYears.get(maturityYears[maturityYears.length - 1])} · maturity on a log scale`;
const HEADER_H = 80;
const LEGEND_H = 44;

function InversionBands() {
  const xScale = useXScale();
  const { top, height } = useDrawingArea();
  return (
    <g pointerEvents="none">
      {inversions.map((band, i) => (
        <g key={band.id}>
          <rect
            x={xScale(band.from)}
            y={top}
            width={xScale(band.to) - xScale(band.from)}
            height={height}
            fill={t.inkSoft}
            fillOpacity={0.1}
          />
          <text
            x={(xScale(band.from) + xScale(band.to)) / 2}
            y={top + 26 + i * 22}
            textAnchor="middle"
            fontSize={15}
            fontWeight={500}
            fill={t.ink}
          >
            {band.text}
          </text>
        </g>
      ))}
    </g>
  );
}

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
            data: maturityYears,
            scaleType: "log",
            min: maturityYears[0] / xFactor,
            max: maturityYears[maturityYears.length - 1] * xFactor,
            tickInterval: maturityYears,
            valueFormatter: (v: number) => labelByYears.get(v) ?? "",
            label: MATURITY,
            height: 64,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        yAxis={[
          {
            min: yLow - yPad,
            max: yHigh + yPad,
            label: YIELD,
            width: 76,
            tickLabelStyle: { fontSize: 15, fill: t.inkSoft },
            labelStyle: { fontSize: 16, fill: t.ink },
          },
        ]}
        series={curves.map((c) => ({
          id: c.id,
          data: c.values,
          label: c.label,
          color: c.color,
          curve: "linear",
          showMark: true,
          shape: "circle",
          valueFormatter: (v: number | null) => (v == null ? "" : `${v.toFixed(2)}${unit}`),
        }))}
        slotProps={{
          legend: {
            direction: "horizontal",
            position: { vertical: "top", horizontal: "end" },
            sx: { fontSize: 16, color: t.ink, columnGap: 3, pr: 5 },
          },
        }}
        sx={{
          "& .MuiLineChart-line": { strokeWidth: 3 },
          "& .MuiLineChart-mark": { strokeWidth: 2.5 },
          "& .MuiChartsAxis-line": { stroke: t.inkSoft },
          "& .MuiChartsAxis-tick": { stroke: t.inkSoft },
          "& .MuiChartsGrid-line": { stroke: t.grid, strokeWidth: 1 },
        }}
      >
        <InversionBands />
      </LineChart>
    </div>
  );
}
