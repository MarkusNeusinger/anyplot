// anyplot.ai
// marimekko-basic: Basic Marimekko Chart
// Library: muix 7.29.1 | JavaScript 22.23.1
// Quality: 94/100 | Created: 2026-07-24

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsText } from "@mui/x-charts/ChartsText";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "marimekko-basic · javascript · muix · anyplot.ai";
const Y_AXIS_LABEL = "Share within column (%)";
const TITLE_HEIGHT = 56;
const LEGEND_HEIGHT = 44;
const Y_AXIS_WIDTH = 86;
const MARGIN = { top: 20, right: 32, bottom: 72, left: 16 };
const MIN_LABEL_SHARE = 0.08;
const MIN_LABEL_WIDTH_PX = 64;

// Columns: set these to your data's column names
const REGION = "Region"; // role: x_category
const PRODUCT = "Product line"; // role: y_category
const REVENUE = "Revenue ($M)"; // role: value

// Data: replace this block with your own records
const data: Array<Record<string, string | number>> = [
  { [REGION]: "North", [PRODUCT]: "Electronics", [REVENUE]: 42 },
  { [REGION]: "North", [PRODUCT]: "Apparel", [REVENUE]: 18 },
  { [REGION]: "North", [PRODUCT]: "Home Goods", [REVENUE]: 15 },
  { [REGION]: "North", [PRODUCT]: "Grocery", [REVENUE]: 25 },
  { [REGION]: "South", [PRODUCT]: "Electronics", [REVENUE]: 20 },
  { [REGION]: "South", [PRODUCT]: "Apparel", [REVENUE]: 22 },
  { [REGION]: "South", [PRODUCT]: "Home Goods", [REVENUE]: 10 },
  { [REGION]: "South", [PRODUCT]: "Grocery", [REVENUE]: 8 },
  { [REGION]: "East", [PRODUCT]: "Electronics", [REVENUE]: 55 },
  { [REGION]: "East", [PRODUCT]: "Apparel", [REVENUE]: 30 },
  { [REGION]: "East", [PRODUCT]: "Home Goods", [REVENUE]: 25 },
  { [REGION]: "East", [PRODUCT]: "Grocery", [REVENUE]: 40 },
  { [REGION]: "West", [PRODUCT]: "Electronics", [REVENUE]: 15 },
  { [REGION]: "West", [PRODUCT]: "Apparel", [REVENUE]: 12 },
  { [REGION]: "West", [PRODUCT]: "Home Goods", [REVENUE]: 8 },
  { [REGION]: "West", [PRODUCT]: "Grocery", [REVENUE]: 5 },
  { [REGION]: "Central", [PRODUCT]: "Electronics", [REVENUE]: 30 },
  { [REGION]: "Central", [PRODUCT]: "Apparel", [REVENUE]: 25 },
  { [REGION]: "Central", [PRODUCT]: "Home Goods", [REVENUE]: 20 },
  { [REGION]: "Central", [PRODUCT]: "Grocery", [REVENUE]: 15 },
];

// Plot: reads only data and the constants above
const unitMatch = REVENUE.match(/\(([^)]+)\)/);
const rawUnit = unitMatch ? unitMatch[1] : "";
const unitPrefix = rawUnit.startsWith("$") ? "$" : "";
const unitSuffix = rawUnit.startsWith("$") ? rawUnit.slice(1) : rawUnit;

const regions: string[] = [];
const products: string[] = [];
for (let i = 0; i < data.length; i++) {
  const reg = String(data[i][REGION]);
  const prod = String(data[i][PRODUCT]);
  if (!regions.includes(reg)) regions.push(reg);
  if (!products.includes(prod)) products.push(prod);
}

// Compute luminance-based fixed text color for each product category color
const productColors: string[] = [];
const productTextColors: string[] = [];
for (let i = 0; i < products.length; i++) {
  const hex = t.palette[i];
  productColors.push(hex);
  const c = hex.replace("#", "");
  const r = parseInt(c.slice(0, 2), 16) / 255;
  const g = parseInt(c.slice(2, 4), 16) / 255;
  const b = parseInt(c.slice(4, 6), 16) / 255;
  const lum = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  productTextColors.push(lum > 0.52 ? "#1A1A17" : "#FAF8F1");
}

// Compute region totals and Marimekko layout in data percentage space (0..100)
const regionTotals = new Map<string, number>();
let grandTotal = 0;
for (let i = 0; i < data.length; i++) {
  const reg = String(data[i][REGION]);
  const val = Number(data[i][REVENUE]);
  regionTotals.set(reg, (regionTotals.get(reg) ?? 0) + val);
  grandTotal += val;
}

interface MarimekkoSegment {
  product: string;
  productIdx: number;
  value: number;
  share: number;
  y0: number;
  y1: number;
}

interface MarimekkoColumn {
  region: string;
  total: number;
  widthPct: number;
  x0: number;
  x1: number;
  segments: MarimekkoSegment[];
}

const columns: MarimekkoColumn[] = [];
let cumX = 0;
for (let r = 0; r < regions.length; r++) {
  const reg = regions[r];
  const total = regionTotals.get(reg)!;
  const widthPct = (total / grandTotal) * 100;
  const x0 = cumX;
  const x1 = cumX + widthPct;
  cumX = x1;

  // Stack bottom-to-top so first product is at the top of each column
  let cumY = 100;
  const segments: MarimekkoSegment[] = [];
  for (let p = 0; p < products.length; p++) {
    const prod = products[p];
    const matchingRow = data.find(
      (row) => String(row[REGION]) === reg && String(row[PRODUCT]) === prod,
    );
    const val = matchingRow ? Number(matchingRow[REVENUE]) : 0;
    const share = total > 0 ? val / total : 0;
    const heightPct = share * 100;
    const y1 = cumY;
    const y0 = cumY - heightPct;
    cumY = y0;
    segments.push({
      product: prod,
      productIdx: p,
      value: val,
      share,
      y0,
      y1,
    });
  }

  columns.push({
    region: reg,
    total,
    widthPct,
    x0,
    x1,
    segments,
  });
}

function MarimekkoCells() {
  const xScale = useXScale("x") as (v: number) => number;
  const yScale = useYScale("y") as (v: number) => number;
  const { top, height } = useDrawingArea();
  const bottomY = top + height;

  return (
    <g>
      {columns.map((col) => {
        const px0 = xScale(col.x0);
        const px1 = xScale(col.x1);
        const colW = px1 - px0;
        const colMidX = px0 + colW / 2;

        return (
          <g key={col.region}>
            {col.segments.map((seg) => {
              const pyTop = yScale(seg.y1);
              const pyBottom = yScale(seg.y0);
              const segH = pyBottom - pyTop;
              const showLabel = seg.share >= MIN_LABEL_SHARE && colW >= MIN_LABEL_WIDTH_PX;

              return (
                <g key={seg.product}>
                  <rect
                    x={px0}
                    y={pyTop}
                    width={colW}
                    height={segH}
                    fill={productColors[seg.productIdx]}
                    stroke={t.pageBg}
                    strokeWidth={2.5}
                  />
                  {showLabel && (
                    <ChartsText
                      x={colMidX}
                      y={pyTop + segH / 2}
                      text={`${unitPrefix}${seg.value}${unitSuffix} (${Math.round(seg.share * 100)}%)`}
                      style={{
                        fill: productTextColors[seg.productIdx],
                        fontSize: 14,
                        fontWeight: 600,
                        textAnchor: "middle",
                        dominantBaseline: "central",
                      }}
                    />
                  )}
                </g>
              );
            })}

            <ChartsText
              x={colMidX}
              y={bottomY + 24}
              text={col.region}
              style={{
                fill: t.ink,
                fontSize: 15,
                fontWeight: 600,
                textAnchor: "middle",
                dominantBaseline: "central",
              }}
            />
            <ChartsText
              x={colMidX}
              y={bottomY + 46}
              text={`${unitPrefix}${col.total}${unitSuffix} (${Math.round(col.widthPct)}%)`}
              style={{
                fill: t.inkSoft,
                fontSize: 14,
                textAnchor: "middle",
                dominantBaseline: "central",
              }}
            />
          </g>
        );
      })}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;
  const chartHeight = height - TITLE_HEIGHT - LEGEND_HEIGHT;

  return (
    <div
      style={{
        width,
        height,
        backgroundColor: t.pageBg,
        display: "flex",
        flexDirection: "column",
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      <div
        style={{
          height: TITLE_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          fontWeight: 600,
          color: t.ink,
        }}
      >
        {TITLE}
      </div>
      <div
        style={{
          height: LEGEND_HEIGHT,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 28,
        }}
      >
        {products.map((prod, idx) => (
          <div key={prod} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                width: 14,
                height: 14,
                borderRadius: 3,
                backgroundColor: productColors[idx],
                display: "inline-block",
              }}
            />
            <span style={{ fontSize: 15, color: t.ink, fontWeight: 500 }}>{prod}</span>
          </div>
        ))}
      </div>
      <ChartsContainer
        width={width}
        height={chartHeight}
        margin={MARGIN}
        skipAnimation
        series={[]}
        xAxis={[
          {
            id: "x",
            position: "none",
            scaleType: "linear",
            min: 0,
            max: 100,
          },
        ]}
        yAxis={[
          {
            id: "y",
            scaleType: "linear",
            min: 0,
            max: 100,
            width: Y_AXIS_WIDTH,
            label: Y_AXIS_LABEL,
            labelStyle: { fontSize: 16, fill: t.ink, fontWeight: 500 },
            tickLabelStyle: { fontSize: 14, fill: t.inkSoft },
            valueFormatter: (v: number) => `${v}%`,
          },
        ]}
      >
        <MarimekkoCells />
        <ChartsYAxis axisId="y" />
      </ChartsContainer>
    </div>
  );
}
