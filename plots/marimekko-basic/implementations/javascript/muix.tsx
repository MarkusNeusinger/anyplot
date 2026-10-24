// anyplot.ai
// marimekko-basic: Marimekko Chart
// Library: muix 9.2.1 | JavaScript 22.23.1
// Quality: 90/100 | Created: 2026-08-03

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { ChartsYAxis } from "@mui/x-charts/ChartsYAxis";
import { ChartsText } from "@mui/x-charts/ChartsText";
import { useDrawingArea, useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const TITLE = "marimekko-basic · javascript · muix · anyplot.ai";
const TITLE_HEIGHT = 56;
const LEGEND_HEIGHT = 44;
const Y_AXIS_WIDTH = 86;
const MARGIN = { top: 20, right: 32, bottom: 72, left: 16 };
const MIN_LABEL_SHARE = 0.08;
const MIN_LABEL_WIDTH_PX = 64;

// Data
const REGION_COL = "Region";
const PRODUCT_COL = "Product Category";
const REVENUE_COL = "Revenue ($M)";

const DATA: Array<Record<string, string | number>> = [
  { [REGION_COL]: "North", [PRODUCT_COL]: "Electronics", [REVENUE_COL]: 120 },
  { [REGION_COL]: "North", [PRODUCT_COL]: "Apparel", [REVENUE_COL]: 80 },
  { [REGION_COL]: "North", [PRODUCT_COL]: "Home & Garden", [REVENUE_COL]: 60 },
  { [REGION_COL]: "North", [PRODUCT_COL]: "Sports", [REVENUE_COL]: 40 },
  { [REGION_COL]: "South", [PRODUCT_COL]: "Electronics", [REVENUE_COL]: 60 },
  { [REGION_COL]: "South", [PRODUCT_COL]: "Apparel", [REVENUE_COL]: 70 },
  { [REGION_COL]: "South", [PRODUCT_COL]: "Home & Garden", [REVENUE_COL]: 40 },
  { [REGION_COL]: "South", [PRODUCT_COL]: "Sports", [REVENUE_COL]: 30 },
  { [REGION_COL]: "East", [PRODUCT_COL]: "Electronics", [REVENUE_COL]: 150 },
  { [REGION_COL]: "East", [PRODUCT_COL]: "Apparel", [REVENUE_COL]: 90 },
  { [REGION_COL]: "East", [PRODUCT_COL]: "Home & Garden", [REVENUE_COL]: 70 },
  { [REGION_COL]: "East", [PRODUCT_COL]: "Sports", [REVENUE_COL]: 40 },
  { [REGION_COL]: "West", [PRODUCT_COL]: "Electronics", [REVENUE_COL]: 50 },
  { [REGION_COL]: "West", [PRODUCT_COL]: "Apparel", [REVENUE_COL]: 45 },
  { [REGION_COL]: "West", [PRODUCT_COL]: "Home & Garden", [REVENUE_COL]: 35 },
  { [REGION_COL]: "West", [PRODUCT_COL]: "Sports", [REVENUE_COL]: 20 },
];

// Derive regions and product categories in order of first appearance
const regions: string[] = [];
const products: string[] = [];
for (let i = 0; i < DATA.length; i++) {
  const reg = String(DATA[i][REGION_COL]);
  const prod = String(DATA[i][PRODUCT_COL]);
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
for (let i = 0; i < DATA.length; i++) {
  const reg = String(DATA[i][REGION_COL]);
  const val = Number(DATA[i][REVENUE_COL]);
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
  const total = regionTotals.get(reg) ?? 0;
  const widthPct = (total / grandTotal) * 100;
  const x0 = cumX;
  const x1 = cumX + widthPct;
  cumX = x1;

  // Stack bottom-to-top so first product is at the top of each column
  let cumY = 100;
  const segments: MarimekkoSegment[] = [];
  for (let p = 0; p < products.length; p++) {
    const prod = products[p];
    const matchingRow = DATA.find(
      (row) => String(row[REGION_COL]) === reg && String(row[PRODUCT_COL]) === prod,
    );
    const val = matchingRow ? Number(matchingRow[REVENUE_COL]) : 0;
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
  const xScale = useXScale();
  const yScale = useYScale();
  const { top, height } = useDrawingArea();
  const bottomY = top + height;

  return (
    <g>
      {columns.map((col) => {
        const px0 = Number(xScale(col.x0));
        const px1 = Number(xScale(col.x1));
        const colW = px1 - px0;
        const colMidX = px0 + colW / 2;

        return (
          <g key={col.region}>
            {col.segments.map((seg) => {
              const pyTop = Number(yScale(seg.y1));
              const pyBottom = Number(yScale(seg.y0));
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
                      text={`$${seg.value}M (${Math.round(seg.share * 100)}%)`}
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
              text={`$${col.total}M (${Math.round(col.widthPct)}%)`}
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
            label: "Share of Regional Revenue (%)",
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
